from dataclasses import asdict, dataclass, field
from datetime import date
from typing import Dict, List, Optional, Tuple

import numpy as np

from .exceptions import InputValidationError
from .schemas import Provenance


ALLOWED_SOURCE_TYPES = {
    "expert_elicitation", "delphi_elicitation", "published_evidence",
    "local_costing", "stakeholder_preference", "policy", "scenario_assumption",
}
ALLOWED_CONFIDENCE = {"low", "moderate", "high"}


@dataclass(frozen=True)
class DecisionContext:
    disease: str
    population: str
    care_setting: str
    intended_user: str
    intended_use: str


@dataclass(frozen=True)
class OutcomeContext:
    definition: str
    time_horizon: str
    severity: str
    reversibility: str
    preventability_by_action: str


@dataclass(frozen=True)
class ValuedConsequence:
    name: str
    value: float
    unit: str
    source: str
    confidence: str
    lower: Optional[float] = None
    upper: Optional[float] = None

    def __post_init__(self):
        if not self.name.strip() or not self.unit.strip() or not self.source.strip():
            raise InputValidationError("valued consequence requires name, unit, and source")
        if self.confidence not in ALLOWED_CONFIDENCE:
            raise InputValidationError("valued consequence confidence must be low, moderate, or high")
        _positive(self.value, "valued consequence value")
        if self.lower is not None:
            _positive(self.lower, "valued consequence lower")
        if self.upper is not None:
            _positive(self.upper, "valued consequence upper")
        if self.lower is not None and self.lower > self.value:
            raise InputValidationError("valued consequence lower cannot exceed value")
        if self.upper is not None and self.upper < self.value:
            raise InputValidationError("valued consequence upper cannot be below value")


@dataclass(frozen=True)
class ConsequenceAssessment:
    components: List[str]
    source: str
    confidence: str
    monetary_value: Optional[float] = None
    valued_components: List[ValuedConsequence] = field(default_factory=list)


@dataclass(frozen=True)
class DecisionThresholdElicitation:
    """Action threshold probability, not a score cutoff. Maps to R via R=(1-p_t)/p_t."""

    primary_probability: float
    plausible_probability_range: Tuple[float, float]
    elicitation_method: str
    source: str
    confidence: str

    def __post_init__(self):
        values = [self.primary_probability] + list(self.plausible_probability_range)
        if any(not np.isfinite(x) or x <= 0 or x >= 1 for x in values):
            raise InputValidationError("decision threshold probabilities must lie strictly between 0 and 1")
        lower, upper = self.plausible_probability_range
        if lower > self.primary_probability or self.primary_probability > upper:
            raise InputValidationError("primary decision threshold must lie within its plausible range")
        if self.confidence not in ALLOWED_CONFIDENCE:
            raise InputValidationError("decision threshold confidence must be low, moderate, or high")


@dataclass(frozen=True)
class ActionabilityAssessment:
    triggered_action: str
    expected_effectiveness: str
    evidence_strength: str
    intervention_risks: List[str] = field(default_factory=list)
    subgroup_variation: Optional[str] = None


@dataclass(frozen=True)
class CapacityAssessment:
    K: int
    operational_period: str
    staffing_resources: str
    expected_to_bind: Optional[bool] = None

    def __post_init__(self):
        if isinstance(self.K, bool) or int(self.K) != self.K or self.K < 0:
            raise InputValidationError("capacity K must be a nonnegative integer")


@dataclass(frozen=True)
class ElicitationFrame:
    """Required before any trade-off question. Recorded verbatim in provenance."""

    intended_action: str
    target_outcome: str
    stakeholder_perspective: str
    time_horizon: str

    def __post_init__(self):
        for label, value in (("intended_action", self.intended_action),
                             ("target_outcome", self.target_outcome),
                             ("stakeholder_perspective", self.stakeholder_perspective),
                             ("time_horizon", self.time_horizon)):
            if not str(value).strip():
                raise InputValidationError(
                    "elicitation frame requires {}; identify the action, outcome, "
                    "perspective, and horizon before asking any trade-off question".format(label)
                )


@dataclass(frozen=True)
class NaturalFrequencyChoice:
    """One trade-off from the elicitation ladder. Field names avoid causal-benefit framing."""

    additional_outcome_positive: int
    additional_outcome_negative: int
    accepted: bool

    def __post_init__(self):
        if (isinstance(self.additional_outcome_positive, bool)
                or int(self.additional_outcome_positive) != self.additional_outcome_positive
                or self.additional_outcome_positive <= 0):
            raise InputValidationError("additional_outcome_positive must be a positive integer")
        if (isinstance(self.additional_outcome_negative, bool)
                or int(self.additional_outcome_negative) != self.additional_outcome_negative
                or self.additional_outcome_negative < 0):
            raise InputValidationError("additional_outcome_negative must be a nonnegative integer")
        if not isinstance(self.accepted, bool):
            raise InputValidationError("accepted must be true or false")


@dataclass(frozen=True)
class RGuidanceInput:
    decision: DecisionContext
    outcome: OutcomeContext
    false_negative: ConsequenceAssessment
    false_positive: ConsequenceAssessment
    actionability: ActionabilityAssessment
    capacity: CapacityAssessment
    provenance: Provenance
    decision_threshold: Optional[DecisionThresholdElicitation] = None
    elicitation_frame: Optional[ElicitationFrame] = None
    natural_frequency_choices: List[NaturalFrequencyChoice] = field(default_factory=list)
    primary_R: Optional[float] = None
    plausible_range: Optional[Tuple[float, float]] = None
    sensitivity_grid: Optional[List[float]] = None
    decision_transition_Rs: List[float] = field(default_factory=list)
    disagreements: List[str] = field(default_factory=list)
    missing_evidence: List[str] = field(default_factory=list)
    review_date: Optional[str] = None
    selection_basis: str = ""


@dataclass(frozen=True)
class RGuidanceResult:
    recommended_R_primary: Optional[float]
    recommended_R_range: Optional[Tuple[float, float]]
    recommended_R_grid: List[float]
    status: str
    provenance: Dict[str, object]
    confidence: str
    warnings: List[str]
    rationale_machine: Dict[str, object]
    rationale_human: str
    point_estimate_basis: str = ""
    module2_separation_guard: str = (
        "R guidance is an optional Module 3B input and cannot define, relabel, or replace Low/Mid/High."
    )


def _positive(value, label):
    if value is None or not np.isfinite(value) or value <= 0:
        raise InputValidationError("{} must be a finite positive number".format(label))
    return float(value)


def _default_grid(lower, primary, upper):
    if np.isclose(lower, upper):
        return [float(lower)]
    geom = np.geomspace(lower, upper, 5).tolist()
    return sorted(set(float(x) for x in geom + [primary, lower, upper]))


def r_from_decision_threshold(probability: float) -> float:
    if not np.isfinite(probability) or probability <= 0 or probability >= 1:
        raise InputValidationError("decision threshold probability must lie strictly between 0 and 1")
    return float((1.0 - probability) / probability)


def decision_threshold_from_r(R: float) -> float:
    ratio = _positive(R, "R")
    return float(1.0 / (1.0 + ratio))


def r_guidance_frame_questions() -> List[str]:
    return [
        "What action does crossing the threshold trigger?",
        "What is the target outcome, defined exactly as the score is meant to identify it?",
        "Whose perspective is being elicited (bedside clinician, service lead, patient, payer)?",
        "Over what time horizon is the outcome assessed?",
    ]


def r_guidance_questions() -> List[str]:
    return r_guidance_frame_questions() + [
        "Trade-off question, repeated across a short adaptive ladder (see natural_frequency_question).",
        "How many actions can the service absorb (K), and over what period?",
        "How confident is this scenario: low, moderate, or high?",
    ]


def natural_frequency_question(frame: ElicitationFrame,
                               additional_outcome_negative: int,
                               additional_outcome_positive: int = 1) -> str:
    """Neutral wording: attributes no benefit to any patient, no action as unnecessary."""
    if not isinstance(frame, ElicitationFrame):
        raise InputValidationError(
            "natural_frequency_question requires an ElicitationFrame; identify the action, "
            "outcome, stakeholder perspective, and time horizon before asking"
        )
    choice = NaturalFrequencyChoice(additional_outcome_positive, additional_outcome_negative, True)
    positive_label = "patient who experiences" if choice.additional_outcome_positive == 1 \
        else "patients who experience"
    negative_label = "additional patient who does not" if choice.additional_outcome_negative == 1 \
        else "additional patients who do not"
    return (
        "Suppose lowering the threshold identifies {positive} additional {positive_label} "
        "{outcome}, while also triggering {action} for {negative} {negative_label} experience "
        "{outcome}. Considering the expected benefits, harms, workload, and a time horizon of "
        "{horizon}, would you accept this tradeoff?"
    ).format(positive=choice.additional_outcome_positive, positive_label=positive_label,
             outcome=frame.target_outcome, action=frame.intended_action,
             negative=choice.additional_outcome_negative, negative_label=negative_label,
             horizon=frame.time_horizon)


def next_natural_frequency_question(frame: ElicitationFrame,
                                    choices: Optional[List[NaturalFrequencyChoice]] = None,
                                    max_questions: int = 3):
    if not isinstance(frame, ElicitationFrame):
        raise InputValidationError(
            "next_natural_frequency_question requires an ElicitationFrame; identify the action, "
            "outcome, stakeholder perspective, and time horizon before asking"
        )
    answered = list(choices or [])
    if len(answered) >= max_questions:
        return {
            "status": "question_limit_reached",
            "additional_outcome_negative": None,
            "question": None,
            "reason": "the configured question limit has been reached",
        }
    if not answered:
        next_ratio = 9
        reason = "initial middle scenario"
    else:
        derivation = _natural_frequency_derivation(answered)
        if not derivation["consistent"]:
            return {
                "status": "inconsistent_answers",
                "additional_outcome_negative": None,
                "question": None,
                "reason": (
                    "a harder trade-off was accepted while an easier one was rejected; "
                    "review the answers with the respondent before asking further questions"
                ),
            }
        lower = derivation["accepted_R_lower_bound"]
        upper = derivation["rejected_R_upper_bound"]
        already_tested = {row["implied_R_boundary"] for row in derivation["choices"]}
        if lower is not None and upper is not None:
            candidates = list(range(int(np.floor(lower)) + 1, int(np.ceil(upper))))
            candidates = [x for x in candidates if float(x) not in already_tested]
            if not candidates:
                return {
                    "status": "bracket_resolved",
                    "additional_outcome_negative": None,
                    "question": None,
                    "reason": "no untested whole-number trade-off remains inside the bracket",
                }
            target = np.sqrt(max(lower, 1e-12) * upper)
            next_ratio = min(candidates, key=lambda x: abs(np.log(max(x, 1e-12)) - np.log(target)))
            reason = "narrows the accepted-to-rejected bracket"
        elif lower is not None:
            next_ratio = max(int(np.floor(lower * 2 + 1)), int(lower) + 1)
            reason = "tests a harder trade-off to find a rejected upper bound"
        else:
            upper_int = int(np.ceil(upper))
            next_ratio = max(0, int(np.floor(upper_int / 2)))
            if float(next_ratio) in already_tested and next_ratio > 0:
                next_ratio -= 1
            reason = "tests an easier trade-off to find an accepted lower bound"
    return {
        "status": "question_available",
        "additional_outcome_negative": int(next_ratio),
        "additional_outcome_positive": 1,
        "question": natural_frequency_question(frame, int(next_ratio), 1),
        "reason": reason,
    }


def _natural_frequency_derivation(choices):
    """bracketing_status: bracketed, one_sided_lower, one_sided_upper, or inconsistent.
    A primary value is returned for bracketed only."""
    if not choices:
        return None
    rows = []
    for choice in choices:
        ratio = float(choice.additional_outcome_negative) / float(choice.additional_outcome_positive)
        rows.append({
            "additional_outcome_positive": int(choice.additional_outcome_positive),
            "additional_outcome_negative": int(choice.additional_outcome_negative),
            "accepted": bool(choice.accepted),
            "implied_R_boundary": ratio,
            "implied_action_probability": 1.0 / (1.0 + ratio),
        })
    accepted = [row["implied_R_boundary"] for row in rows if row["accepted"]]
    rejected = [row["implied_R_boundary"] for row in rows if not row["accepted"]]
    lower = max(accepted) if accepted else None
    upper = min(rejected) if rejected else None

    consistent = not (lower is not None and upper is not None and lower > upper)
    if not consistent:
        status = "inconsistent"
    elif lower is not None and upper is not None:
        status = "bracketed"
    elif lower is not None:
        status = "one_sided_lower"
    else:
        status = "one_sided_upper"

    bracketed = status == "bracketed" and lower < upper
    primary = None
    primary_rule = None
    if bracketed and lower > 0:
        primary = float(np.sqrt(lower * upper))
        primary_rule = (
            "geometric (log-scale) midpoint of the elicited switch interval; "
            "a summary of where the respondent switched, not an estimate of the true R"
        )
    elif bracketed:
        primary = float(upper / 2.0)
        primary_rule = (
            "arithmetic midpoint of the elicited switch interval because the accepted "
            "lower bound is zero; not an estimate of the true R"
        )
    return {
        "choices": rows,
        "accepted_R_lower_bound": lower,
        "rejected_R_upper_bound": upper,
        "bracketing_status": status,
        "consistent": consistent,
        "bracketed": bracketed,
        "R": primary,
        "range": (float(lower), float(upper)) if bracketed else None,
        "primary_rule": primary_rule,
    }


def build_simple_r_guidance(
    disease: str,
    population: str,
    intended_user: str,
    intended_use: str,
    outcome: str,
    triggered_action: str,
    capacity_K: int,
    capacity_period: str,
    primary_R: Optional[float] = None,
    plausible_range: Optional[Tuple[float, float]] = None,
    sensitivity_grid: Optional[List[float]] = None,
    action_threshold_probability: Optional[float] = None,
    plausible_probability_range: Optional[Tuple[float, float]] = None,
    natural_frequency_choices: Optional[List[NaturalFrequencyChoice]] = None,
    stakeholder_perspective: Optional[str] = None,
    time_horizon: Optional[str] = None,
    care_setting: str = "unspecified",
    false_negative_consequences: Optional[List[str]] = None,
    false_positive_burdens: Optional[List[str]] = None,
    intervention_risks: Optional[List[str]] = None,
    stakeholders: Optional[List[str]] = None,
    notes: Optional[str] = None,
) -> RGuidanceResult:
    """One route only: direct R, action_threshold_probability, or natural_frequency_choices.
    Omit all three to receive insufficient_basis."""
    direct_r_supplied = primary_R is not None or plausible_range is not None
    probability_supplied = (
        action_threshold_probability is not None or plausible_probability_range is not None
    )
    frequency_supplied = bool(natural_frequency_choices)
    if sum([bool(direct_r_supplied), bool(probability_supplied), frequency_supplied]) > 1:
        raise InputValidationError(
            "supply one route only: direct R, action-threshold probability, or natural-frequency choices"
        )
    decision_threshold = None
    if probability_supplied:
        if action_threshold_probability is None or plausible_probability_range is None:
            raise InputValidationError(
                "action-threshold route requires a primary probability and plausible probability range"
            )
        decision_threshold = DecisionThresholdElicitation(
            primary_probability=action_threshold_probability,
            plausible_probability_range=plausible_probability_range,
            elicitation_method="direct action-threshold question",
            source="workflow stakeholder scenario",
            confidence="low",
        )
    requester = list(stakeholders or [intended_user])
    scenario_notes = notes or "User-stated operational consequence scenario; no literature required."
    horizon = time_horizon or "unspecified"
    frame = None
    if frequency_supplied:
        frame = ElicitationFrame(
            intended_action=triggered_action,
            target_outcome=outcome,
            stakeholder_perspective=stakeholder_perspective or intended_user,
            time_horizon=horizon,
        )
    return build_r_guidance(RGuidanceInput(
        decision=DecisionContext(disease, population, care_setting, intended_user, intended_use),
        outcome=OutcomeContext(outcome, horizon, "user-specified", "user-specified", "not assessed"),
        false_negative=ConsequenceAssessment(
            list(false_negative_consequences or ["missed actionable case"]),
            "user scenario", "low"),
        false_positive=ConsequenceAssessment(
            list(false_positive_burdens or ["unnecessary alert or action"]),
            "user scenario", "low"),
        actionability=ActionabilityAssessment(
            triggered_action, "not quantified", "unknown", list(intervention_risks or [])),
        capacity=CapacityAssessment(capacity_K, capacity_period, "user-specified"),
        provenance=Provenance(
            "scenario_assumption", requester, date.today().isoformat(), [], scenario_notes, "low"),
        decision_threshold=decision_threshold,
        elicitation_frame=frame,
        natural_frequency_choices=list(natural_frequency_choices or []),
        primary_R=primary_R,
        plausible_range=plausible_range,
        sensitivity_grid=sensitivity_grid,
        missing_evidence=[
            "formal consequence valuation or structured elicitation was not supplied"
        ],
        selection_basis="user-stated consequence scenario",
    ))


def _component_derivation(false_negative, false_positive):
    fn = list(false_negative.valued_components)
    fp = list(false_positive.valued_components)
    if not fn and not fp:
        return None
    if not fn or not fp:
        raise InputValidationError("component derivation requires valued components for both FN and FP")
    units = {item.unit for item in fn + fp}
    if len(units) != 1:
        raise InputValidationError("all valued FN and FP components must use one commensurate unit")
    fn_names = [x.name.strip().lower() for x in fn]
    fp_names = [x.name.strip().lower() for x in fp]
    if len(fn_names) != len(set(fn_names)) or len(fp_names) != len(set(fp_names)):
        raise InputValidationError("duplicate valued component names risk double counting")
    fn_total = float(sum(x.value for x in fn))
    fp_total = float(sum(x.value for x in fp))
    fn_low = float(sum(x.lower if x.lower is not None else x.value for x in fn))
    fn_high = float(sum(x.upper if x.upper is not None else x.value for x in fn))
    fp_low = float(sum(x.lower if x.lower is not None else x.value for x in fp))
    fp_high = float(sum(x.upper if x.upper is not None else x.value for x in fp))
    return {
        "R": fn_total / fp_total,
        "range": (fn_low / fp_high, fn_high / fp_low),
        "unit": next(iter(units)),
        "FN_total": fn_total,
        "FP_total": fp_total,
        "FN_components": [asdict(x) for x in fn],
        "FP_components": [asdict(x) for x in fp],
    }


def build_r_guidance(request: RGuidanceInput) -> RGuidanceResult:
    """Validates and grids a supplied R scenario. Does not estimate R from prevalence or clinical labels."""
    if request.provenance.source_type not in ALLOWED_SOURCE_TYPES:
        raise InputValidationError("Unsupported provenance source_type")
    if request.provenance.confidence not in ALLOWED_CONFIDENCE:
        raise InputValidationError("confidence must be low, moderate, or high")
    basis = request.selection_basis.lower()
    forbidden = []
    if "prevalence" in basis:
        forbidden.append("disease prevalence")
    if "preferred threshold" in basis or "make threshold" in basis or "force threshold" in basis:
        forbidden.append("preferred-threshold tuning")
    if forbidden:
        raise InputValidationError("R cannot be based on {}".format(" or ".join(forbidden)))

    if request.natural_frequency_choices and request.elicitation_frame is None:
        raise InputValidationError(
            "natural-frequency elicitation requires an ElicitationFrame identifying the intended "
            "action, target outcome, stakeholder perspective, and time horizon; the same trade-off "
            "carries a different meaning under a different action, outcome, respondent, or horizon"
        )

    warnings = []
    component_derivation = _component_derivation(request.false_negative, request.false_positive)
    frequency_derivation = _natural_frequency_derivation(request.natural_frequency_choices)
    threshold_derivation = None
    if request.decision_threshold is not None:
        probability = request.decision_threshold.primary_probability
        p_low, p_high = request.decision_threshold.plausible_probability_range
        threshold_derivation = {
            "R": r_from_decision_threshold(probability),
            "range": (r_from_decision_threshold(p_high), r_from_decision_threshold(p_low)),
            "primary_probability": probability,
            "probability_range": (p_low, p_high),
            "elicitation_method": request.decision_threshold.elicitation_method,
            "source": request.decision_threshold.source,
            "confidence": request.decision_threshold.confidence,
        }
    if request.primary_R is not None:
        primary = _positive(request.primary_R, "primary_R")
    elif component_derivation is not None:
        primary = float(component_derivation["R"])
    elif threshold_derivation is not None:
        primary = float(threshold_derivation["R"])
    elif frequency_derivation is not None and frequency_derivation["bracketed"]:
        primary = float(frequency_derivation["R"])
    else:
        primary = None
    if request.plausible_range is not None:
        lower = _positive(request.plausible_range[0], "plausible_range lower")
        upper = _positive(request.plausible_range[1], "plausible_range upper")
        if lower > upper:
            raise InputValidationError("plausible_range must be ordered low to high")
        plausible = (lower, upper)
    elif component_derivation is not None:
        plausible = tuple(component_derivation["range"])
    elif threshold_derivation is not None:
        plausible = tuple(threshold_derivation["range"])
    elif frequency_derivation is not None and frequency_derivation["bracketed"]:
        plausible = tuple(frequency_derivation["range"])
    else:
        plausible = None

    independently_costed = (request.false_negative.monetary_value is not None and
                            request.false_positive.monetary_value is not None)
    if component_derivation is not None:
        derived = float(component_derivation["R"])
        if request.primary_R is not None and not np.isclose(primary, derived, rtol=0.05):
            warnings.append("primary R differs by more than 5% from the independently valued component ratio")
        if np.isclose(component_derivation["range"][0], component_derivation["range"][1]):
            warnings.append("valued components lack uncertainty bounds; the component-derived range is degenerate")
        if component_derivation["unit"].lower() not in {"usd", "dollar", "dollars", "currency"}:
            warnings.append("component values are commensurate but nonmonetary; do not label FAE as currency")
    elif independently_costed:
        fn_cost = _positive(request.false_negative.monetary_value, "false-negative monetary value")
        fp_cost = _positive(request.false_positive.monetary_value, "false-positive monetary value")
        derived = fn_cost / fp_cost
        if primary is None:
            primary = derived
        elif not np.isclose(primary, derived, rtol=0.05):
            warnings.append("primary R differs by more than 5% from independently entered component costs")
    elif (request.false_negative.monetary_value is None) != (request.false_positive.monetary_value is None):
        warnings.append("only one monetary consequence is defined; FAE must not be converted to currency")
    else:
        warnings.append("FAE is nonmonetary because C_FP and C_FN lack independent monetary definitions")

    if threshold_derivation is not None and primary is not None:
        elicited = float(threshold_derivation["R"])
        if not np.isclose(primary, elicited, rtol=0.20):
            warnings.append("primary R differs by more than 20% from the elicited action-threshold ratio")
    if frequency_derivation is not None:
        bracketing = frequency_derivation["bracketing_status"]
        if bracketing == "inconsistent":
            warnings.append(
                "natural-frequency answers are inconsistent: a harder trade-off was accepted "
                "while an easier one was rejected, so no single R explains them. Review the "
                "answers with the respondent; no primary R is reported"
            )
        elif bracketing == "one_sided_lower":
            warnings.append(
                "every trade-off offered was accepted, so the elicitation bounds R only from "
                "below (R is at least {:g}); ask a harder trade-off before selecting R".format(
                    frequency_derivation["accepted_R_lower_bound"])
            )
        elif bracketing == "one_sided_upper":
            warnings.append(
                "every trade-off offered was rejected, so the elicitation bounds R only from "
                "above (R is at most {:g}); ask an easier trade-off before selecting R".format(
                    frequency_derivation["rejected_R_upper_bound"])
            )
        elif not frequency_derivation["bracketed"]:
            warnings.append(
                "the accepted and rejected trade-offs coincide, leaving no interval to summarize"
            )

    scenario_based = request.provenance.source_type == "scenario_assumption"
    if primary is None and plausible is not None:
        primary = float(np.sqrt(plausible[0] * plausible[1]))
        scenario_based = True
        warnings.append("primary R is a geometric-midpoint scenario, not an identified clinical value")
    if primary is not None and plausible is None:
        plausible = (primary, primary)
        warnings.append("unique primary R has no plausible uncertainty range")
    if primary is None:
        status = "insufficient_basis"
        grid = []
        warnings.append("no defensible primary R or plausible range was supplied")
    else:
        if not (plausible[0] <= primary <= plausible[1]):
            raise InputValidationError("primary_R must lie within plausible_range")
        if request.sensitivity_grid is not None:
            grid = sorted(set(_positive(x, "sensitivity_grid value") for x in request.sensitivity_grid))
            if primary not in grid:
                grid.append(primary); grid.sort()
            if grid[0] > plausible[0] or grid[-1] < plausible[1]:
                warnings.append("sensitivity grid does not span the full plausible range")
        else:
            grid = _default_grid(plausible[0], primary, plausible[1])
        if frequency_derivation is not None:
            tested = [
                row["implied_R_boundary"] for row in frequency_derivation["choices"]
                if plausible[0] <= row["implied_R_boundary"] <= plausible[1]
            ]
            grid = sorted(set(grid + tested))
        transitions = sorted(set(_positive(x, "decision transition R")
                                 for x in request.decision_transition_Rs))
        in_range_transitions = [x for x in transitions if plausible[0] <= x <= plausible[1]]
        if len(in_range_transitions) < len(transitions):
            warnings.append("decision-transition R values outside the plausible range were excluded")
        grid = sorted(set(grid + in_range_transitions + [primary, plausible[0], plausible[1]]))
        source_to_status = {
            "local_costing": "locally_costed",
            "expert_elicitation": "consensus_based",
            "delphi_elicitation": "consensus_based",
            "published_evidence": "evidence_based",
            "stakeholder_preference": "consensus_based",
            "policy": "evidence_based",
            "scenario_assumption": "scenario_based",
        }
        status = "scenario_based" if scenario_based else source_to_status[request.provenance.source_type]

    confidence = request.provenance.confidence
    confidence_rank = {"low": 0, "moderate": 1, "high": 2}
    evidence_confidence = [request.false_negative.confidence, request.false_positive.confidence]
    if component_derivation is not None:
        evidence_confidence.extend(
            item.confidence
            for item in request.false_negative.valued_components + request.false_positive.valued_components
        )
    if request.decision_threshold is not None:
        evidence_confidence.append(request.decision_threshold.confidence)
    invalid_confidence = [x for x in evidence_confidence if x not in ALLOWED_CONFIDENCE]
    if invalid_confidence:
        raise InputValidationError("all consequence and elicitation confidence values must be low, moderate, or high")
    lowest_evidence_confidence = min(evidence_confidence, key=lambda x: confidence_rank[x])
    if confidence_rank[lowest_evidence_confidence] < confidence_rank[confidence]:
        confidence = lowest_evidence_confidence
        warnings.append("overall confidence reduced to the lowest supporting evidence confidence")
    if scenario_based and confidence != "low":
        warnings.append("scenario-based R is reported with low confidence")
        confidence = "low"
    frequency_drove_primary = (
        frequency_derivation is not None and frequency_derivation["bracketed"]
        and request.primary_R is None and component_derivation is None
        and threshold_derivation is None
    )
    if frequency_drove_primary and confidence != "low":
        warnings.append(
            "R derived from stakeholder trade-off elicitation is reported with low confidence"
        )
        confidence = "low"
    if request.missing_evidence:
        warnings.append("missing evidence: " + "; ".join(request.missing_evidence))
    if request.disagreements:
        warnings.append("stakeholder disagreement requires sensitivity analysis")
    if request.capacity.expected_to_bind is True:
        warnings.append("capacity is expected to bind; retention under K is not independent cost optimality")
    if not request.actionability.triggered_action.strip():
        warnings.append("triggered action is unspecified; R is not interpretable as willingness-to-treat")
    if request.actionability.evidence_strength.lower() in {"weak", "none", "unknown"}:
        warnings.append("actionability evidence is weak")

    if primary is None:
        point_estimate_basis = (
            "No primary R is reported. {}".format(
                "; ".join(warnings) if warnings else "No defensible basis was supplied."
            )
        )
    elif frequency_drove_primary:
        point_estimate_basis = (
            "R={:g} is the geometric (log-scale) midpoint of the elicited switch interval "
            "[{:g}, {:g}], the largest trade-off accepted and the smallest rejected. It summarizes "
            "where the respondent switched; it is not an estimate of the true R, and the interval "
            "carries the uncertainty."
        ).format(primary, plausible[0], plausible[1])
    elif request.primary_R is not None:
        point_estimate_basis = (
            "R={:g} was entered directly as a prespecified value; the range and grid carry the "
            "sensitivity analysis.".format(primary)
        )
    elif component_derivation is not None:
        point_estimate_basis = (
            "R={:g} is the ratio of independently valued FN and FP components in {}.".format(
                primary, component_derivation["unit"])
        )
    elif threshold_derivation is not None:
        point_estimate_basis = (
            "R={:g} is implied by the elicited action-threshold probability {:g} through "
            "R=(1-p_t)/p_t.".format(primary, threshold_derivation["primary_probability"])
        )
    else:
        point_estimate_basis = (
            "R={:g} is the geometric midpoint of the supplied plausible range; it is a scenario "
            "summary, not an identified clinical value.".format(primary)
        )

    human = (
        "R={} is a {} scenario for {} in {}. The plausible range is {} and all Module 3B "
        "comparators should be reported across grid {}. This is not a prevalence-derived or threshold-tuned value."
    ).format(primary, status, request.decision.intended_use, request.decision.population, plausible, grid)
    machine = {
        "elicitation_frame": asdict(request.elicitation_frame) if request.elicitation_frame else None,
        "point_estimate_is_not_an_estimate_of_true_R": True,
        "basis": request.selection_basis or request.provenance.source_type,
        "independently_costed": independently_costed,
        "capacity_K": request.capacity.K,
        "capacity_period": request.capacity.operational_period,
        "expected_capacity_binding": request.capacity.expected_to_bind,
        "action": request.actionability.triggered_action,
        "uncertainty_review_date": request.review_date or date.today().isoformat(),
        "prevalence_used": False,
        "preferred_threshold_tuning_used": False,
        "decision_transition_Rs_used_for_grid_only": (
            in_range_transitions if primary is not None else []
        ),
        "equation": "R = C_FN / C_FP",
        "decision_threshold_equation": "R = (1 - p_t) / p_t",
        "component_derivation": component_derivation,
        "decision_threshold_derivation": threshold_derivation,
        "natural_frequency_derivation": frequency_derivation,
        "capacity_role": "context and binding audit only; K does not identify R",
        "module1_role": (
            "optional calibration and score-to-risk translation only; Module 1 does not identify R"
        ),
        "module2_role": (
            "not used to identify R; observed clinician behavior is descriptive and cannot set preferences"
        ),
    }
    return RGuidanceResult(primary, plausible, grid, status, asdict(request.provenance),
                           confidence, warnings, machine, human, point_estimate_basis)
