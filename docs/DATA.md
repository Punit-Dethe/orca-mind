# Dataset inspection and transformation contract

## Source 1: original compiled annotations

Repository commit: `2ceee82d0aeb0be45bf95e74806771f35be75f37`.
File: `dclde_2026_dclde_2026_killer_whales_Annotations.csv`.
Verified size: 50,276,877 bytes.
SHA-256: `f9b5bca4d276cf46259063b9a0e5b47433b0123fa1cdb0e0b0a2766b4eb7ac88`.

| Exact CSV column | Use and limitations |
| --- | --- |
| Unnamed first column | Supplied row identifier; retained as event_id |
| Soundfile | Display filename |
| Dataset | Source coverage label (32 observed values); not validated coordinates or necessarily 32 distinct research sites |
| LowFreqHz / HighFreqHz | Supplied frequency bounds; missing for 2,398 rows each |
| FileBeginSec / FileEndSec | Within-recording event boundaries in seconds |
| UTC | Supplied timestamp, preserved without assuming uniform recording-start semantics |
| ClassSpecies | Four original codes: HW 124,977; KW 59,107; UndBio 11,821; AB 11,669 |
| KW | Binary source killer-whale indicator; not a call type |
| KW_certain | Source-supplied KW certainty indicator, not a calibrated probability; 149,415 missing |
| Ecotype | SRKW, TKW, NRKW, SAR, OKW; 154,917 missing |
| Provider | 10 supplied providers |
| AnnotationLevel | Detection, Call, File; different granularity, not identical events |
| FilePath | Full supplied path used as the source-qualified recording identity |
| FileOk | TRUE for all imported rows; it does not verify currently accessible audio |

207,574 events; 13,084 unique recording paths. 79 exact-field duplicate candidates are retained. No invalid time or frequency intervals were detected using the implemented validators. Zero-duration intervals are allowed and retained; no acoustic meaning is inferred from them.

The blank call field in normalized output means the source does **not** supply fine call identifiers. There is no pod, clan, named call type, precise coordinate or standardized confidence-probability column to invent. AB is shown as its source code; no expansion is assumed by this implementation.

## Source 2: enriched manifest

Public URL is recorded in `docs/enriched-schema.json`. Earth Species Project's `alp-data` implementation declares the `all` split at `gs://esp-data-274503/dclde2026/v0.1.0/raw/2026/dclde_2026_killer_whales/processed_enriched_v2.csv`.
SHA-256: `3f428d361008666c42369d471e12c8f05412057af547a42bdf5dd560e5912bf9`.

The CSV contains 9,883 recording rows, each with a TSV-serialized `selection_table`. Expanding those tables yields 186,972 event rows, including 47,497 killer whale events and 7,418 eligible named KW labels. 19 duplicate candidates are retained. The manifest declares 9 providers and excludes UAF_NGOS; do not assume it is equivalent to the original CSV.

The nested table supplies `Begin Time (s)`, `End Time (s)`, `Low Freq (Hz)`, `High Freq (Hz)`, `species`, `canonical_name`, `sound_detail`, `ecotype`, `call_type`, `acoustic_behavior`, `pod`, `clan`, `annotation_level`, `confidence`, `genus`, `family`, `species_common`, and `coarse_call_type`. Full actual outer and nested field names are recorded in the schema report. This first-release normalized event projection uses timing, frequency, species, ecotype, call, level and confidence. Other source fields remain in the raw manifest and are not fabricated or implicitly joined into the compiled source.

The richer source has no normalized UTC or location mapping in this implementation. Their UI state is unavailable. Do not infer coordinates or calendar trends from offsets or filenames.

## Identity and transformations

- Sources remain separate everywhere, including SQLite keys, source selectors, file blocks and exports.
- Compiled recording identity is full FilePath; enriched identity is audio_path. Never join on basename alone.
- Raw source bytes are unchanged. `NA`, `nan`, `null`, `none` and empty normalized strings are treated as missing; numeric non-finite values become null.
- Valid interval means finite start/end, start ≥ 0, end ≥ start. Duration = end − start for valid intervals; invalid rows stay in event facts.
- Duplicate candidates match recording, start/end, species, call, ecotype, annotation level and frequency bounds. No automatic deduplication.
- Distinct recording counts use set unions rather than sums of per-group counts.
- Duration summaries and histogram bins use valid intervals only. Bin bounds in seconds: ≤0.25, (0.25,0.5], (0.5,1], (1,2], (2,5], (5,10], (10,30], >30.
- Provider, ecotype and annotation-level labels remain as supplied; no arbitrary typo correction, compound-label splitting or biological reassignment.

## Transition policy

1. Group events by source-qualified recording identity.
2. Keep valid killer whale events with a non-empty call label except exact case-insensitive `Unk` and `unknown`.
3. Sort by numeric start, then source event ID for deterministic ties.
4. Form each consecutive pair. Overlapping intervals remain pairs; the signed end-to-start gap can be negative.
5. Preserve call labels verbatim, including uncertain and compound labels.
6. No maximum gap is imposed. Omitted or unlabeled annotations can lie between adjacent typed events.
7. Provider/ecotype filtering on precomputed pairs uses the **starting event's** attributes. The pair's second label may have a different or missing ecotype.

The enriched snapshot produces 6,841 descriptive pairs. The reference's reproduction subset additionally requires ≥3 typed calls and ≥2 distinct types per recording. Its 5,806-pair result must not be compared directly with our broader 6,841-pair total as if the eligibility were identical.

Matrix P(B|A) uses count(A→B) / count(all outgoing pairs from A) after scope filters. Edges hidden by minimum count or top-12 truncation remain in the denominator. Network node size is incident pair count, not unique animal count. No p-values are assigned to these filtered edges.

## Dimensional implementation

`Fact_CallEvent` has one row per source annotation. `Fact_CallTransition` has one row per eligible successive pair. Distinct views provide recording, call type, population, provider and source-location dimensions. Source-qualified natural keys are used; surrogate IDs and enforced foreign keys are deferred. UTC is retained as an event attribute; no inferred date dimension exists. SQLite remains a local analytical artifact; the hosted dashboard queries its precomputed outputs.

## Compact event blocks

Recording ID modulo 64 selects the lazily requested block. An event array follows:
`[id, start, end, species, call, population, level, low, high, utc, confidence]`.
The recording object supplies path and provider. JSON uses null for unavailable numeric measurements. No raw 50 MB CSV is processed by the client.

## Research provenance

Saved reference JSON/Markdown and the inspected algorithms/tests are in `references/`, from DCLDE Explorer at the commit recorded in `references/tree.json`. Findings are attributed as reported. They remain fixed under global UI filters. No raw permutation distribution was available in those saved files, so no invented null histogram is drawn. Separate Icelandic call-combination and social-network datasets have not been integrated.
