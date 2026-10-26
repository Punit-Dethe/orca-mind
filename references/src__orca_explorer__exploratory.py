"""Reproduce exploratory annotation findings without fetching DCLDE audio."""

from __future__ import annotations

import argparse
import csv
import json
import math
from collections import Counter, defaultdict
from io import StringIO
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from alp_data.datasets import DCLDE2026
from scipy.stats import kruskal, mannwhitneyu


def _clean(value: object) -> str:
    return str(value or "").strip()


def parse_killer_whale_recordings(
    rows: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Parse manifest rows into recording-level killer-whale event sequences."""
    recordings: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        events: list[dict[str, Any]] = []
        annotations = csv.DictReader(StringIO(row["selection_table"]), delimiter="\t")
        for annotation in annotations:
            if _clean(annotation.get("species")) != "Killer whale":
                continue
            parsed = dict(annotation)
            parsed["_begin"] = float(_clean(annotation.get("Begin Time (s)")) or 0.0)
            events.append(parsed)
        if not events:
            continue
        recordings.append(
            {
                "recording_id": _clean(row.get("audio_path")) or f"row-{index}",
                "provider": _clean(row.get("provider")),
                "duration_seconds": float(row.get("audio_duration") or 0.0),
                "events": events,
            }
        )
    return recordings


def _single_value(events: list[dict[str, Any]], field: str) -> str | None:
    values = {_clean(event.get(field)) for event in events if _clean(event.get(field))}
    return next(iter(values)) if len(values) == 1 else None


def _holm_adjust(pvalues: dict[str, float]) -> dict[str, float]:
    ordered = sorted(pvalues.items(), key=lambda item: item[1])
    adjusted: dict[str, float] = {}
    running_max = 0.0
    total = len(ordered)
    for index, (name, pvalue) in enumerate(ordered):
        running_max = max(running_max, min(1.0, (total - index) * pvalue))
        adjusted[name] = running_max
    return adjusted


def analyze_onc_call_type_richness(
    recordings: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    """Compare per-recording labeled call-type richness within one provider."""
    groups: dict[str, list[float]] = {"OKW": [], "SRKW": [], "TKW": []}
    for recording in recordings:
        if recording["provider"] != "ONC":
            continue
        events = recording["events"]
        ecotype = _single_value(events, "ecotype")
        if ecotype not in groups:
            continue
        call_types = {
            _clean(event.get("call_type"))
            for event in events
            if _clean(event.get("call_type")).casefold() not in {"", "unk", "unknown"}
        }
        if call_types:
            groups[ecotype].append(float(len(call_types)))

    if any(not values for values in groups.values()):
        raise ValueError("All three ONC ecotypes need labeled call-type recordings")
    overall = kruskal(*(groups[ecotype] for ecotype in groups))
    raw_pairwise: dict[str, float] = {}
    pairwise_stats: dict[str, float] = {}
    names = list(groups)
    for left_index, left in enumerate(names):
        for right in names[left_index + 1 :]:
            result = mannwhitneyu(groups[left], groups[right], alternative="two-sided")
            comparison = f"{left}_vs_{right}"
            raw_pairwise[comparison] = float(result.pvalue)
            pairwise_stats[comparison] = float(result.statistic)
    adjusted = _holm_adjust(raw_pairwise)

    return {
        "status": "exploratory",
        "finding": (
            "Per-recording labeled call-type richness differs among OKW, SRKW, "
            "and TKW within the ONC provider subset."
        ),
        "unit_of_analysis": "recording",
        "provider_held_constant": "ONC",
        "by_ecotype": {
            ecotype: {
                "recordings": len(values),
                "median_unique_call_types": float(np.median(values)),
            }
            for ecotype, values in groups.items()
        },
        "kruskal_wallis": {
            "h": float(overall.statistic),
            "p": float(overall.pvalue),
        },
        "pairwise_mann_whitney": {
            comparison: {
                "u": pairwise_stats[comparison],
                "p_unadjusted": raw_pairwise[comparison],
                "p_holm": adjusted[comparison],
            }
            for comparison in raw_pairwise
        },
        "interpretation_boundary": (
            "Richness describes supplied human labels in selected recordings, "
            "not complete repertoire size in the wild."
        ),
    }


def _adjacent_matches(sequence: list[str]) -> int:
    return sum(left == right for left, right in zip(sequence, sequence[1:]))


def _random_order_expected_matches(sequence: list[str]) -> float:
    counts = Counter(sequence)
    return sum(count * (count - 1) for count in counts.values()) / len(sequence)


def analyze_call_type_adjacency(
    recordings: Iterable[dict[str, Any]],
    *,
    permutations: int = 5000,
    seed: int = 20260821,
) -> dict[str, Any]:
    """Test whether identical call labels cluster adjacently within recordings."""
    if permutations < 1:
        raise ValueError("permutations must be positive")
    sequences: list[list[str]] = []
    subgroups: dict[tuple[str, str], list[list[str]]] = defaultdict(list)
    for recording in recordings:
        events = sorted(recording["events"], key=lambda event: event["_begin"])
        sequence = [
            _clean(event.get("call_type"))
            for event in events
            if _clean(event.get("call_type")).casefold() not in {"", "unk", "unknown"}
        ]
        if len(sequence) < 3 or len(set(sequence)) < 2:
            continue
        sequences.append(sequence)
        ecotype = _single_value(events, "ecotype") or "mixed_or_missing"
        subgroups[(recording["provider"], ecotype)].append(sequence)

    observed = sum(_adjacent_matches(sequence) for sequence in sequences)
    pair_count = sum(len(sequence) - 1 for sequence in sequences)
    rng = np.random.default_rng(seed)
    null_matches = np.empty(permutations, dtype=int)
    encoded = [np.asarray(sequence, dtype=object) for sequence in sequences]
    for permutation in range(permutations):
        null_matches[permutation] = sum(
            int(np.sum((shuffled := rng.permutation(sequence))[:-1] == shuffled[1:]))
            for sequence in encoded
        )

    large_subgroups: dict[str, dict[str, Any]] = {}
    for (provider, ecotype), group_sequences in subgroups.items():
        if len(group_sequences) < 10:
            continue
        group_pairs = sum(len(sequence) - 1 for sequence in group_sequences)
        group_observed = sum(_adjacent_matches(sequence) for sequence in group_sequences)
        group_expected = sum(
            _random_order_expected_matches(sequence) for sequence in group_sequences
        )
        large_subgroups[f"{provider}|{ecotype}"] = {
            "recordings": len(group_sequences),
            "adjacent_pairs": group_pairs,
            "observed_match_rate": group_observed / group_pairs,
            "random_order_expected_rate": group_expected / group_pairs,
            "rate_difference": (group_observed - group_expected) / group_pairs,
        }

    null_mean = float(np.mean(null_matches))
    return {
        "status": "exploratory",
        "finding": (
            "Identical call-type labels occur adjacently more often than expected "
            "under random within-recording order."
        ),
        "eligible_recordings": len(sequences),
        "adjacent_pairs": pair_count,
        "observed_matches": observed,
        "observed_match_rate": observed / pair_count,
        "random_order_mean_matches": null_mean,
        "random_order_mean_rate": null_mean / pair_count,
        "absolute_rate_difference": (observed - null_mean) / pair_count,
        "permutation_p_greater": float(
            (int(np.sum(null_matches >= observed)) + 1) / (permutations + 1)
        ),
        "permutations": permutations,
        "seed": seed,
        "large_provider_ecotype_subgroups": large_subgroups,
        "interpretation_boundary": (
            "Clustering can indicate bouts or repeated-call sequences, but may also "
            "reflect recording selection and annotation practice. It does not "
            "demonstrate syntax, turn-taking, or meaning."
        ),
    }


def analyze_standard_split_pod_labels(rows: Iterable[dict[str, Any]]) -> dict[str, Any]:
    """Quantify call-type/pod-label coupling in the curated SRKW split."""
    joint: Counter[tuple[str, str]] = Counter()
    providers: Counter[str] = Counter()
    for row in rows:
        provider = _clean(row.get("provider"))
        annotations = csv.DictReader(StringIO(row["selection_table"]), delimiter="\t")
        for annotation in annotations:
            if _clean(annotation.get("species")) != "Killer whale":
                continue
            pod = _clean(annotation.get("pod"))
            call_type = _clean(annotation.get("call_type"))
            if not pod or not call_type:
                continue
            joint[(pod, call_type)] += 1
            providers[provider] += 1

    total = sum(joint.values())
    pod_counts: Counter[str] = Counter()
    call_counts: Counter[str] = Counter()
    for (pod, call_type), count in joint.items():
        pod_counts[pod] += count
        call_counts[call_type] += count

    mutual_information = 0.0
    for (pod, call_type), count in joint.items():
        probability = count / total
        mutual_information += probability * math.log(
            probability / ((pod_counts[pod] / total) * (call_counts[call_type] / total))
        )
    pod_entropy = -sum(
        (count / total) * math.log(count / total) for count in pod_counts.values()
    )
    call_entropy = -sum(
        (count / total) * math.log(count / total) for count in call_counts.values()
    )
    normalized_mutual_information = mutual_information / math.sqrt(
        pod_entropy * call_entropy
    )
    majority_correct = sum(
        max(count for (pod, label), count in joint.items() if label == call_type)
        for call_type in call_counts
    )

    return {
        "status": "dataset_audit",
        "finding": (
            "Call type and supplied pod-group label are strongly coupled in the "
            "vfpa_srkw_standard split, creating label-leakage risk."
        ),
        "annotated_segments": total,
        "providers": dict(providers),
        "pod_group_counts": dict(pod_counts),
        "unique_call_types": len(call_counts),
        "call_type_to_majority_pod_accuracy_same_data": majority_correct / total,
        "majority_pod_baseline_accuracy": max(pod_counts.values()) / total,
        "normalized_mutual_information": normalized_mutual_information,
        "coverage_warning": (
            "There are no K-only labels, only 25 L-only labels, and 408 combined "
            "pod-group labels (K/L, J/K/L, or J/L)."
        ),
        "interpretation_boundary": (
            "This split cannot independently establish pod dialects by predicting "
            "pod from call-type labels; the variables are already entangled."
        ),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Reproduce metadata-only exploratory DCLDE findings."
    )
    parser.add_argument("--permutations", type=int, default=5000)
    parser.add_argument("--output", type=Path)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    all_dataset = DCLDE2026(split="all", streaming=True)
    recordings = parse_killer_whale_recordings(all_dataset._data)
    standard_dataset = DCLDE2026(split="vfpa_srkw_standard", streaming=True)
    report = {
        "status": "exploratory",
        "killer_whale_recordings_in_all_split": len(recordings),
        "finding_002_call_type_richness": analyze_onc_call_type_richness(recordings),
        "finding_003_call_type_adjacency": analyze_call_type_adjacency(
            recordings, permutations=args.permutations
        ),
        "finding_004_pod_label_entanglement": analyze_standard_split_pod_labels(
            standard_dataset._data
        ),
    }
    rendered = json.dumps(report, indent=2, ensure_ascii=False)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered + "\n", encoding="utf-8")
    print(rendered)


if __name__ == "__main__":
    main()
