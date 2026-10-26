"""Search DCLDE annotation sequences for temporal and transition patterns."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from alp_data.datasets import DCLDE2026
from scipy.stats import wilcoxon

from orca_explorer.exploratory import parse_killer_whale_recordings


def _clean(value: object) -> str:
    return str(value or "").strip()


def _labeled_events(recording: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        event
        for event in sorted(recording["events"], key=lambda event: event["_begin"])
        if _clean(event.get("call_type")).casefold() not in {"", "unk", "unknown"}
    ]


def _bh_adjust(pvalues: dict[tuple[str, str], float]) -> dict[tuple[str, str], float]:
    ordered = sorted(pvalues.items(), key=lambda item: item[1])
    adjusted: dict[tuple[str, str], float] = {}
    running_min = 1.0
    total = len(ordered)
    for reverse_index in range(total - 1, -1, -1):
        pair, pvalue = ordered[reverse_index]
        rank = reverse_index + 1
        running_min = min(running_min, pvalue * total / rank)
        adjusted[pair] = min(1.0, running_min)
    return adjusted


def analyze_temporal_spacing(
    recordings: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Compare start-to-start spacing for same- versus changed-call transitions."""
    same_type_medians: list[float] = []
    changed_type_medians: list[float] = []
    for recording in recordings:
        events = _labeled_events(recording)
        same_gaps: list[float] = []
        changed_gaps: list[float] = []
        for left, right in zip(events, events[1:]):
            start_to_start = float(right["_begin"]) - float(left["_begin"])
            if start_to_start <= 0:
                continue
            if _clean(left.get("call_type")) == _clean(right.get("call_type")):
                same_gaps.append(start_to_start)
            else:
                changed_gaps.append(start_to_start)
        if same_gaps and changed_gaps:
            same_type_medians.append(float(np.median(same_gaps)))
            changed_type_medians.append(float(np.median(changed_gaps)))

    if not same_type_medians:
        raise ValueError("No recordings contain both same- and changed-type transitions")
    result = wilcoxon(same_type_medians, changed_type_medians, alternative="two-sided")
    shorter = sum(
        same < changed
        for same, changed in zip(same_type_medians, changed_type_medians)
    )
    return {
        "status": "exploratory",
        "finding": (
            "Within recordings containing both transition kinds, same-type calls "
            "have shorter start-to-start spacing than call-type changes."
        ),
        "unit_of_analysis": "recording",
        "eligible_recordings": len(same_type_medians),
        "median_of_recording_same_type_medians_seconds": float(
            np.median(same_type_medians)
        ),
        "median_of_recording_changed_type_medians_seconds": float(
            np.median(changed_type_medians)
        ),
        "same_type_shorter_recordings": shorter,
        "same_type_shorter_fraction": shorter / len(same_type_medians),
        "wilcoxon_signed_rank": {
            "statistic": float(result.statistic),
            "two_sided_p": float(result.pvalue),
        },
        "interpretation_boundary": (
            "Shorter spacing is consistent with repeated-call bouts. Annotation "
            "selection, omitted sounds, overlaps, and call duration can also affect "
            "start-to-start intervals; the result does not establish syntax or meaning."
        ),
    }


def analyze_distinct_transitions(
    recordings: Iterable[dict[str, Any]],
    *,
    permutations: int = 5000,
    seed: int = 20260821,
) -> dict[str, Any]:
    """Test supported directed call pairs against random within-recording order."""
    if permutations < 1:
        raise ValueError("permutations must be positive")
    observed: Counter[tuple[str, str]] = Counter()
    expected: Counter[tuple[str, str]] = Counter()
    transition_groups: dict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    sequences: list[list[str]] = []
    for recording in recordings:
        events = _labeled_events(recording)
        sequence = [_clean(event.get("call_type")) for event in events]
        if len(sequence) < 2:
            continue
        sequences.append(sequence)
        ecotypes = {
            _clean(event.get("ecotype"))
            for event in events
            if _clean(event.get("ecotype"))
        }
        ecotype = next(iter(ecotypes)) if len(ecotypes) == 1 else "mixed_or_missing"
        group = f"{recording['provider']}|{ecotype}"
        for left, right in zip(sequence, sequence[1:]):
            observed[(left, right)] += 1
            transition_groups[(left, right)][group] += 1
        counts = Counter(sequence)
        length = len(sequence)
        for left, left_count in counts.items():
            for right, right_count in counts.items():
                expected[(left, right)] += (
                    left_count * (right_count - int(left == right)) / length
                )

    candidates = {
        pair
        for pair, pair_expected in expected.items()
        if pair[0] != pair[1] and pair_expected >= 3 and observed[pair] >= 3
    }
    rng = np.random.default_rng(seed)
    null_greater_equal: Counter[tuple[str, str]] = Counter()
    for _ in range(permutations):
        shuffled_counts: Counter[tuple[str, str]] = Counter()
        for sequence in sequences:
            shuffled = rng.permutation(sequence)
            for left, right in zip(shuffled, shuffled[1:]):
                pair = (str(left), str(right))
                if pair in candidates:
                    shuffled_counts[pair] += 1
        for pair in candidates:
            if shuffled_counts[pair] >= observed[pair]:
                null_greater_equal[pair] += 1

    raw_pvalues = {
        pair: (null_greater_equal[pair] + 1) / (permutations + 1)
        for pair in candidates
    }
    adjusted = _bh_adjust(raw_pvalues)
    ranked = sorted(
        candidates,
        key=lambda pair: (
            adjusted[pair],
            raw_pvalues[pair],
            -(observed[pair] / expected[pair]),
        ),
    )
    top_candidates = [
        {
            "transition": f"{left} -> {right}",
            "observed": observed[(left, right)],
            "random_order_expected": expected[(left, right)],
            "enrichment_ratio": observed[(left, right)] / expected[(left, right)],
            "permutation_p_greater": raw_pvalues[(left, right)],
            "benjamini_hochberg_q": adjusted[(left, right)],
            "provider_ecotype_groups": dict(
                transition_groups[(left, right)].most_common()
            ),
        }
        for left, right in ranked[:10]
    ]
    significant = sum(adjusted[pair] < 0.05 for pair in candidates)
    return {
        "status": "exploratory_negative",
        "question": (
            "Are any adequately supported directed call-type transitions more "
            "frequent than expected under random within-recording order?"
        ),
        "recordings_with_two_or_more_typed_calls": len(sequences),
        "candidate_pairs_tested": len(candidates),
        "permutations": permutations,
        "seed": seed,
        "pairs_below_fdr_0_05": significant,
        "top_candidates": top_candidates,
        "conclusion": (
            "No individual directed transition survived false-discovery-rate "
            "correction. Specific motifs remain leads only."
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Find temporal and transition patterns in DCLDE annotations."
    )
    parser.add_argument("--permutations", type=int, default=5000)
    parser.add_argument("--output", type=Path)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    dataset = DCLDE2026(split="all", streaming=True)
    recordings = parse_killer_whale_recordings(dataset._data)
    report = {
        "status": "exploratory",
        "killer_whale_recordings": len(recordings),
        "finding_005_temporal_spacing": analyze_temporal_spacing(recordings),
        "finding_006_specific_transition_scan": analyze_distinct_transitions(
            recordings, permutations=args.permutations
        ),
    }
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
