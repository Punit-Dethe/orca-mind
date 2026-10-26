# OrcaMind

A metadata-first killer whale communication research dashboard for a Data Warehousing and Data Mining project. Explore real annotations, trace events to source recordings, inspect observed call transitions, and read the evidence behind reported research findings.

**No translations, invented observations, or claims of independently reproduced statistical tests.**

## Run locally

Requires Node.js 18+; no npm dependencies or install step.

```bash
git clone https://github.com/Punit-Dethe/orca-mind.git
cd orca-mind
npm start
```

Open **http://localhost:5173**. The checked-in `dist/` includes verified, precomputed data, so the dashboard starts without downloading the raw CSV or audio. Alternatively, `python3 -m http.server 5173 --directory dist` works. ES modules and JSON requests require HTTP; opening `index.html` directly as a file will not work.

## What works

- **Overview:** scoped annotation counts, recording counts, supplied call labels, ecotype composition, provider coverage and a sourced research highlight.
- **Call Atlas:** searchable raw call labels, event-duration histograms, ecotype coverage, next-call counts, source recordings, searchable/paginated recording explorer and zoomable event timelines. Real overlap lanes, event metadata and same-label highlighting.
- **Communication Patterns:** directed transition network, count/probability matrix, count threshold, label focus and pair-level calculation explanations. Reported repetition/timing results remain separate from filtered, descriptive calculations.
- **Population Intelligence:** ecotype comparisons, normalized or raw repertoire frequencies, and provider composition to expose source confounding.
- **Research Discoveries:** four expandable, attributed findings with questions, methods, sample sizes, interpretation and limitations, including the negative multiple-testing result.
- **Data Warehouse:** real ETL row accounting, missing-data diagnostics, schema/provenance, the implemented dimensional projection and interactive OLAP pivot/slicing.
- **Mining Laboratory:** an explicitly planned methodology roadmap; no fake run buttons or model scores.
- Global source/provider/ecotype/species filters; CSV export with scope and source hash.
- Light theme by default, with a saved dark-theme toggle; blue, coral and muted-violet data colors.

## Two source snapshots, kept separate

| Snapshot | Annotation events | Source recordings | Named killer whale events* | Provider count |
| --- | ---: | ---: | ---: | ---: |
| Original compiled CSV | 207,574 | 13,084 | Unavailable | 10 |
| Earth Species Project enriched manifest | 186,972 | 9,883 | 7,418 | 9 |

\* Non-empty KW call labels, excluding exact `Unk` and `unknown`; ambiguous and compound supplied labels remain unaltered. Counts describe annotations, not animal abundance or complete repertoires.

The enriched source is the default because it contains the actual call-type annotations needed by the atlas and sequence views. The original CSV contains `ClassSpecies` but **no call-type identifier**. Its species categories must never be relabeled as vocal repertoires. The enriched dataset excludes UAF_NGOS and differs in taxonomy and preprocessing. No observation-level merge is performed.

See [dataset documentation](docs/DATA.md), [presentation walkthrough](docs/PRESENTATION.md), and [reproduction plan](docs/REPRODUCTION.md).

## Rebuild the data warehouse

Python 3.10+; standard library only. No audio requests or third-party Python packages are required.

```bash
python3 scripts/download.py --enriched
python3 scripts/ingest.py
```

The downloader verifies both source hashes. The enriched URL is mutable; if its bytes have changed, the script stops for schema review and preserves any previous local snapshot. Checked-in precomputations still run offline. The original CSV is pinned to a Git commit.

The ETL generates:

- `data/warehouse.sqlite`: event and transition fact tables, natural-key dimension views, and an index for recording queries (generated locally, ignored by git).
- `dist/data/<source>/summary.json`: analytical cube, transition counts and actual ETL/quality/provenance information.
- `dist/data/<source>/recordings.json`: source-specific recording index.
- `dist/data/<source>/events-0.json` through `events-63.json`: compact, lazy-loaded annotation blocks.
- `docs/<source>-schema.json`: machine-readable inspected schema and quality report.

All source events are retained, including duplicate candidates and invalid intervals. Invalid intervals are excluded from durations and sequences, with explicit flags. Named transitions omit unknown/unlabeled events, retain overlaps, and have no maximum-gap cutoff. This eligibility differs from the reference test. See `docs/DATA.md`.

## Verify

```bash
npm run check
npm test
# Offline parsing/JSON checks; SQL integration checks also run when a local warehouse exists:
python3 -m unittest discover -s tests -v
```

Tests cover parsing, missing/invalid measurements, deterministic call order, overlaps, counts, filtering, export escaping, source separation and aggregate conservation. Browser QA covered search/drill-down, timeline loading, source/provider filtering, the count/probability matrix, and calculated pair explanations. Responsive CSS is provided; device-specific mobile QA is not claimed.

## Architecture

```text
scripts/download.py   → original metadata snapshots (data/raw, ignored)
scripts/ingest.py     → SQLite warehouse + precomputed source-specific JSON
static dashboard     → summary/index JSON + lazy per-recording event block
```

The frontend uses native JavaScript modules, accessible HTML controls, CSS and inline SVG; it is intentionally buildless. This keeps local demos and static hosting dependency-free. Statistical processing stays in Python, outside rendering. No 50 MB raw CSV is sent to the browser. New API/data-access implementations can replace the current precomputed query layer later.

`dist/app.js` contains the seven views and interaction handlers; `dist/data-utils.js` centralizes pure filtering, grouping, output escaping and export. `scripts/serve.mjs` is a small local static server. Sites hosting uses `.openai/hosting.json`. No cloud database, authentication backend, model endpoint or paid API is necessary.

## Scientific boundaries and deferred work

The reference's 47.9%/34.8% repetition result, timing comparison and p/q-values are **reported**, not independently reproduced here. Dashboard transitions are descriptive calculations on the loaded snapshot, with different eligibility. Network edges are annotation transitions, not relationships between individual whales. Raw composite/uncertain labels are not split or silently standardized.

No audio player, spectrogram, geographic pins, null-distribution histogram, confidence intervals or experiment execution is provided. Raw audio availability was not validated. Independent permutation tests, repertoire similarity with evaluation, K-Means/hierarchical clustering, Apriori/FP-Growth and grouped classification remain later work. Negative findings must remain visible.

## Sources and licensing

- [JPalmerK / DCLDE_Dataset](https://github.com/JPalmerK/DCLDE_Dataset), pinned CSV snapshot and original processing repository.
- [Earth Species Project / alp-data DCLDE2026](https://github.com/earthspecies/alp-data/blob/main/alp_data/datasets/dclde2026.py), enriched metadata manifest, declared CC-BY-4.0.
- Palmer et al., *A Public Dataset of Annotated Orcinus orca Acoustic Signals for Detection and Ecotype Classification*: https://doi.org/10.1038/s41597-025-05281-5.
- [Djay96 / orca-dclde-explorer](https://github.com/Djay96/orca-dclde-explorer), reported exploratory findings and statistical implementation references. Its MIT license is preserved in `references/LICENSE`.

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for attribution. Application code is MIT licensed; source datasets retain their original terms.
