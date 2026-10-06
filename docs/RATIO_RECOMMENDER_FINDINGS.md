# Choosing R without a cost study — tier defaults and how much R actually matters

Answers the question raised in the Module 3B walkthrough: a user applying the framework
to a new disease has no literature cost build, so how do they set `R = c_FN / c_FP`?

Implementation: `src/universal_cutoff/ratio_recommender.py`;
tests: `tests/test_ratio_recommender.py` in the repository checkout.

The numbers below were produced by `run_ratio_recommender.py` in the analysis workspace,
which reads the standardized per-threshold exports for the four diseases. Those exports
are derived from credentialed MIMIC-IV-ED and are therefore not redistributed here; the
recommender itself runs on any confusion table:

```python
from universal_cutoff import build_threshold_table, recommend_ratio

thresholds = build_threshold_table(df, "score", outcome_col="outcome")
print(recommend_ratio(thresholds, tier="A", k_fracs=[0.01, 0.05, 0.10, 0.20]).summary())
```

---

## 1. Why R does not require costing

When `C_FN` and `C_FP` represent constant relative consequences and the usual
expected-loss assumptions apply, their ratio has an equivalent risk-threshold reading
under the standard threshold identity (Pauker & Kassirer 1975/1980; Vickers & Elkin
decision curve analysis):

```
pt = c_FP / (c_FP + c_FN) = 1 / (1 + R)        <=>        R = (1 - pt) / pt
```

R is the risk threshold at which a decision-maker is indifferent, written as odds. So a
scenario value can be read off a **published threshold probability for a comparable
decision**, with no monetary cost derivation. Equivalently, `R = N - 1`, where N is the
break-even number of alerts per outcome-positive case at the decision margin. This is
not the observed PPV of the deployed alert and not a causal number needed to treat.

Two drivers set it, and both are judgements about the **decision**, not the disease:
how fast and how badly the miss hurts, and how costly it is to act on a well patient.

## 2. The tier table

Each tier is anchored to a published threshold probability. These adjacent-decision
anchors make the defaults prespecified scenarios, not locally estimated parameters.

| Tier | Decision profile | Published anchor | pt | Default R | Band | Alerts per case |
|---|---|---|---|---|---|---|
| **A** | Time-critical illness, cheap and safe response | PE testing threshold ~1.8–2% (Pauker–Kassirer); this framework's ED sepsis cost build at 6.25% | 2–6.25% | **20** | 15–49 | ~21 |
| **B** | Serious but not hour-critical, moderate response | Statin primary prevention at 7.5% 10-year ASCVD risk | 7–15% | **10** | 6–13 | ~11 |
| **C** | Not time-critical, invasive or expensive response | Prostate biopsy, reasonable range 10–30% | 20–30% | **3** | 2–4 | ~4 |

Tier A's low end is exactly R = 15 — the ED sepsis literature build sits there, at the
conservative end of its own tier. Tier assignment is a judgement about what the alert
makes someone *do*: the same illness moves tiers if the response changes from a blood
test to a procedure.

`explain_tiers()` prints the full guide, with worked examples and a "not this tier if"
test for each.

## 3. How much does R actually matter?

Measured on each disease's own confusion table, sweeping R from 1 to 100. Only the
score-by-outcome distribution is used — no treatment or behaviour data, so nothing here
is entangled with the Module 2 anchors.

`recall spread` is the range of recall produced by **every R in the tier band**. Zero
means the choice of R is irrelevant at that capacity.

| Disease | Tier | Capacity 1% | 2% | 5% | 10% | 20% | 30% | Unconstrained |
|---|---|---|---|---|---|---|---|---|
| Sepsis (ESRP_new, sepsis3) | A | **0.0 pp** | **0.0** | **0.0** | **0.0** | **0.0** | 3.2 | 31.3 |
| COPD (AutoScore) | B | **0.0 pp** | 9.8 | 14.0 | 14.0 | 14.0 | 14.0 | 14.0 |
| Pneumonia (AutoScore) | B | **0.0 pp** | **0.0** | **0.0** | 13.0 | 17.7 | 17.7 | 17.7 |
| AKI (AutoScore) | B | **0.0 pp** | **0.0** | **0.0** | **0.0** | **0.0** | 10.0 | 20.2 |

### The rule this produces

**Where the capacity boundary remains selected throughout the evaluated R band, R does
not move the cutoff.** The optimum is then to alert the highest-risk feasible patients
until the budget runs out. In the source update, sepsis at 1% capacity gave the same
cutoff (59) for every evaluated R from 2 to 100.

**Where capacity is slack, R matters and must be reported as a band.** Recall moves
13–31 pp across a tier band once the budget stops binding.

In the four source-update datasets, the tight-capacity settings often landed in the first
case. Users should test this on their own confusion table rather than assume that a
nominal capacity limit is binding for every R.

## 4. Validation: does the cheap route reproduce the expensive one?

Sepsis is the only disease with a full literature cost build (R = 15). Comparing that
against the ten-second tier pick (Tier A default, R = 20):

| Capacity | Cost-optimal threshold at R = 15 (literature) | at R = 20 (tier default) | Same? |
|---|---|---|---|
| 1% | 59 | 59 | yes |
| 2% | 53 | 53 | yes |
| 5% | 45 | 45 | yes |
| 10% | 40 | 40 | yes |
| 20% | 34 | 34 | yes |
| 30% | 31 | 30 | no (recall 64.8% vs 68.0%) |
| Unconstrained | 31 | 26 | no |

**In this sepsis source-update comparison, the tier default reproduced the
literature-costed threshold at 1%, 2%, 5%, 10%, and 20% capacity.** The two diverged at
30% and without a capacity constraint, where R changed the selected operating point.

This is a consistency check on one disease, not proof that tier defaults transfer
everywhere. It does establish that the expensive route was not buying threshold
precision under the operating conditions the framework targets.

## 5. Honest limitations

- **The anchors come from adjacent decisions, not from the user's setting.** A tier
  default is a starting point; where the invariance band is narrow, results should be
  reported across the band (the standard decision-curve convention) or R narrowed locally.
- **One-disease validation.** Only sepsis has both a literature build and a tier pick,
  so §4 is a single comparison.
- **Tier assignment is a judgement.** COPD, pneumonia and AKI were all placed in Tier B
  by the same reasoning; a user who considers the pneumonia decision time-critical would
  choose Tier A and get a different answer at loose capacity.
- **In-sample.** All bands are computed on `full_sample_exploratory` exports, so they
  inherit the same threshold optimism as the rest of the cross-disease work.
- **Nothing here prices absolute cost.** The recommender fixes the ratio, which sets the
  threshold. Reporting lambda in currency still needs absolute costs; lambda in
  false-alarm-equivalents does not.
- **The identity has assumptions.** It treats relative FP/FN consequences as constant
  and connects them to a calibrated action probability through expected loss. The tier
  route does not by itself demonstrate calibration, treatment benefit, transportability,
  or clinical utility.
- **The invariance band is computational.** It is the widest contiguous run on the
  specified R grid selecting the same cutoff; it is not a statistical confidence interval.
- **Module separation remains intact.** The recommender is an optional Module 3B scenario
  input. It cannot create, rename, or replace Module 2 Low/Mid/High. Capacity-only users
  may stop at Module 3A without specifying R.

## References

- Pauker SG, Kassirer JP. Therapeutic decision making: a cost-benefit analysis. *N Engl J Med* 1975;293:229-34.
- Pauker SG, Kassirer JP. The threshold approach to clinical decision making. *N Engl J Med* 1980;302:1109-17.
- Vickers AJ, Elkin EB. Decision curve analysis: a novel method for evaluating prediction models. *Med Decis Making* 2006;26:565-74.
- Vickers AJ, van Calster B, Steyerberg EW. A simple, step-by-step guide to interpreting decision curve analysis. *Diagn Progn Res* 2019;3:18.
- Vickers AJ, van Calster B, Steyerberg EW. Reporting and interpreting decision curve analysis: a guide for investigators. *Eur Urol* 2018;74:796-804.
- Patel AP, et al. Learning decision thresholds for risk-stratification models from aggregate clinician behavior. *J Am Med Inform Assoc* 2021;28:2258-64. doi:10.1093/jamia/ocab159
- Djulbegovic B, et al. How do physicians decide to treat: an empirical evaluation of the threshold model. *BMC Med Inform Decis Mak* 2014;14:47.
