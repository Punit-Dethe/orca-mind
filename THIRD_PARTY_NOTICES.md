# Source attribution

## DCLDE data

Palmer et al. (2025), **A Public Dataset of Annotated Orcinus orca Acoustic Signals for Detection and Ecotype Classification**, DOI: https://doi.org/10.1038/s41597-025-05281-5. Original processing/compiled annotations: https://github.com/JPalmerK/DCLDE_Dataset. Original repository MIT notice is retained as `references/DATASET_LICENSE`; this code-repository license is not a claim that every underlying recording has identical licensing.

Enriched annotations are provided through Earth Species Project's `alp-data` DCLDE2026 interface, https://github.com/earthspecies/alp-data. The implementation declares CC-BY-4.0 for this dataset: https://creativecommons.org/licenses/by/4.0/. OrcaMind normalizes metadata into a source-specific analytical projection and precomputes descriptive aggregates; it does not distribute audio. Original providers retain attribution through the provider fields. Source data changes are documented in `docs/DATA.md` and machine-readable schema reports.

## Reference research

Djay96, **Orca Explorer**, https://github.com/Djay96/orca-dclde-explorer. Reported findings, saved JSON and inspected code/test references are retained under its MIT notice in `references/LICENSE`. OrcaMind's descriptive ingestion implementation is separate; copying saved research results does not constitute independent reproduction.

## Typography

DM Sans and Manrope are requested from Google Fonts, with system sans-serif fallbacks. The application remains usable without font network access. No downloaded font binaries are bundled.

## Hero photography

`dist/assets/orca-hero.jpg`: Southern Resident killer whale breaching, sourced from NOAA Fisheries' article [Limiting Chinook Fishing in Low-Return Years to Help Killer Whales](https://www.fisheries.noaa.gov/feature-story/limiting-chinook-fishing-low-return-years-help-killer-whales-what-do-you-think). Original image: https://www.fisheries.noaa.gov/s3/2021-06/srkw-breach.jpg?VersionId=null. Supplied photo bytes are preserved; the browser crops and fades the image with CSS for the hero layout. This is decorative wildlife photography, not a DCLDE recording observation.
