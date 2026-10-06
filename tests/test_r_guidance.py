import pytest

from universal_cutoff import (ActionabilityAssessment, CapacityAssessment,
    ConsequenceAssessment, DecisionContext, DecisionThresholdElicitation, ElicitationFrame,
    NaturalFrequencyChoice, OutcomeContext, Provenance, RGuidanceInput, ValuedConsequence,
    build_r_guidance, build_simple_r_guidance, decision_threshold_from_r,
    natural_frequency_question, next_natural_frequency_question,
    r_guidance_frame_questions, r_guidance_questions)
from universal_cutoff.exceptions import InputValidationError


FRAME = ElicitationFrame(
    intended_action="clinical reassessment",
    target_outcome="Sepsis-3 within 6 hours",
    stakeholder_perspective="ED triage clinician",
    time_horizon="6 hours",
)


def request(**overrides):
    values = dict(
        decision=DecisionContext("sepsis", "adult ED", "ED", "triage clinician", "resource activation"),
        outcome=OutcomeContext("Sepsis-3", "6 hours", "high", "variable", "plausible"),
        false_negative=ConsequenceAssessment(["treatment delay", "morbidity"], "expert panel", "moderate"),
        false_positive=ConsequenceAssessment(["alert burden", "testing"], "workflow study", "moderate"),
        actionability=ActionabilityAssessment("clinical reassessment", "uncertain", "moderate", ["overtesting"]),
        capacity=CapacityAssessment(40, "daily ED encounters", "one response team", True),
        provenance=Provenance("scenario_assumption", ["ED clinicians", "patients"], "2026-08-20", [], "initial scenario", "low"),
        primary_R=15, plausible_range=(3, 20), sensitivity_grid=[3, 5, 10, 15, 20],
        selection_basis="prespecified consequence scenario")
    values.update(overrides)
    return RGuidanceInput(**values)


def test_r_guidance_returns_primary_range_grid_provenance_and_guard():
    result = build_r_guidance(request())
    assert result.recommended_R_primary == 15
    assert result.recommended_R_range == (3, 20)
    assert result.recommended_R_grid == [3, 5, 10, 15, 20]
    assert result.status == "scenario_based"
    assert result.confidence == "low"
    assert "cannot define" in result.module2_separation_guard


def test_prevalence_based_r_is_rejected():
    with pytest.raises(InputValidationError):
        build_r_guidance(request(selection_basis="derived from disease prevalence"))


def test_threshold_tuned_r_is_rejected():
    with pytest.raises(InputValidationError):
        build_r_guidance(request(selection_basis="chosen to make threshold 36 optimal"))


def test_nonpositive_r_is_rejected():
    with pytest.raises(InputValidationError):
        build_r_guidance(request(primary_R=0))


def test_action_threshold_probability_derives_r_and_uncertainty_range():
    elicitation = DecisionThresholdElicitation(
        primary_probability=.10, plausible_probability_range=(.05, .20),
        elicitation_method="modified Delphi", source="multistakeholder panel",
        confidence="moderate")
    result = build_r_guidance(request(
        provenance=Provenance("delphi_elicitation", ["clinicians", "patients"], confidence="moderate"),
        primary_R=None, plausible_range=None, sensitivity_grid=None,
        decision_threshold=elicitation))
    assert result.recommended_R_primary == pytest.approx(9)
    assert result.recommended_R_range == pytest.approx((4, 19))
    assert result.status == "consensus_based"
    assert result.rationale_machine["decision_threshold_derivation"]["primary_probability"] == .10


def test_commensurate_components_derive_r_by_equation():
    fn = ConsequenceAssessment(
        ["delay", "morbidity"], "published evidence", "moderate",
        valued_components=[
            ValuedConsequence("delay", 10, "harm_point", "cohort study", "moderate", 8, 12),
            ValuedConsequence("morbidity", 5, "harm_point", "patient panel", "moderate", 3, 7),
        ])
    fp = ConsequenceAssessment(
        ["testing"], "local costing", "moderate",
        valued_components=[
            ValuedConsequence("testing", 2, "harm_point", "workflow study", "moderate", 1, 3),
        ])
    result = build_r_guidance(request(
        provenance=Provenance("published_evidence", confidence="moderate"),
        false_negative=fn, false_positive=fp, primary_R=None,
        plausible_range=None, sensitivity_grid=None))
    assert result.recommended_R_primary == pytest.approx(7.5)
    assert result.recommended_R_range == pytest.approx((11 / 3, 19))
    assert result.rationale_machine["component_derivation"]["FN_total"] == 15


def test_noncommensurate_components_are_rejected():
    fn = ConsequenceAssessment(["delay"], "study", "moderate",
        valued_components=[ValuedConsequence("delay", 10, "QALY", "study", "moderate")])
    fp = ConsequenceAssessment(["time"], "study", "moderate",
        valued_components=[ValuedConsequence("time", 2, "minutes", "study", "moderate")])
    with pytest.raises(InputValidationError):
        build_r_guidance(request(false_negative=fn, false_positive=fp))


def test_decision_transitions_refine_grid_but_cannot_change_primary():
    result = build_r_guidance(request(decision_transition_Rs=[4.5, 12.25, 50]))
    assert result.recommended_R_primary == 15
    assert 4.5 in result.recommended_R_grid
    assert 12.25 in result.recommended_R_grid
    assert 50 not in result.recommended_R_grid
    assert result.rationale_machine["decision_transition_Rs_used_for_grid_only"] == [4.5, 12.25]


def test_simple_scenario_route_is_low_friction_and_scenario_labeled():
    result = build_simple_r_guidance(
        disease="sepsis", population="adult ED", intended_user="triage team",
        intended_use="early reassessment", outcome="actionable sepsis within 6 hours",
        triggered_action="clinical reassessment", capacity_K=40, capacity_period="per day",
        primary_R=15, plausible_range=(5, 25),
    )
    assert result.recommended_R_primary == 15
    assert result.recommended_R_range == (5, 25)
    assert result.status == "scenario_based"
    assert result.confidence == "low"
    assert result.provenance["source_type"] == "scenario_assumption"
    assert "not a prevalence-derived" in result.rationale_human


def test_simple_scenario_route_does_not_invent_r_when_user_has_no_basis():
    result = build_simple_r_guidance(
        disease="sepsis", population="adult ED", intended_user="triage team",
        intended_use="early reassessment", outcome="actionable sepsis",
        triggered_action="clinical reassessment", capacity_K=40, capacity_period="per day",
    )
    assert result.status == "insufficient_basis"
    assert result.recommended_R_primary is None
    assert len(r_guidance_questions()) == 7


def test_simple_action_probability_route_derives_r_range_and_grid():
    result = build_simple_r_guidance(
        disease="sepsis", population="adult ED", intended_user="triage team",
        intended_use="early reassessment", outcome="actionable sepsis",
        triggered_action="clinical reassessment", capacity_K=40, capacity_period="per day",
        action_threshold_probability=.10, plausible_probability_range=(.05, .20),
    )
    assert result.recommended_R_primary == pytest.approx(9)
    assert result.recommended_R_range == pytest.approx((4, 19))
    assert result.status == "scenario_based"
    assert result.rationale_machine["decision_threshold_derivation"]["primary_probability"] == .10
    assert decision_threshold_from_r(9) == pytest.approx(.10)


def test_simple_route_rejects_mixed_r_and_probability_inputs():
    with pytest.raises(InputValidationError):
        build_simple_r_guidance(
            disease="sepsis", population="adult ED", intended_user="triage team",
            intended_use="early reassessment", outcome="actionable sepsis",
            triggered_action="clinical reassessment", capacity_K=40, capacity_period="per day",
            primary_R=9, plausible_range=(4, 19),
            action_threshold_probability=.10, plausible_probability_range=(.05, .20),
        )


def simple(**overrides):
    values = dict(
        disease="sepsis", population="adult ED", intended_user="triage team",
        intended_use="early reassessment", outcome="actionable sepsis",
        triggered_action="clinical reassessment", capacity_K=40, capacity_period="per day",
        stakeholder_perspective="ED triage clinician", time_horizon="6 hours")
    values.update(overrides)
    return build_simple_r_guidance(**values)


def test_natural_frequency_switch_choices_bracket_r_without_probability_question():
    result = simple(natural_frequency_choices=[
        NaturalFrequencyChoice(1, 4, True),
        NaturalFrequencyChoice(1, 19, False),
        NaturalFrequencyChoice(1, 9, True),
    ])
    assert result.recommended_R_primary == pytest.approx((9 * 19) ** .5)
    assert result.recommended_R_range == (9, 19)
    assert 9 in result.recommended_R_grid and 19 in result.recommended_R_grid
    assert result.status == "scenario_based"
    assert result.confidence == "low"
    derivation = result.rationale_machine["natural_frequency_derivation"]
    assert derivation["bracketing_status"] == "bracketed"
    assert derivation["consistent"] is True
    assert derivation["primary_rule"].startswith("geometric (log-scale) midpoint")


def test_point_estimate_is_labelled_a_switch_interval_midpoint_not_an_estimate_of_true_r():
    result = simple(natural_frequency_choices=[
        NaturalFrequencyChoice(1, 13, True),
        NaturalFrequencyChoice(1, 19, False),
    ])
    assert "geometric (log-scale) midpoint" in result.point_estimate_basis
    assert "not an estimate of the true R" in result.point_estimate_basis
    assert result.rationale_machine["point_estimate_is_not_an_estimate_of_true_R"] is True


def test_inconsistent_answers_return_unavailable_estimate_rather_than_raising():
    result = simple(natural_frequency_choices=[
        NaturalFrequencyChoice(1, 19, True),
        NaturalFrequencyChoice(1, 9, False),
    ])
    assert result.status == "insufficient_basis"
    assert result.recommended_R_primary is None
    assert result.rationale_machine["natural_frequency_derivation"]["consistent"] is False
    assert any("inconsistent" in w for w in result.warnings)


def test_all_accepted_answers_give_a_one_sided_lower_bound_only():
    result = simple(natural_frequency_choices=[
        NaturalFrequencyChoice(1, 9, True),
        NaturalFrequencyChoice(1, 19, True),
    ])
    assert result.status == "insufficient_basis"
    assert result.recommended_R_primary is None
    derivation = result.rationale_machine["natural_frequency_derivation"]
    assert derivation["bracketing_status"] == "one_sided_lower"
    assert derivation["accepted_R_lower_bound"] == 19
    assert any("bounds R only from below" in w for w in result.warnings)


def test_all_rejected_answers_give_a_one_sided_upper_bound_only():
    result = simple(natural_frequency_choices=[
        NaturalFrequencyChoice(1, 9, False),
        NaturalFrequencyChoice(1, 4, False),
    ])
    assert result.status == "insufficient_basis"
    assert result.recommended_R_primary is None
    derivation = result.rationale_machine["natural_frequency_derivation"]
    assert derivation["bracketing_status"] == "one_sided_upper"
    assert derivation["rejected_R_upper_bound"] == 4
    assert any("bounds R only from above" in w for w in result.warnings)


def test_elicitation_requires_action_outcome_perspective_and_horizon():
    assert len(r_guidance_frame_questions()) == 4
    for bad in (("", "o", "s", "h"), ("a", "", "s", "h"), ("a", "o", "", "h"), ("a", "o", "s", "")):
        with pytest.raises(InputValidationError):
            ElicitationFrame(*bad)
    with pytest.raises(InputValidationError):
        build_r_guidance(request(
            natural_frequency_choices=[NaturalFrequencyChoice(1, 9, True)],
            primary_R=None, plausible_range=None, sensitivity_grid=None))


def test_trade_off_question_avoids_benefit_and_unnecessary_framing():
    text = natural_frequency_question(FRAME, 9)
    lowered = text.lower()
    # The approved prompt retains "expected benefits, harms, workload".
    # Prohibited wording attributes benefit to a patient or calls an action unnecessary.
    for banned in ("patient benefits", "patients benefit", "benefit from", "benefits from",
                   "unnecessar", "helped", "receive it", "receives it"):
        assert banned not in lowered, banned
    assert "lowering the threshold identifies" in text
    assert "do not experience" in text
    assert FRAME.intended_action in text and FRAME.target_outcome in text
    assert FRAME.time_horizon in text
    with pytest.raises(InputValidationError):
        natural_frequency_question("clinical reassessment", 9)


def test_frequency_question_generator_builds_three_step_adaptive_ladder():
    first = next_natural_frequency_question(FRAME)
    assert first["additional_outcome_negative"] == 9
    second = next_natural_frequency_question(FRAME, [NaturalFrequencyChoice(1, 9, True)])
    assert second["additional_outcome_negative"] == 19
    third = next_natural_frequency_question(FRAME, [
        NaturalFrequencyChoice(1, 9, True),
        NaturalFrequencyChoice(1, 19, False),
    ])
    assert third["additional_outcome_negative"] == 13
    stopped = next_natural_frequency_question(FRAME, [
        NaturalFrequencyChoice(1, 9, True),
        NaturalFrequencyChoice(1, 19, False),
        NaturalFrequencyChoice(1, 13, True),
    ])
    assert stopped["status"] == "question_limit_reached"


def test_ladder_stops_asking_once_answers_are_inconsistent():
    result = next_natural_frequency_question(FRAME, [
        NaturalFrequencyChoice(1, 19, True),
        NaturalFrequencyChoice(1, 9, False),
    ])
    assert result["status"] == "inconsistent_answers"
    assert result["question"] is None
