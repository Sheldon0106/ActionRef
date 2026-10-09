"""Dependency-free checks for the public repository (not clinical validation)."""
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
TEXT = {'.md', '.py', '.r', '.json', '.yaml', '.yml', '.toml', '.cff', '.txt', '.csv', '.log'}


def public_files():
    result = subprocess.run(
        ['git', 'ls-files', '-z', '--cached', '--others', '--exclude-standard'],
        cwd=ROOT, capture_output=True, check=True,
    )
    # Check the current working-tree publication set, including new files and
    # excluding files removed in the pending revision. Required assets below
    # are still checked explicitly.
    return sorted({ROOT / p.decode('utf-8') for p in result.stdout.split(b'\0')
                   if p and (ROOT / p.decode('utf-8')).exists()})


def main():
    failures = []
    paths = public_files()
    for required in ('src/universal_cutoff/data/__init__.py', 'src/universal_cutoff/data/ratio_tiers.json'):
        if ROOT / required not in paths:
            failures.append('Required package resource is not in the Git file set: ' + required)
    csv_count = 0
    patterns = {
        'local absolute path': re.compile(r'(?i)\b[a-z]:[\\/]+'),
        'private key': re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
        'GitHub credential': re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{50,})\b'),
    }
    for path in paths:
        if not path.is_file():
            failures.append('{}: listed file missing'.format(path.relative_to(ROOT)))
            continue
        if path.suffix.lower() not in TEXT:
            continue
        source = path.read_text(encoding='utf-8-sig')
        for label, pattern in patterns.items():
            if pattern.search(source):
                failures.append('{}: {}'.format(path.relative_to(ROOT), label))
        if path.suffix == '.md':
            for target in re.findall(r'!?\[[^\]\n]*\]\(([^)\n]+)\)', source):
                target = target.strip().split(' "')[0].strip('<>')
                url = urlsplit(target)
                if url.scheme or target.startswith(('#', '//')) or not url.path:
                    continue
                resolved = (path.parent / unquote(url.path)).resolve()
                if not resolved.exists():
                    failures.append('{}: broken local link {}'.format(path.relative_to(ROOT), target))
        if path.suffix == '.csv':
            csv_count += 1
            with path.open(encoding='utf-8-sig', newline='') as handle:
                header = next(csv.reader(handle), [])
            forbidden = {'subject_id', 'hadm_id', 'stay_id', 'patient_id', 'encounter_id', 'mrn', 'date_of_birth'}
            found = forbidden.intersection(x.strip().lower() for x in header)
            if found:
                failures.append('{}: possible encounter-level identifiers {}'.format(path.relative_to(ROOT), sorted(found)))
    manifest_path = ROOT / 'docs/assets/data/provenance.json'
    manifest = json.loads(manifest_path.read_text())
    for filename, record in manifest['files'].items():
        file = manifest_path.parent / filename
        if hashlib.sha256(file.read_bytes()).hexdigest() != record['sha256']:
            failures.append('Figure source checksum mismatch: ' + filename)
    manifest_path = ROOT / 'results/cross_disease_validation_v1/manifest.json'
    manifest = json.loads(manifest_path.read_text())
    for filename, expected in manifest['output_sha256'].items():
        file = ROOT / 'results' / filename.replace('\\', '/')
        if not file.exists() or hashlib.sha256(file.read_bytes()).hexdigest().lower() != expected.lower():
            failures.append('Research output checksum mismatch: ' + filename)
    manifest_path = ROOT / 'docs/assets/data/synthetic_provenance.json'
    manifest = json.loads(manifest_path.read_text())
    for filename, expected in manifest['sha256'].items():
        file = manifest_path.parent / filename
        if hashlib.sha256(file.read_bytes()).hexdigest() != expected:
            failures.append('Synthetic figure source checksum mismatch: ' + filename)
    manifest_path = ROOT / 'results/sepsis_primary/manifest.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    for filename, record in manifest['files'].items():
        file = manifest_path.parent / filename
        if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != record['sha256']:
            failures.append('Primary paper source checksum mismatch: ' + filename)
    config = manifest['config']
    if hashlib.sha256((ROOT / config['path']).read_bytes()).hexdigest() != config['sha256']:
        failures.append('Primary paper configuration checksum mismatch')
    pairs = [('semantic_response_curve.csv', 'sepsis_learning_curve.csv'),
             ('sepsis_action_points.json', 'sepsis_action_points.json'),
             ('sepsis_action_reliability.json', 'sepsis_action_reliability.json')]
    for primary, figure in pairs:
        if (manifest_path.parent / primary).read_bytes() != (ROOT / 'docs/assets/data' / figure).read_bytes():
            failures.append('Paper and figure source differ: ' + primary)
    for folder, files_key, config_key in (
        ('results/copd/validation_v2_corrected', 'public_files', 'public_config'),
        ('results/aert', 'files', 'config'),
    ):
        bundle = ROOT / folder
        record = json.loads((bundle / 'manifest.json').read_text(encoding='utf-8'))
        for filename, expected in record[files_key].items():
            file = bundle / filename
            if not file.is_file() or hashlib.sha256(file.read_bytes()).hexdigest() != expected['sha256']:
                failures.append('Additional-application source checksum mismatch: ' + folder + '/' + filename)
        config = record[config_key]
        if hashlib.sha256((ROOT / config['path']).read_bytes()).hexdigest() != config['sha256']:
            failures.append('Additional-application configuration checksum mismatch: ' + folder)

    # JSON summaries must not silently carry individual records inside nested lists.
    forbidden = {'subject_id', 'hadm_id', 'stay_id', 'patient_id', 'encounter_id',
                 'subject_ids', 'patient_ids', 'stay_ids', 'hadm_ids',
                 'mrn', 'date_of_birth', 'note_text', 'annotation_linkage'}
    def record_keys(value):
        if isinstance(value, dict):
            for key, child in value.items():
                yield str(key).lower()
                yield from record_keys(child)
        elif isinstance(value, list):
            for child in value:
                yield from record_keys(child)
    for path in paths:
        if path.suffix == '.json' and 'results' in path.relative_to(ROOT).parts:
            found = forbidden.intersection(record_keys(json.loads(path.read_text(encoding='utf-8'))))
            if found:
                failures.append('{}: possible nested individual-record fields {}'.format(
                    path.relative_to(ROOT), sorted(found)))

    for name in ('workflow', 'synthetic-example', 'clinical-action', 'copd-partial-output'):
        for suffix in ('png', 'svg', 'pdf'):
            if not (ROOT / 'docs/assets/figures' / (name + '.' + suffix)).is_file():
                failures.append('Missing figure export: ' + name + '.' + suffix)
        svg = ROOT / 'docs/assets/figures' / (name + '.svg')
        if svg.is_file() and '<text' not in svg.read_text(encoding='utf-8'):
            failures.append('Figure SVG has no editable text: ' + name)
    if failures:
        print('\n'.join(failures))
        raise SystemExit(1)
    print('PASS: {} public files, {} aggregate CSV headers, local links, path/credential patterns, source/result hashes, and figure exports.'.format(len(paths), csv_count))


if __name__ == '__main__':
    main()
