# Five-minute academic demonstration

**0:00 — The question.** Open Overview: “Can human acoustic annotations reveal statistically meaningful structures in killer whale vocalizations?” Explain that this is not language translation. Point to the data-source selector and evidence badges.

**0:40 — Real data and coverage.** Contrast the enriched source with the original compiled CSV. The latter has 207,574 annotations including other acoustic classes, and no fine call identifiers. Explain why a species class is not a vocal repertoire. Click a provider or species bar to slice the workspace; reset filters.

**1:20 — Inspect an observation.** Open Call Atlas in the enriched source. Search S04, open the exact label, inspect its counts/duration histogram, then choose a recording. Use timeline zoom and horizontal pan; click a real event. Explain overlapping lanes and the difference between annotated extent and recording duration.

**2:10 — Patterns and evidence.** Open Communication Patterns. First distinguish the fixed, reported 47.9% versus 34.8% comparison from the broader dataset-derived transition graph. Switch to the matrix and click a cell to show the actual numerator and denominator. Filter to ONC to demonstrate source stratification. Emphasize that zero of the reference's 224 directed candidates survived FDR correction.

**3:00 — Sampling limitations.** Open Population Intelligence, compare SRKW/TKW in counts and within-ecotype percentages, and inspect provider composition. Unequal annotation coverage cannot establish population abundance or complete repertoires.

**3:40 — DWDM implementation.** Open Data Warehouse. Show source → staging → SQLite facts → aggregates. Discuss event and transition grains, natural-key dimension views, missing fields, retained duplicates and actual ETL counts. Pivot rows and columns, slice by provider, export the filtered analytical cube.

**4:30 — Honest roadmap.** Open Research Discoveries for methods and limitations, then Mining Laboratory. Explain that permutation-test reproduction is next; clustering and association mining will follow a defensible scientific question and recording-level evaluation. No fabricated accuracy scores or completed experiments.

Course mapping: warehouse architecture/ETL/dimensions → Data Warehouse; raw data lake → preserved raw snapshots; KDD/preprocessing → schema/quality/timelines; frequent patterns and sequences → observed transitions plus planned permutation/association experiments; clustering and classification → explicitly future, evaluated methods.
