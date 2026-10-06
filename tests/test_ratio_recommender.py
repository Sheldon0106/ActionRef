from __future__ import annotations

import unittest

import numpy as np
import pandas as pd

from universal_cutoff import (
    RATIO_TIERS,
    alerts_per_case,
    build_threshold_table,
    decision_threshold_from_r,
    get_tier,
    implied_pt,
    implied_ratio,
    ratio_band_impact,
    ratio_from_alerts_per_case,
    ratio_invariance,
    recommend_ratio,
    tier_table,
)


def _toy_confusion():
    """Small monotone confusion table: 1000 patients, 100 positives, 10 score bins."""
    rng = np.random.default_rng(0)
    score = np.concatenate([rng.integers(0, 7, 900), rng.integers(3, 10, 100)])
    label = np.concatenate([np.zeros(900, int), np.ones(100, int)])
    frame = pd.DataFrame({"score": score, "outcome": label})
    return build_threshold_table(frame, "score", outcome_col="outcome")


def _direct_threshold(conf, ratio, k_frac):
    table = conf.table.copy()
    if k_frac is not None:
        limit = int(np.floor(k_frac * conf.policy_N + 1e-12))
        table = table[table["alert_count"] <= limit]
    table["cost_FAE"] = table["FP"] + ratio * table["FN"]
    minimum = float(table["cost_FAE"].min())
    tied = table[np.isclose(table["cost_FAE"], minimum, atol=1e-12, rtol=0)]
    return tied.sort_values(["alert_count", "threshold"], ascending=[False, True]).iloc[0]


class TestIdentities(unittest.TestCase):
    def test_ratio_and_pt_are_inverses(self):
        for pt in (0.02, 0.0625, 0.1, 0.25, 0.5):
            self.assertAlmostEqual(implied_pt(implied_ratio(pt)), pt, places=12)

    def test_sepsis_operating_point_round_trips(self):
        # the framework's literature-costed R=15 corresponds to pt = 6.25%
        self.assertAlmostEqual(implied_pt(15.0), 0.0625, places=12)
        self.assertAlmostEqual(implied_ratio(0.0625), 15.0, places=12)

    def test_alerts_per_case_round_trips(self):
        for ratio in (2.0, 10.0, 20.0, 49.0):
            self.assertAlmostEqual(ratio_from_alerts_per_case(alerts_per_case(ratio)), ratio, places=12)

    def test_break_even_agrees_with_cost_spec(self):
        for ratio in (3.0, 10.0, 20.0):
            self.assertAlmostEqual(decision_threshold_from_r(ratio), implied_pt(ratio), places=12)

    def test_rejects_out_of_range_inputs(self):
        for bad in (0.0, 1.0, -0.1, 1.5):
            with self.assertRaises(ValueError):
                implied_ratio(bad)
        with self.assertRaises(ValueError):
            implied_pt(0.0)
        with self.assertRaises(ValueError):
            ratio_from_alerts_per_case(1.0)


class TestTierTable(unittest.TestCase):
    def test_tiers_are_ordered_and_non_overlapping(self):
        highs = [t.ratio_high for t in RATIO_TIERS]
        lows = [t.ratio_low for t in RATIO_TIERS]
        self.assertEqual(highs, sorted(highs, reverse=True))
        for previous, current in zip(RATIO_TIERS, RATIO_TIERS[1:]):
            self.assertGreater(previous.ratio_low, current.ratio_high)

    def test_each_default_sits_inside_its_own_band(self):
        for tier in RATIO_TIERS:
            self.assertTrue(
                tier.contains(tier.default_ratio),
                f"tier {tier.key} default {tier.default_ratio} outside "
                f"[{tier.ratio_low}, {tier.ratio_high}]",
            )

    def test_band_endpoints_follow_from_threshold_probabilities(self):
        for tier in RATIO_TIERS:
            self.assertAlmostEqual(tier.ratio_low, implied_ratio(tier.pt_high), places=12)
            self.assertAlmostEqual(tier.ratio_high, implied_ratio(tier.pt_low), places=12)

    def test_sepsis_literature_ratio_falls_in_tier_a(self):
        self.assertTrue(get_tier("A").contains(15.0))

    def test_lookup_is_case_insensitive_and_validated(self):
        self.assertIs(get_tier("a"), get_tier("A"))
        with self.assertRaises(KeyError):
            get_tier("Z")

    def test_table_renders_one_row_per_tier(self):
        table = tier_table()
        self.assertEqual(len(table), len(RATIO_TIERS))
        self.assertEqual(list(table["tier"]), [t.key for t in RATIO_TIERS])


class TestInvariance(unittest.TestCase):
    def setUp(self):
        self.conf = _toy_confusion()

    def test_reference_threshold_matches_direct_optimization(self):
        table = ratio_invariance(self.conf, reference_ratio=10.0, k_fracs=[None, 0.1])
        for _, row in table.iterrows():
            kf = None if pd.isna(row["K_frac"]) else row["K_frac"]
            direct = _direct_threshold(self.conf, 10.0, kf)
            self.assertEqual(row["threshold_at_reference"], float(direct["threshold"]))

    def test_band_contains_the_reference_ratio(self):
        table = ratio_invariance(self.conf, reference_ratio=10.0, k_fracs=[None, 0.05, 0.1])
        self.assertTrue((table["ratio_band_low"] <= 10.0).all())
        self.assertTrue((table["ratio_band_high"] >= 10.0).all())

    def test_every_ratio_in_the_band_selects_the_same_threshold(self):
        grid = [round(float(r), 2) for r in np.arange(1.0, 50.5, 0.5)]
        table = ratio_invariance(self.conf, reference_ratio=10.0, k_fracs=[0.1], ratio_grid=grid)
        row = table.iloc[0]
        inside = [r for r in grid if row["ratio_band_low"] <= r <= row["ratio_band_high"]]
        self.assertGreater(len(inside), 1)
        for ratio in inside:
            best = _direct_threshold(self.conf, ratio, 0.1)
            self.assertEqual(float(best["threshold"]), row["threshold_at_reference"])

    def test_binding_capacity_makes_the_band_span_the_whole_grid(self):
        # under a tight budget the optimum is top-K, so R cannot move the threshold
        grid = [round(float(r), 2) for r in np.arange(2.0, 60.5, 0.5)]
        table = ratio_invariance(self.conf, reference_ratio=20.0, k_fracs=[0.01], ratio_grid=grid)
        row = table.iloc[0]
        self.assertTrue(bool(row["band_covers_grid"]))
        self.assertEqual(int(row["distinct_thresholds"]), 1)

    def test_empty_grid_is_an_error(self):
        with self.assertRaises(ValueError):
            ratio_invariance(self.conf, reference_ratio=10.0, ratio_grid=[])

    def test_dataframe_input_is_supported(self):
        via_result = ratio_invariance(self.conf, reference_ratio=10.0, k_fracs=[0.1])
        via_frame = ratio_invariance(self.conf.table, reference_ratio=10.0, k_fracs=[0.1])
        pd.testing.assert_frame_equal(via_result, via_frame)


class TestBandImpact(unittest.TestCase):
    def setUp(self):
        self.conf = _toy_confusion()

    def test_zero_spread_when_one_threshold_is_optimal_throughout(self):
        impact = ratio_band_impact(self.conf, ratio_low=5.0, ratio_high=50.0, k_fracs=[0.01])
        row = impact.iloc[0]
        self.assertEqual(row["threshold_min"], row["threshold_max"])
        self.assertAlmostEqual(row["recall_spread_pp"], 0.0, places=12)

    def test_spreads_are_non_negative_and_ordered(self):
        impact = ratio_band_impact(self.conf, ratio_low=2.0, ratio_high=40.0, k_fracs=[None, 0.05, 0.2])
        self.assertTrue((impact["recall_max"] >= impact["recall_min"]).all())
        self.assertTrue((impact["recall_spread_pp"] >= 0).all())
        self.assertTrue((impact["alert_frac_spread_pp"] >= 0).all())

    def test_band_outside_the_grid_is_an_error(self):
        with self.assertRaises(ValueError):
            ratio_band_impact(self.conf, ratio_low=500.0, ratio_high=600.0)


class TestRecommendation(unittest.TestCase):
    def setUp(self):
        self.conf = _toy_confusion()

    def test_default_comes_from_the_tier(self):
        rec = recommend_ratio(self.conf, tier="A", k_fracs=[0.01, 0.1])
        self.assertEqual(rec.ratio, get_tier("A").default_ratio)
        self.assertAlmostEqual(rec.threshold_probability, implied_pt(rec.ratio), places=12)

    def test_explicit_ratio_overrides_the_default_but_keeps_the_tier(self):
        rec = recommend_ratio(self.conf, tier="A", ratio=15.0, k_fracs=[0.01])
        self.assertEqual(rec.ratio, 15.0)
        self.assertEqual(rec.tier.key, "A")

    def test_summary_reports_every_capacity(self):
        rec = recommend_ratio(self.conf, tier="B", k_fracs=[0.01, 0.05, 0.2])
        text = rec.summary()
        self.assertIn("TIER B", text)
        self.assertEqual(len(rec.invariance), 3)
        for label in ("capacity 1%", "capacity 5%", "capacity 20%"):
            self.assertIn(label, text)

    def test_summary_explains_the_tier_before_the_numbers(self):
        # the point of the tier text is that a user can tell whether they belong in it
        text = recommend_ratio(self.conf, tier="A", k_fracs=[0.05]).summary()
        for expected in ("Pick this if:", "Decisions that fit:", "decision margin", "VERDICT"):
            self.assertIn(expected, text)

    def test_tier_a_low_end_is_the_sepsis_literature_ratio(self):
        # keeps the tier table consistent with the framework's own worked cost example
        self.assertAlmostEqual(get_tier("A").ratio_low, 15.0, places=9)

    def test_default_is_safe_flag_agrees_with_the_band(self):
        rec = recommend_ratio(self.conf, tier="A", k_fracs=[0.01])
        tier = get_tier("A")
        expected = bool(
            (rec.invariance["ratio_band_low"] <= tier.ratio_low).all()
            and (rec.invariance["ratio_band_high"] >= tier.ratio_high).all()
        )
        self.assertEqual(rec.default_is_safe, expected)

    def test_recommendation_stays_separate_from_module2(self):
        rec = recommend_ratio(self.conf, tier="B", k_fracs=[0.05])
        self.assertEqual(rec.status, "scenario_based")
        self.assertEqual(rec.confidence, "low")
        self.assertIn("cannot define", rec.module2_separation_guard)


if __name__ == "__main__":
    unittest.main()
