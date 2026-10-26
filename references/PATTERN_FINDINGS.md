# Temporal and transition patterns

This metadata-only analysis searches the ordering and timing of human-annotated
call types. It is exploratory and does not identify callers, receivers, or
meaning.

## Finding 005: repeated call types are closer together

For every recording containing at least one same-type transition and one
changed-type transition, the analysis calculated the median start-to-start
spacing of each transition kind. This gives each recording one paired
comparison instead of treating every transition as independent.

| Measure | Same call type | Call type changes |
|---|---:|---:|
| Eligible recordings | 256 | 256 |
| Median of recording-level median spacing | 4.44 seconds | 7.33 seconds |

Same-type spacing was shorter in 177/256 recordings (69.1%). A paired Wilcoxon
signed-rank test produced p = 2.43 × 10⁻¹².

Together with Finding 003's excess same-type adjacency, this is consistent with
repeated call types forming tighter temporal bouts. It does not establish
grammar or conversation: annotation selection, omitted/unlabeled sounds,
overlapping detections, and call duration can all affect the spacing.

## Finding 006: no specific directed motif survives correction

The scan tested 224 distinct directed call pairs having at least three observed
transitions and a random-order expectation of at least three. It used 5,000
within-recording reorderings and Benjamini–Hochberg false-discovery-rate
correction.

| Leading candidate | Observed | Expected | Enrichment | Raw p | Corrected q |
|---|---:|---:|---:|---:|---:|
| `T01 → T02` | 18 | 10.74 | 1.68× | 0.00140 | 0.314 |

Zero of the 224 pairs had q < 0.05. Therefore, this scan supports a general
tendency toward repeated-call bouts, but it does not support claiming a
specific multi-call motif. `T01 → T02` is suitable for a preregistered test on
independent TKW recordings, not for a current biological conclusion.

## Reproduce

```bash
uv run --no-sync orca-find-patterns --output PATTERN_FINDINGS_RESULTS.json
```

The machine-readable result is
[PATTERN_FINDINGS_RESULTS.json](PATTERN_FINDINGS_RESULTS.json).
