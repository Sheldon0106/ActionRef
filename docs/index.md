---
hide:
  - toc
---

<div class="hero" markdown>
<p class="eyebrow">CLINICAL SCORE CUTOFF</p>

# Scores, in the context of practice.

ActionRef connects an existing clinical score to recorded actions, giving teams
interpretable reference points for discussing alert thresholds and their consequences.

[Run the example](quickstart.md){ .md-button .md-button--primary }
[Understand the references](references.md){ .md-button }
[Reproduce the paper](paper-reproduction.md){ .md-button }
</div>

![The ActionRef workflow, from existing scores and observed actions to behavioral references, operating candidates, and separate evaluation.](assets/figures/workflow.png)

[Open the full-size diagram](assets/figures/workflow.svg)

## Four questions, one workflow

Using your own score? Start with the [synthetic walkthrough](quickstart.md) and
[output states](output-states.md). Reading the paper? Open the
[primary result tables](paper-results.md) and their [reproduction guide](paper-reproduction.md).

<div class="feature-grid" markdown>
<div class="feature-card" markdown>
### What happens in practice?
Learn the relationship between a score and recorded actions, with the sample
support visible alongside the fitted curve.
</div>
<div class="feature-card" markdown>
### What does a reference mean?
Read Low, Mid, and High through their action-probability targets. Keep relative
references and unavailable outputs visible.
</div>
<div class="feature-card" markdown>
### What can the team handle?
Map references to an alert budget, and optionally compare thresholds under
explicit consequence weights.
</div>
<div class="feature-card" markdown>
### What changes on new data?
Evaluate the chosen thresholds on separate encounters, reporting workload,
recorded-action yield, and outcome coverage.
</div>
</div>

## Start with a complete example

```bash
python -m pip install -e ".[test]"
python examples/synthetic_walkthrough.py
```

The example includes synthetic inputs, a learning/evaluation split, and saved
aggregate outputs. [Follow it step by step →](quickstart.md)

## Explore the evidence

The primary application is [sepsis ESRP](clinical-example.md): MIMIC references
27 / 36 / 51, Stanford local re-estimation 26 / 36 / 50, and candidate 31 under
R = 11,299/804. [COPD and HEART-derived AERT](evidence.md#additional-applications)
provide additional applications, including partial-reference output and exploratory
short-discrete reference learning. The [reported result tables](paper-results.md)
and [reproduction guide](paper-reproduction.md) connect these applications to the
paper's tables and Supplementary Data.

AKI and pneumonia are retained as software development and compatibility records;
they are not reported in the paper.

ActionRef describes recorded practice and supports explicit threshold comparisons.
The proposed clinical workflow and its evaluation remain part of the local decision.
