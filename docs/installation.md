# Installation

The distribution is named `universal-cutoff`; Python code imports `universal_cutoff`.
Install from the repository:

```bash
git clone https://github.com/Sheldon0106/ActionRef.git
cd ActionRef
```

## Create an environment

The core package supports Python 3.8 and newer. Python 3.11 or newer is convenient
when also building the documentation. Regenerating the repository figures uses
R separately; see [figure sources and reproduction](figures.md).

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

Or on macOS / Linux:

```bash
source .venv/bin/activate
```

From the repository root:

```bash
python -m pip install -e ".[test]"
python -m pytest
python examples/synthetic_walkthrough.py
```

The package dependencies are NumPy, pandas, SciPy, and scikit-learn. The clinical
reproduction runners additionally use PyYAML and, for plots, matplotlib:

```bash
python -m pip install -e ".[research]"
```

## Preview the documentation

```bash
python -m pip install -r requirements-docs.txt
python -m mkdocs serve
```

Open the local address printed by MkDocs. See the [walkthrough](quickstart.md) next.
