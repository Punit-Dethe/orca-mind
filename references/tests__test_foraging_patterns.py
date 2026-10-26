import pytest

from orca_explorer.foraging_patterns import (
    analyze_pattern,
    build_report,
    contingency_table,
    stratified_analysis,
)


def _row(deployment: str, buzz: int, slow: int, capture: int) -> dict[str, str]:
    return {
        "deployment": deployment,
        "bzsounds": str(buzz),
        "sc": str(slow),
        "kindet": str(capture),
    }


def test_contingency_table_uses_present_then_absent_rows() -> None:
    rows = [
        _row("a", 1, 0, 1),
        _row("a", 1, 0, 0),
        _row("a", 0, 0, 1),
        _row("a", 0, 0, 0),
        _row("a", 0, 0, 0),
    ]

    assert contingency_table(rows, "bzsounds") == [[1, 1], [1, 2]]


def test_stratified_analysis_tracks_deployment_directions() -> None:
    rows = [
        _row("a", 1, 0, 1),
        _row("a", 0, 0, 0),
        _row("b", 1, 0, 1),
        _row("b", 0, 0, 0),
        _row("c", 1, 0, 0),
        _row("c", 0, 0, 1),
        _row("d", 1, 0, 0),
        _row("d", 0, 0, 0),
    ]

    result = stratified_analysis(rows, "bzsounds")

    assert result["deployment_count"] == 4
    assert result["informative_deployment_count"] == 4
    assert result["deployment_direction_sign_test"] == {
        "positive": 2,
        "negative": 1,
        "ties": 1,
        "two_sided_p_value": 1.0,
    }
    assert result["mantel_haenszel_common_odds_ratio"] == pytest.approx(2.0)


def test_report_preserves_action_marker_boundary() -> None:
    rows = [
        _row("a", 1, 1, 1),
        _row("a", 0, 0, 0),
        _row("b", 1, 1, 1),
        _row("b", 0, 0, 0),
    ]

    report = build_report(rows)

    assert report["status"] == "action_patterns_supported_not_word_translation"
    assert {item["canonical_gloss"] for item in report["patterns"]} == {
        "SEARCH",
        "PURSUE",
    }
    assert all(item["role"] == "biosonar_action_marker" for item in report["patterns"])


def test_pattern_analysis_rejects_nonbinary_values() -> None:
    rows = [_row("a", 1, 0, 1)]
    rows[0]["bzsounds"] = "yes"

    with pytest.raises(ValueError, match="binary 0/1"):
        analyze_pattern(rows, "buzzes")
