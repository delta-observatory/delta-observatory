# Delta Observatory workspace

Delta Observatory investigates astronomical observations, measurements, and candidate objects or events.
The initial scientific focus covers asteroids and exoplanets.

The workspace currently contains research, dataset documentation, and scientific experiment evidence.
R0, the scientific contract stage, remains active.
Application implementation has not started.
The application and deployment repositories contain exclusion rules only.
Catalog inclusion does not establish local observation availability or an implemented detection method.

## Start here

1. Read [ROADMAP.md](ROADMAP.md) for current evidence, delivery status, and next actions.
2. Read [DESIGN.md](DESIGN.md) for the intended system and component boundaries.
3. Read [experiments/PROCEDURE.md](experiments/PROCEDURE.md) before scientific planning, execution, review, or reproduction.
4. Read [experiments/PLAN.md](experiments/PLAN.md) for scientific task dependencies and ownership.

## Document responsibilities

| Document | Authority and purpose |
|---|---|
| [DESIGN.md](DESIGN.md) | Intended application behavior, architecture, and requirements. It does not authorize implementation or deployment. |
| [ROADMAP.md](ROADMAP.md) | Current delivery status, project decisions, progress history, and next actions. |
| [experiments/PROCEDURE.md](experiments/PROCEDURE.md) | Current required scientific procedure, evidence requirements, and stop conditions. |
| [experiments/PLAN.md](experiments/PLAN.md) | Scientific task scope, dependencies, conditional work, and protected ownership. |
| [Protocol template](experiments/planning/experiment-template.md) | Fields for each new experiment's specific design and criteria. |
| [REFERENCE-CATALOGS.md](REFERENCE-CATALOGS.md) | Reference acquisition, identity comparison, and catalog-influence rules. |
| [detection/TOOLING.md](detection/TOOLING.md) | Scientific software reuse, evaluated choices, adoption limits, and product gaps. |
| [CHECKS.md](CHECKS.md) | Workspace audit coverage, current limitations, and repeatable checks. |

An experiment's frozen protocol governs reproduction of its historical result.
Current procedures govern new work without rewriting historical evidence.
Method explanations describe scientific options rather than adopted application defaults.
Planning status, execution status, scientific outcome, and method adoption are separate records.
Resolve a documentation conflict before executing affected work.

## Workspace structure

| Location | Current contents or intended responsibility |
|---|---|
| [datasets/](datasets/README.md) | Catalog, product descriptions, metadata, acquisition instructions, and recorded acquisition evidence. |
| [detection/](detection/README.md) | Method explanations, academic references, retained papers, software guidance, and synthetic demonstrations. |
| [experiments/](experiments/README.md) | Scientific procedure, task planning, bounded experiments, evidence, and reviews. |
| `database/` | Placeholder for schema, migrations, and record constraints. |
| `workers/` | Placeholder for ingestion and scientific processing. |
| `backend/` | Placeholder for the application API and coordination. |
| `frontend/` | Placeholder for the interactive application. |
| `kubernetes/` | Placeholder for local deployment manifests and environment configuration. |
| `scripts/` | Workspace documentation and structure checks. |
| `raw/` | Local downloaded observations in `raw/<dataset-id>/`. Git does not track this directory. |

The agreed architecture uses separate component repositories within this umbrella workspace.
The root coordination repository and all eight component repositories are initialized locally on `main`.
Each repository has independent Git metadata.
The root excludes all component directories.
Initial commits cover the root, datasets, detection, and experiments repositories.
The five application repositories contain exclusion rules only and remain without commits.
No remote addresses are configured.
[VERSION-CONTROL.md](VERSION-CONTROL.md) defines repository boundaries, exclusions, and verification commands.

Store downloaded observations in `raw/<dataset-id>/` at the workspace root.
Each directory name must exactly match a dataset directory in [datasets/](datasets/README.md).
Keep execution attempts outside documentation directories.
Retained papers, small scientific results, and documented synthetic examples are intentional assets.
Licensed upstream snapshots and repeated experiment code preserve historical reproducibility.
Do not remove those snapshots as ordinary duplication.

## Current scientific evidence

The [experiment index](experiments/README.md) records 10 completed bounded investigations.
The original eight DECam investigations have a shared record checker.
The Photutils comparison rejected its fixed empirical configuration.
The TESS investigation recovered both selected known planets' periods and transit phases.
It does not validate transit depth, completeness, false-alarm rates, or planet confirmation.

Scientific calibration, independent evaluation, and the application contract remain incomplete.
Shared validation, cohort registration, and complete-run deadlines are available through [experiment support](experiments/SUPPORT.md).
G01 and G02 still require experiment-specific protocols and new independent evaluation selections.
G03 will use the completed image and brightness-series evidence to propose the application contract.
The roadmap controls application delivery after that contract.

## Workspace checks

Run the structural check from the workspace root:

```bash
python3 scripts/check_workspace.py
```

Read [CHECKS.md](CHECKS.md) for additional checks and their exact scope.
