# Known-object reference policy

Apply this policy within the current [experiment procedure](experiments/PROCEDURE.md).
The initial scientific focus covers asteroids and exoplanets.
Additional targets require appropriate reference sources and matching rules.
Reference catalogs support identity comparisons and recovery measurements.
Catalog absence does not establish a new discovery.

## Reference sources

| Target | Source | Role |
|---|---|---|
| Asteroids | [MPCORB](datasets/mpcorb/README.md) | Known-object identifiers and orbital elements for local calculations. |
| Asteroids | [JPL SBDB](datasets/jpl-sbdb/README.md) | Orbital solutions, uncertainties, aliases, and physical properties. |
| Asteroids | [JPL identification API](https://ssd-api.jpl.nasa.gov/doc/sb_ident.html) | Known objects in a specified field at an observation time and observer location. |
| Asteroids | [SkyBoT](datasets/skybot/README.md) | Saved field-and-time predictions with observer geometry and uncertainty. |
| Exoplanets | [NASA Exoplanet Archive](datasets/nasa-exoplanet-archive/README.md) | Confirmed planets, host stars, and published parameters through its table-query service. |

Keep confirmed exoplanets and unconfirmed candidates separately identified.
Preserve the provider's classification, including false-positive classifications when available.
The [TESS recovery record](experiments/tess-known-planet-recovery/README.md) preserves the first bounded NASA Exoplanet Archive subset.
Dataset entries and experiment manifests identify actual acquisitions.
They do not establish complete local catalogs or application integration.

## Acquisition and preservation

Use official downloads or APIs to obtain reference records.
Save dated local copies of the selected records or query responses.
Use internet searches for supporting investigation, not as the catalog identity system.
A complete local catalog is optional. A saved, bounded query response can satisfy an experiment's needs.

Record these fields for each reference acquisition:

- Provider, catalog name, and release or API version when available.
- Retrieval time in UTC and the exact query or download address.
- Query parameters, including field, observation time, and observer location when applicable.
- File size, checksum, format, and local storage location.
- Units, coordinate frame, time convention, and applicable parameter epoch.
- Selection limits, pagination, truncation, errors, and known coverage limits.

Preserve the original response alongside any normalized records.
Store large catalog files in `raw/<dataset-id>/` at the workspace root.
Store their manifests and checksums with the experiment evidence.
Do not replace an experiment's reference copy when the provider updates its catalog.
Acquire a new copy for a new comparison and retain both acquisition records.
An unavailable service or incomplete response means comparison is incomplete, not that no known object matches.

## Identity comparison

An asteroid's catalog position is not fixed.
Compare predicted positions with measurements at the observation time and observer location.
Record prediction software or service, orbital solution, uncertainty, matching tolerance, and motion agreement.
Preserve ambiguous matches and alternative identities.

For exoplanets, retain planet identifiers, host-star identifiers, aliases, and source references.
Compare the observed signal with applicable published parameters, including period and event epoch for transit searches.
A matching host star alone does not identify a planet.
Record uncertainty and the time convention used for event comparisons.

Keep identity status separate from scientific evidence quality.
Useful comparison states include matched, ambiguous, unmatched, and not checked.
An unmatched result applies only to the recorded catalog selection and matching rules.

## Experiment requirements

1. Link the observational dataset and detection method in `experiment.json`.
2. Declare each reference dataset's role before execution.
3. Link its saved acquisition manifest and exact reference copy.
4. Define the matching rules before interpreting identity comparisons.
5. Record whether catalog information influenced target selection or parameter tuning.
6. Save detection results before catalog comparison when claiming blind detection.
7. Preserve comparison results, failures, and ambiguous identities.

Known-object recovery tests may deliberately use catalog information.
Label those tests as guided and preserve their selection procedure.
Artificial-source recovery remains a separate measurement with its own limitations.
Neither test alone measures performance on all unknown objects.

Existing experiments retain their recorded catalog access order and limitations.
This policy does not retroactively turn a guided experiment into a blind experiment.
The next experiment must identify its required reference subset before acquisition or execution.
