from orca_explorer.exploratory import (
    _holm_adjust,
    analyze_call_type_adjacency,
    analyze_standard_split_pod_labels,
)


def test_holm_adjustment_is_monotonic() -> None:
    adjusted = _holm_adjust({"first": 0.01, "second": 0.04, "third": 0.5})

    assert adjusted == {"first": 0.03, "second": 0.08, "third": 0.5}


def test_call_type_adjacency_counts_recording_sequences() -> None:
    recordings = [
        {
            "provider": "TEST",
            "events": [
                {"_begin": 0.0, "call_type": "A", "ecotype": "SRKW"},
                {"_begin": 1.0, "call_type": "A", "ecotype": "SRKW"},
                {"_begin": 2.0, "call_type": "B", "ecotype": "SRKW"},
            ],
        },
        {
            "provider": "TEST",
            "events": [
                {"_begin": 0.0, "call_type": "A", "ecotype": "SRKW"},
                {"_begin": 1.0, "call_type": "B", "ecotype": "SRKW"},
                {"_begin": 2.0, "call_type": "B", "ecotype": "SRKW"},
            ],
        },
    ]

    report = analyze_call_type_adjacency(recordings, permutations=20, seed=4)

    assert report["eligible_recordings"] == 2
    assert report["adjacent_pairs"] == 4
    assert report["observed_matches"] == 2


def test_pod_label_entanglement_reports_same_data_accuracy() -> None:
    rows = [
        {
            "provider": "P",
            "selection_table": (
                "species\tpod\tcall_type\n"
                "Killer whale\tJ\tS01\n"
                "Killer whale\tJ\tS01\n"
                "Killer whale\tL\tS02\n"
                "Killer whale\tJ\tS02\n"
            ),
        }
    ]

    report = analyze_standard_split_pod_labels(rows)

    assert report["annotated_segments"] == 4
    assert report["call_type_to_majority_pod_accuracy_same_data"] == 0.75
