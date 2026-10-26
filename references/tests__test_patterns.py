from orca_explorer.patterns import (
    _bh_adjust,
    analyze_distinct_transitions,
    analyze_temporal_spacing,
)


def _recording(call_types: list[str], starts: list[float]) -> dict[str, object]:
    return {
        "provider": "TEST",
        "events": [
            {
                "_begin": start,
                "call_type": call_type,
                "ecotype": "SRKW",
            }
            for call_type, start in zip(call_types, starts)
        ],
    }


def test_bh_adjustment_preserves_rank_order() -> None:
    first = ("A", "B")
    second = ("B", "C")
    adjusted = _bh_adjust({first: 0.01, second: 0.2})

    assert adjusted[first] == 0.02
    assert adjusted[second] == 0.2


def test_temporal_spacing_uses_recording_medians() -> None:
    recordings = [
        _recording(["A", "A", "B"], [0.0, 1.0, 5.0]),
        _recording(["B", "B", "A"], [0.0, 2.0, 8.0]),
    ]

    report = analyze_temporal_spacing(recordings)

    assert report["eligible_recordings"] == 2
    assert report["median_of_recording_same_type_medians_seconds"] == 1.5
    assert report["median_of_recording_changed_type_medians_seconds"] == 5.0
    assert report["same_type_shorter_recordings"] == 2


def test_transition_scan_reports_supported_pair_without_overclaiming() -> None:
    recordings = [
        _recording(["A", "B", "A", "B", "A", "B"], [0, 1, 2, 3, 4, 5]),
        _recording(["A", "B", "A", "B", "A", "B"], [0, 1, 2, 3, 4, 5]),
    ]

    report = analyze_distinct_transitions(recordings, permutations=20, seed=5)

    assert report["candidate_pairs_tested"] >= 1
    assert report["top_candidates"][0]["transition"] == "A -> B"
