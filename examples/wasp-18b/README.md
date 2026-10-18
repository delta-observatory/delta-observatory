# Example investigation: WASP-18 b period search range

This directory holds evidence exports of one recorded investigation in the running application.
Each file is the unchanged response of an export endpoint of the API.
The exports contain stored values only. No new scientific run produced them.

## Investigation

| Item | Value |
|---|---|
| Question | Does a wider period search find a stronger signal in the same light curve? |
| Observation | TESS SPOC 120-second light curve of TIC 100100827, sector 2. The known planet is WASP-18 b. |
| Method | `tess-bls` version 1, with the parameters of the closed T01 known-planet recovery experiment. |
| Run A | `e0534db5-b3c5-47c2-bd47-b974916e6773`, `maximum_period` 10 days, 46 development light curves. |
| Run B | `4dc34144-7504-4b3a-b25b-78fdae5d9005`, `maximum_period` 20 days, this light curve only. |
| Other parameters | Identical in both runs. |
| Candidate | `T01-A`, `da282d45-bd48-4eb8-8071-c2108475961f`, imported from the T01 experiment record. |
| Assessment | `71bfc528-74ce-4e67-9b94-8596e70e3a13`: evidence axis, status `supported`, basis `review`. |

The run labels are historical. Run A was the slice check, and run B was a frontend test with one changed parameter.

## Result

Both runs give the same best signal for this light curve:

| Measurement | Value |
|---|---|
| Period | 0.941385 d |
| Relative period error against the WASP-18 b reference | 7.2e-5 |
| Transit time error against the reference | 0.00067 d |
| Depth | 0.00947 ± 0.0000145 (formal) |
| Observed transits | 28 |

The values are equal to all stored digits.
Astropy builds the period grid from `minimum_period`, so the 20-day grid contains every trial of the 10-day grid.
The wider search therefore found no stronger peak.

## Limitations

- The light curve is development data. The candidate is a known planet. The result shows recovery, not discovery.
- The even and odd transit depths (0.00999 and 0.00890) differ by about 38 times their formal uncertainties. The formal uncertainties do not include correlated noise. The assessment does not interpret this difference.
- Depth accuracy, completeness, and false-alarm rates are not validated.
- The candidate is a `lab` candidate. Its own evidence is a set of external T01 files. The export lists those files by URI, SHA-256, and size, and it does not include them.

## Files

| File | Endpoint | Content | Manifest SHA-256 |
|---|---|---|---|
| `run-4dc34144-max-period-20d.zip` | `GET /api/runs/4dc34144-…/export?artifacts=all` | Run B, its job and measurements, the light curve, the prepared series, the periodogram, and the research records that refer to the run, including the assessment. 3.2 MB. | `70c0c9b61a51119871f454235cf2d73ea077f3ac8638c906b00a52ba768149a0` |
| `run-e0534db5-max-period-10d-records.zip` | `GET /api/runs/e0534db5-…/export?artifacts=none` | Run A: 46 jobs and their measurements, without artifact files. | `3ecef3c2d0fd19e3266bc73b7d2021fcbd5105e7f58e115c1d4ce2fdbee982db` |
| `candidate-t01a-records.zip` | `GET /api/candidates/da282d45-…/export?artifacts=none` | The candidate with its assessment. A candidate export includes only the candidate's own evidence, not the runs that an assessment cites. | `202695b857d656dc43e548c3e1e6bb0fae9c2cd116a239f1de05b1cd9f4972ad` |

`SHA256SUMS` gives the SHA-256 of each ZIP file.
Each export names its contract source as `database` commit `00913dda1c67d56a8fcd29321f6f4b309204faad`, the commit hash when the API made the export.
The same contracts are at `database` commit `4e0d1ae6724f859053b6b7579cc3f09da4425bd4` in the published history. The export files are unchanged, so their SHA-256 values stay valid.
The manifest SHA-256 is the value of the `X-Export-Manifest-SHA256` response header.

## Check the exports

`scripts/verify_export.py` in the [backend repository](https://github.com/delta-observatory/backend) needs only the Python standard library.
`--schema` also checks the manifest against contract `export/1`, and it needs `jsonschema`.
Run these commands from the entry repository after `python3 scripts/components.py clone`:

```bash
(cd examples/wasp-18b && sha256sum -c SHA256SUMS)
python3 backend/scripts/verify_export.py examples/wasp-18b/run-4dc34144-max-period-20d.zip \
  --manifest-sha256 70c0c9b61a51119871f454235cf2d73ea077f3ac8638c906b00a52ba768149a0
```

The script checks the size and SHA-256 of each listed file, unlisted files, and unsafe paths.
It prints a JSON report, and its exit status is 1 when a check fails.

## Data credits

The light curve comes from the TESS mission through MAST. The reference values come from the NASA Exoplanet Archive.
[ACKNOWLEDGMENTS.md](../../ACKNOWLEDGMENTS.md) gives the required statements.
