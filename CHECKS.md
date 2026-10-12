# Workspace checks and consistency

The workspace contains research and bounded scientific experiments.
Application implementation remains pending.
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
- Available Git status at the workspace and component boundaries.
- `raw/` directory names against dataset IDs. The checker does not read files inside `raw/`.

This is a workspace integrity checker.
The separate [common validator](experiments/RECORD-CONTRACT.md) checks new experiment records with their original inputs.
The workspace checker also checks cohort reservations and support-test implementation hashes.
It does not execute scientific searches, validate candidates, or check remote service availability.
It does not establish that every scientific statement is correct.

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

## Documentation consistency review

The current review aligns these responsibilities:

- The design describes the intended system.
- The roadmap describes current progress and unresolved application decisions.
- The procedure defines required experiment execution and evidence.
- The scientific plan defines task scope, dependencies, and protected ownership.
- The template uses the procedure's separate status and decision fields.
- The detection execution guide supplies scientific examples without requiring every example stage in every bounded experiment.
- Historical reviews describe their original review state.
- Historical closure follows original protocols without claiming compliance with later requirements.

The design tree now includes experiments and workspace guidance.
The experiment index distinguishes completed TESS recovery from pending broader transit validation.
The plan shows conditional dependencies that also appear in its task register.
Root and experiment agent instructions direct future agents to the current procedure.

## Current verification evidence

Review date: 2026-10-12 UTC, corresponding to 2026-10-11 in Chicago.
The current [machine-readable report](workspace-check.json) records structural results, counts, checker identity, and available Git status.
This report is a maintained workspace snapshot, rather than immutable scientific experiment evidence.

- The dataset catalog has 115 entries with matching directories and metadata identities.
- The scientific task register has 18 tasks without prerequisite cycles, including conditional edges.
- The experiment index contains ten registered bounded investigations.
- The literature check accepts 65 retained PDFs and 67 source records.
- Two unavailable source files retain explicit retrieval reasons.
- The original DECam checker passes for eight experiments and eight unique observation files.
- Its saved totals cover 1740 recovery assessments and 87 recovery cells.
- All 382 experiment and dated-review evidence files retain their pre-review hashes.
- No generated Python caches, unfinished downloads, or raw observation files remain inside experiment records.
- Temporary-copy probes correctly reject broken links, conflicting conditional dependencies, changed frozen settings, and non-standard JSON constants.

The small synthetic array in `detection/examples/sample-output/` is a documented demonstration asset.
The retained papers and licensed upstream snapshots are intentional evidence.
Their presence does not indicate unfinished downloads or accidental duplication.

The root and eight component directories now contain separate local Git repositories on `main`.
Richard authorized initial commits for the root, datasets, detection, and experiments repositories.
All nine repositories have initial commits.
The database repository contains contract documentation only.
The four other application repositories contain exclusion rules only.
No remotes are configured.
The saved audit report captures Git status at the time of its generation.
Run the checker again to inspect current Git status.
[VERSION-CONTROL.md](VERSION-CONTROL.md) records the boundaries and exclusion policy.

## Testing support verification

The [support report](experiments/support-check.json) records regression results and implementation hashes.
Checks cover valid closure, negative outcomes, failed attempts, invalid records, cohort conflicts, concurrent reservations, deadlines, and interruption.
The supervised TESS repeat completed with identical scientific arrays and numerical search results.
Its original validator passed integrity, reproduction, and independent arithmetic checks.
The historical runner and all protected evidence remain unchanged.

## Open work that remains explicit

| Item | Current limitation and next requirement |
|---|---|
| Application contract | R0 remains active. G03 must describe supported scientific records before application implementation. |
| Evaluation selection | The [shared register](experiments/COHORTS.md) exists with historical development exclusions. G02 still requires new evaluation selections and reservations. |
| Scientific validation | The [common validator](experiments/RECORD-CONTRACT.md) implements the new record contract. Experiment-specific calculations and scientific review remain required. |
| Historical TESS runner | Frozen code retains its internal timeout defect. The supported [external supervisor](experiments/SUPPORT.md) enforces the complete-run deadline. |
| TESS measurement validity | Guided period-and-phase recovery does not establish depth accuracy, completeness, or false-alarm rates. |
| Photutils reproduction | The retained validation explicitly records that a full numerical repeat was not performed. |
| Scientific adoption | Independent evaluation and uncertainty calibration remain prerequisites for broader adoption claims. |

These items remain unresolved work.
The structural check can pass while these scientific and implementation requirements remain open.

## Maintenance

1. Update the owning document when a fact or decision changes.
2. Update affected index links and dependent planning records.
3. Preserve historical evidence and its original hashes.
4. Run the structural checker.
5. Run applicable literature or scientific record checks when their inputs change.
6. Report the check scope and remaining limitations.

The writing check covers structural rules only.
This review does not claim complete ASD-STE100 dictionary conformity.
