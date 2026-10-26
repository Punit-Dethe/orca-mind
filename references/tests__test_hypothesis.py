from orca_explorer.hypothesis import analyze_buzzer_hypothesis, extract_recordings


def _row(provider: str, ecotype: str, behaviors: list[str], name: str) -> dict[str, str]:
    lines = ["species\tecotype\tacoustic_behavior"]
    lines.extend(f"Killer whale\t{ecotype}\t{behavior}" for behavior in behaviors)
    return {
        "provider": provider,
        "audio_path": name,
        "selection_table": "\n".join(lines) + "\n",
    }


def test_extract_recordings_uses_presence_not_event_count() -> None:
    rows = [
        _row("ONC", "OKW", ["buzzer", "buzzer", "burst_pulse"], "a.wav"),
        _row("ONC", "SRKW", ["burst_pulse"], "b.wav"),
        _row("OTHER", "OKW", ["buzzer"], "c.wav"),
    ]

    recordings, diagnostics = extract_recordings(rows)

    assert recordings == [
        {"recording_id": "a.wav", "ecotype": "OKW", "has_buzzer": True},
        {"recording_id": "b.wav", "ecotype": "SRKW", "has_buzzer": False},
    ]
    assert diagnostics["manifest_rows_seen"] == 3
    assert diagnostics["provider_rows_seen"] == 2


def test_hypothesis_report_uses_recording_level_counts() -> None:
    recordings = [
        {"recording_id": "a", "ecotype": "OKW", "has_buzzer": True},
        {"recording_id": "b", "ecotype": "OKW", "has_buzzer": False},
        {"recording_id": "c", "ecotype": "SRKW", "has_buzzer": False},
        {"recording_id": "d", "ecotype": "TKW", "has_buzzer": False},
    ]

    report = analyze_buzzer_hypothesis(recordings)

    assert report["comparison"]["contingency_table_present_absent"] == [
        [1, 1],
        [0, 2],
    ]
    assert report["by_ecotype"]["OKW"]["rate"] == 0.5
