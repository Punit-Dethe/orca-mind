# From reported evidence to reproduced evidence

The current UI has two active evidence classes: **Dataset-derived** (our descriptive computations) and **Reported** (source-attributed reference results). The Mining Laboratory is **Planned**. No “Reproduced” badge is earned by copying reference JSON or matching a rounded percentage manually.

1. Pin the exact input version and hash used by DCLDE Explorer; check source provider coverage and original annotation schema before counting.
2. Inspect `references/src__orca_explorer__exploratory.py`, `patterns.py`, `hypothesis.py`, their tests, and saved outputs. The source parser retains killer whale events and the reference adjacency analysis requires ≥3 non-empty, non-unknown labels and ≥2 distinct labels per recording.
3. Implement that eligibility in a separate statistical module. Keep its output distinct from the broader dashboard transition table.
4. First compare eligible recording count, pair count and exact observed matches: reference 276, 5,806 and 2,782.
5. Run 5,000 within-recording permutations with the reference seed and the same random-number generator and statistic. Preserve each recording's complete label-count composition.
6. Save seed, source hash, algorithm version, sample size, observed statistic, null mean, simulation count, p formula and optionally null replicates. Monte Carlo p should use (1 + exceedances)/(1 + B).
7. Compare expected count and rate with the saved reference (roughly 2,023.1 / 34.8%), and observed rate (~47.9%). Do not alter preprocessing to force agreement. Record substantive differences.
8. Add a deterministic scientific regression check and a comparison artifact showing reference, calculated value, absolute difference and tolerance. Mark **Reproduced** only after this succeeds.
9. Extend to paired recording-level timing and the directed-pair scan; preserve multiple-testing correction and the negative result.

When statistical output exists, add it to a separately versioned research JSON document rather than replacing source annotations. Render its source hash, eligibility, filters and sample size beside the chart; include an explicit comparison panel. Keep the original reported source visible for audit.

Later experiments require a stated question, representation, recording-aware evaluation and baseline. Clustering must be checked for provider confounding. Apriori and FP-Growth need a bounded transaction definition. Classification must avoid using input fields that encode the answer or splitting events from the same recording between train and test.
