# Additional exploratory findings

These analyses use streamed DCLDE annotations without fetching audio. They were
selected after inspecting the data and are therefore hypothesis-generating,
not confirmatory.

## Finding 002: labeled call-type richness differs within ONC

To reduce provider confounding, the comparison uses only recordings supplied by
`ONC`, requires a single ecotype label, excludes empty/unknown call types, and
counts unique human call-type labels once per recording.

| Ecotype | Eligible recordings | Median unique labeled call types |
|---|---:|---:|
| `OKW` | 26 | 1.5 |
| `SRKW` | 23 | 1.0 |
| `TKW` | 24 | 1.0 |

The three-group Kruskal–Wallis test produced H = 11.89 and p = 0.00262.

| Pairwise comparison | Holm-adjusted p-value |
|---|---:|
| `OKW` vs `SRKW` | 0.00528 |
| `OKW` vs `TKW` | 0.0480 |
| `SRKW` vs `TKW` | 0.255 |

In this selected subset, `OKW` recordings contain a somewhat richer set of
supplied call-type labels. This overlaps with Finding 001—the extra `buzzer`
annotations contribute to richness—and must not be interpreted as the complete
wild repertoire of an ecotype.

## Finding 003: identical call labels cluster in sequence

Recordings were eligible when they contained at least three non-empty,
non-unknown call-type annotations and at least two distinct call types. The
observed order was compared with 5,000 random reorderings within each recording,
preserving each recording's exact call counts.

| Sequence measure | Observed | Random-order expectation |
|---|---:|---:|
| Eligible recordings | 276 | — |
| Adjacent call pairs | 5,806 | — |
| Same-type adjacent pairs | 2,782 | 2,023.1 |
| Same-type adjacency rate | 47.9% | 34.8% |

The absolute difference was 13.1 percentage points. None of the 5,000 random
reorderings reached the observed value, giving the corrected Monte Carlo
p = 1/5,001 = 0.000200.

The direction was also positive in all six provider/ecotype subgroups with at
least ten eligible recordings. That is consistent with calls occurring in
same-type bouts or repeated-call sequences. It is not evidence of grammar,
turn-taking, receiver response, or semantic meaning; recording selection and
annotation practice could also create clustering.

## Finding 004: pod labels are entangled with call-type labels

The `vfpa_srkw_standard` split contains 1,336 annotated segments and 27 call
types. Its supplied pod-group labels are highly imbalanced:

| Supplied pod label | Segments |
|---|---:|
| `J` | 903 |
| `K/L` | 219 |
| `J/K/L` | 184 |
| `L` | 25 |
| `J/L` | 5 |
| `K` | 0 |

A same-data lookup that assigns each call type to its most frequent pod-group
label reproduces 99.1% of pod-group labels, compared with a 67.6% majority-label
baseline. This is a dataset-audit result, not a biological discovery.

It means a model evaluated randomly on this split could appear excellent at
“pod recognition” by learning call-type/pod label coupling. There are no clean
`K` examples and very few clean `L` examples, so this split cannot support a
balanced, independent J/K/L pod-classification claim without additional data
and group-aware evaluation.

## Reproduce

```bash
uv run --no-sync orca-discover-findings --output EXPLORATORY_FINDINGS_RESULTS.json
```

The command streams annotation metadata only. The machine-readable result is
[EXPLORATORY_FINDINGS_RESULTS.json](EXPLORATORY_FINDINGS_RESULTS.json).
