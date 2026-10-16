"""Mathematical reference cases, not yet runtime/legacy parity certification."""

import pytest


def weighted_nps(promoter: float, detractor: float, innocuous: float) -> float:
    total = promoter + detractor + innocuous
    return round((promoter - detractor) / total, 4) if total else 0.0


def test_nps_uses_reach_not_article_counts():
    # Three articles with unequal reach would have count-NPS 0.
    assert weighted_nps(100, 50, 50) == 0.25
    assert weighted_nps(1, 1, 1) == 0.0


def test_disjoint_exhaustive_contributions_sum_to_group_nps():
    # Theme A: +100 promoter; Theme B: -50 detractor and +50 innocuous.
    denominator = 200
    contributions = [(100 - 0) / denominator, (0 - 50) / denominator]
    assert sum(contributions) == pytest.approx(weighted_nps(100, 50, 50))


def test_topic_frequency_weighting_differs_from_reach_contribution():
    # MP-009 uses topic NPS weighted by frequency, not group reach.
    topic_nps = [1.0, -1.0]
    topic_frequency = [1, 2]
    legacy_topic_total = sum(
        nps * count / sum(topic_frequency)
        for nps, count in zip(topic_nps, topic_frequency)
    )
    reach_nps = weighted_nps(100, 50, 0)
    assert legacy_topic_total == pytest.approx(-1 / 3)
    assert legacy_topic_total != reach_nps


def test_zero_denominator_reference_behavior():
    assert weighted_nps(0, 0, 0) == 0.0
