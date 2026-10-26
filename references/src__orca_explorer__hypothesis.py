"""Run a cautious, recording-level hypothesis test on DCLDE annotations."""

from __future__ import annotations

import argparse
import csv
import json
from io import StringIO
from pathlib import Path
from typing import Any, Iterable

from alp_data.datasets import DCLDE2026
from scipy.stats import fisher_exact

TARGET_ECOTYPE = "OKW"
COMPARISON_ECOTYPES = ("SRKW", "TKW")


def extract_recordings(
    rows: Iterable[dict[str, Any]], provider: str = "ONC"
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Reduce event annotations to one independent-looking row per recording."""
    recordings: list[dict[str, Any]] = []
    diagnostics = {
        "manifest_rows_seen": 0,
        "provider_rows_seen": 0,
        "excluded_without_acoustic_behavior": 0,
        "excluded_ambiguous_ecotype": 0,
    }

    allowed_ecotypes = {TARGET_ECOTYPE, *COMPARISON_ECOTYPES}
    for index, row in enumerate(rows):
        diagnostics["manifest_rows_seen"] += 1
        if str(row.get("provider", "")).strip() != provider:
            continue
        diagnostics["provider_rows_seen"] += 1

        ecotypes: set[str] = set()
        acoustic_behaviors: set[str] = set()
        annotations = csv.DictReader(StringIO(row["selection_table"]), delimiter="\t")
        for annotation in annotations:
            if annotation.get("species", "").strip() != "Killer whale":
                continue
            ecotype = annotation.get("ecotype", "").strip()
            if ecotype in allowed_ecotypes:
                ecotypes.add(ecotype)
            behavior = annotation.get("acoustic_behavior", "").strip().casefold()
            if behavior:
                acoustic_behaviors.add(behavior)

        if not acoustic_behaviors:
            diagnostics["excluded_without_acoustic_behavior"] += 1
            continue
        if len(ecotypes) != 1:
            diagnostics["excluded_ambiguous_ecotype"] += 1
            continue

        ecotype = next(iter(ecotypes))
        recordings.append(
            {
                "recording_id": str(row.get("audio_path") or f"manifest-row-{index}"),
                "ecotype": ecotype,
                "has_buzzer": "buzzer" in acoustic_behaviors,
            }
        )

    return recordings, diagnostics


def analyze_buzzer_hypothesis(
    recordings: Iterable[dict[str, Any]], provider: str = "ONC"
) -> dict[str, Any]:
    """Compare recording-level buzzer presence for OKW versus SRKW/TKW."""
    rows = list(recordings)
    target = [row for row in rows if row["ecotype"] == TARGET_ECOTYPE]
    comparison = [row for row in rows if row["ecotype"] in COMPARISON_ECOTYPES]
    if not target or not comparison:
        raise ValueError("Both OKW and comparison recordings are required")

    target_present = sum(bool(row["has_buzzer"]) for row in target)
    comparison_present = sum(bool(row["has_buzzer"]) for row in comparison)
    table = [
        [target_present, len(target) - target_present],
        [comparison_present, len(comparison) - comparison_present],
    ]
    result = fisher_exact(table, alternative="two-sided")
    target_rate = target_present / len(target)
    comparison_rate = comparison_present / len(comparison)

    by_ecotype: dict[str, dict[str, Any]] = {}
    for ecotype in (TARGET_ECOTYPE, *COMPARISON_ECOTYPES):
        group = [row for row in rows if row["ecotype"] == ecotype]
        present = sum(bool(row["has_buzzer"]) for row in group)
        by_ecotype[ecotype] = {
            "recordings": len(group),
            "with_buzzer": present,
            "rate": present / len(group) if group else None,
        }

    return {
        "status": "exploratory",
        "hypothesis": (
            "Within ONC recordings, OKW recordings are more likely to contain a "
            "buzzer annotation than SRKW or TKW recordings."
        ),
        "null_hypothesis": (
            "Recording-level buzzer presence is independent of the OKW versus "
            "SRKW/TKW grouping."
        ),
        "unit_of_analysis": "recording",
        "provider_held_constant": provider,
        "by_ecotype": by_ecotype,
        "comparison": {
            "groups": [TARGET_ECOTYPE, "SRKW+TKW"],
            "contingency_table_present_absent": table,
            "target_rate": target_rate,
            "comparison_rate": comparison_rate,
            "absolute_rate_difference": target_rate - comparison_rate,
            "odds_ratio": float(result.statistic),
            "fisher_exact_two_sided_p": float(result.pvalue),
        },
        "interpretation_boundary": (
            "A difference is consistent with an ecotype-linked annotation or "
            "repertoire pattern. It does not establish call meaning, cultural "
            "causation, or population-wide vocalization rates."
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Test an exploratory ecotype-linked DCLDE annotation hypothesis."
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path for the complete JSON result",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    dataset = DCLDE2026(split="all", streaming=True)
    recordings, diagnostics = extract_recordings(dataset._data)
    report = analyze_buzzer_hypothesis(recordings)
    report["data_diagnostics"] = diagnostics
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
