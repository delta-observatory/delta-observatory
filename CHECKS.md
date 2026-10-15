# Workspace checks and consistency

The workspace contains research, bounded scientific experiments, and the TESS vertical slice of the application.
The current [workspace guide](README.md) defines document responsibilities and directory contents.
The current [experiment procedure](experiments/PROCEDURE.md) defines scientific requirements for new experiments.

## Repeatable structural check

Run this command from the workspace root:

```bash
python3 scripts/check_workspace.py
```

To save a report, select an unused output path:

```bash
python3 scripts/check_workspace.py --output /tmp/delta-workspace-check.json
```

The checker covers:

- Local Markdown paths and section references.
- Strict JSON parsing and Python syntax.
- Required workspace entry points and current procedure location.
- Dataset catalog counts, identities, metadata, related entries, and acquisition evidence links.
- Scientific task identities, prerequisite paths, dependency cycles, and diagram agreement.
- Experiment registration, dataset references, and method references.
- Retained source-file sizes, PDF headers, and SHA-256 hashes.
- Applicable experiment freeze, script, closure, and legacy input-manifest hashes.
- Generated caches, temporary files, and observation arrays inside experiment records.
- Generated caches in research repositories. The scan skips Git-ignored `__pycache__`, `node_modules`, `dist`, `build`, and `coverage` folders in the application repositories.
- Available Git status at the workspace and component boundaries.
- `raw/` directory names against dataset IDs. The checker does not read files inside `raw/`.

This is a workspace integrity checker.
The separate [common validator](experiments/RECORD-CONTRACT.md) checks new experiment records with their original inputs.
The workspace checker also checks cohort reservations and support-test implementation hashes.
It does not execute scientific searches, validate candidates, or check remote service availability.
It does not establish that every scientific statement is correct.

## Application component checks

Run each check from its component repository.

| Component | Command | Coverage |
|---|---|---|
| `database/` | `uv run -q --no-project --with jsonschema==4.25.1 python scripts/check_contracts.py` | Every contract schema, every valid and invalid example, and the method parameter defaults. |
| `workers/` | `.venv/bin/python -m pytest -q` | Exact T01 reproduction by `tess-bls`, and the index, search, and memory-limit flow on a temporary PostgreSQL server. |
| `backend/` | `uv run pytest` | Every endpoint on a temporary PostgreSQL server with the vendored migrations. The API rules against the shared vectors in `tests/vectors/`, and the SQL form of the target query against the same vectors. |
| `frontend/` | `npm test` | Sky geometry, the search parser, the fold, and the parameter checks. `src/parity.test.ts` checks the search, the fold, and the parameter checks against the copy of the backend vectors in `vendor/api-vectors/`. |

The component READMEs give the environment setup.
These checks do not validate scientific performance.

## Additional existing checks

Run the retained literature check from the workspace root:

```bash
python3 detection/scripts/validate_library.py
```

This check also inspects PDF structure, page counts, saved citation metadata, and the recorded discovery-count snapshot.

Run the original DECam record check with the external observation directory:

```bash
python3 experiments/scripts/check_records.py --data-dir raw/noirlab-image-archive --output /tmp/decam-record-check.json
```

Its scientific-record scope covers the original eight DECam experiments.
It checks saved recovery totals, implementation hashes, reference snapshots, and original observation checksums.
It does not rerun image processing or establish independent performance.

The [TESS record](experiments/tess-known-planet-recovery/README.md) supplies its own validation and reproduction commands.
The [Photutils record](experiments/decam-photutils-profile/README.md) supplies its original checks and reproduction command.
Use each historical record's own protocol when repeating it.

## Retained assets

The small synthetic array in `detection/examples/sample-output/` is a documented demonstration asset.
The retained papers and licensed upstream snapshots are intentional evidence.
Their presence does not indicate unfinished downloads or accidental duplication.
Closed experiment records follow their original protocols. They do not claim compliance with later procedure requirements.

## Testing support checks

The [support report](experiments/support-check.json) records regression results and implementation hashes.
Checks cover valid closure, negative outcomes, failed attempts, invalid records, cohort conflicts, concurrent reservations, deadlines, and interruption.
The [supervised TESS repeat](experiments/support/tess-repeat-validation.json) gives identical scientific arrays and numerical search results.

## Open work

| Item | Current limitation and next requirement |
|---|---|
| Application contract | Contract version 1 covers the TESS slice. DECam records need a later contract version. G03 review of the contract remains open. |
| Evaluation selection | The [shared register](experiments/COHORTS.md) holds only historical development exclusions. G02 requires new evaluation selections and reservations. |
| Scientific validation | The [common validator](experiments/RECORD-CONTRACT.md) implements the record contract. Experiment-specific calculations and scientific review remain required. |
| Historical TESS runner | Frozen code retains its internal timeout defect. The supported [external supervisor](experiments/SUPPORT.md) enforces the complete-run deadline. |
| TESS measurement validity | Guided period-and-phase recovery does not establish depth accuracy, completeness, or false-alarm rates. |
| Photutils reproduction | No full numerical repeat exists for this record. |
| Scientific adoption | Independent evaluation and uncertainty calibration remain prerequisites for broader adoption claims. |

The structural check can pass while these items remain open.

## Maintenance

1. Update the owning document when a fact or decision changes.
2. Update affected index links and dependent planning records.
3. Preserve historical evidence and its original hashes.
4. Run the structural checker.
5. Run applicable literature or scientific record checks when their inputs change.
6. Report the check scope and remaining limitations.

The writing check covers structural rules only.
This document does not claim complete ASD-STE100 dictionary conformity.
