"""Test foraging-action sound patterns in synchronized killer-whale dive data."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from scipy.stats import binomtest, chi2, fisher_exact


DATA_SOURCE = "https://doi.org/10.5281/zenodo.13308835"
PAPER_SOURCE = "https://doi.org/10.1111/gcb.17490"
CONTEXT_SOURCE = "https://doi.org/10.1111/mms.12836"

PATTERNS = {
    "slow_clicks": {
        "column": "sc",
        "canonical_gloss": "SEARCH",
        "physical_definition": "echolocation clicks with inter-click interval >100 ms",
        "role": "biosonar_action_marker",
    },
    "buzzes": {
        "column": "bzsounds",
        "canonical_gloss": "PURSUE",
        "physical_definition": "echolocation clicks with inter-click interval <11 ms",
        "role": "biosonar_action_marker",
    },
}


def load_rows(path: Path) -> list[dict[str, str]]:
    """Load the published per-dive analysis table."""
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def _binary(row: dict[str, Any], column: str) -> int:
    value = str(row.get(column, "")).strip()
    if value not in {"0", "1"}:
        raise ValueError(f"{column} must contain only binary 0/1 values; got {value!r}")
    return int(value)


def contingency_table(
    rows: Iterable[dict[str, Any]], exposure: str, outcome: str = "kindet"
) -> list[list[int]]:
    """Return [[exposed outcome+, exposed outcome-], [unexposed +, -]]."""
    table = [[0, 0], [0, 0]]
    for row in rows:
        exposed = _binary(row, exposure)
        detected = _binary(row, outcome)
        table[0 if exposed else 1][0 if detected else 1] += 1
    return table


def _stratum_counts(
    rows: Iterable[dict[str, Any]], exposure: str, outcome: str
) -> dict[str, tuple[int, int, int, int]]:
    grouped: dict[str, list[list[int]]] = defaultdict(lambda: [[0, 0], [0, 0]])
    for row in rows:
        deployment = str(row.get("deployment", "")).strip()
        if not deployment:
            raise ValueError("Every row requires a deployment identifier")
        exposed = _binary(row, exposure)
        detected = _binary(row, outcome)
        grouped[deployment][0 if exposed else 1][0 if detected else 1] += 1
    return {
        deployment: (table[0][0], table[0][1], table[1][0], table[1][1])
        for deployment, table in grouped.items()
    }


def stratified_analysis(
    rows: Iterable[dict[str, Any]], exposure: str, outcome: str = "kindet"
) -> dict[str, Any]:
    """Estimate a Mantel-Haenszel OR and CMH test, stratified by deployment."""
    strata = _stratum_counts(rows, exposure, outcome)
    numerator = 0.0
    denominator = 0.0
    observed_minus_expected = 0.0
    variance = 0.0
    positive = negative = ties = informative = 0

    for a, b, c, d in strata.values():
        n = a + b + c + d
        numerator += (a * d) / n
        denominator += (b * c) / n

        exposed_total = a + b
        unexposed_total = c + d
        outcome_total = a + c
        no_outcome_total = b + d
        if n > 1:
            expected = exposed_total * outcome_total / n
            var = (
                exposed_total
                * unexposed_total
                * outcome_total
                * no_outcome_total
                / (n * n * (n - 1))
            )
            observed_minus_expected += a - expected
            variance += var

        if exposed_total and unexposed_total:
            informative += 1
            exposed_rate = a / exposed_total
            unexposed_rate = c / unexposed_total
            if exposed_rate > unexposed_rate:
                positive += 1
            elif exposed_rate < unexposed_rate:
                negative += 1
            else:
                ties += 1

    mh_or = math.inf if denominator == 0 and numerator > 0 else numerator / denominator
    cmh_statistic = (observed_minus_expected**2) / variance if variance else math.nan
    cmh_p = float(chi2.sf(cmh_statistic, 1)) if variance else math.nan
    non_ties = positive + negative
    sign_p = (
        float(binomtest(positive, non_ties, 0.5, alternative="two-sided").pvalue)
        if non_ties
        else math.nan
    )

    return {
        "deployment_count": len(strata),
        "informative_deployment_count": informative,
        "mantel_haenszel_common_odds_ratio": mh_or,
        "cmh_chi_square_no_continuity_correction": cmh_statistic,
        "cmh_p_value": cmh_p,
        "deployment_direction_sign_test": {
            "positive": positive,
            "negative": negative,
            "ties": ties,
            "two_sided_p_value": sign_p,
        },
    }


def analyze_pattern(
    rows: list[dict[str, Any]], pattern_id: str, outcome: str = "kindet"
) -> dict[str, Any]:
    """Analyze one acoustic pattern against movement-validated prey capture."""
    definition = PATTERNS[pattern_id]
    table = contingency_table(rows, definition["column"], outcome)
    exposed_total = sum(table[0])
    unexposed_total = sum(table[1])
    fisher = fisher_exact(table, alternative="two-sided")

    return {
        "pattern_id": pattern_id,
        **definition,
        "dive_count": len(rows),
        "contingency_table": {
            "columns": ["prey_capture_detected", "no_prey_capture_detected"],
            "pattern_present": table[0],
            "pattern_absent": table[1],
        },
        "unstratified_statistics": {
            "capture_rate_pattern_present": table[0][0] / exposed_total,
            "capture_rate_pattern_absent": table[1][0] / unexposed_total,
            "fisher_exact_odds_ratio": float(fisher.statistic),
            "fisher_exact_two_sided_p": float(fisher.pvalue),
        },
        "deployment_stratified_statistics": stratified_analysis(
            rows, definition["column"], outcome
        ),
        "mapping_status": "validated_foraging_action_marker",
    }


def build_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build the two-pattern foraging-action report."""
    analyses = [analyze_pattern(rows, pattern_id) for pattern_id in PATTERNS]
    return {
        "status": "action_patterns_supported_not_word_translation",
        "data_source": DATA_SOURCE,
        "paper_source": PAPER_SOURCE,
        "supporting_behavior_source": CONTEXT_SOURCE,
        "unit": "dive",
        "dive_count": len(rows),
        "deployment_count": len({row["deployment"] for row in rows}),
        "outcome": (
            "prey-capture event inferred from validated movement signatures "
            "(peak jerk, roll, and heading variance thresholds)"
        ),
        "patterns": analyses,
        "interpretation_boundary": (
            "SEARCH and PURSUE are compact functional glosses for echolocation modes. "
            "They are strong action markers grounded in foraging mechanics, but they "
            "are not demonstrated symbolic words or social messages sent to another whale. "
            "The tests show association with prey-capture dives, not causation."
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Test slow-click and buzz patterns against prey-capture dives."
    )
    parser.add_argument("csv_path", type=Path)
    parser.add_argument("--output", type=Path)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    report = build_report(load_rows(args.csv_path))
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
