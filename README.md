# Delta Observatory workspace

Delta Observatory investigates astronomical observations, measurements, and candidate objects or events.
The initial scientific focus covers asteroids and exoplanets.

The workspace currently contains research, dataset documentation, and scientific experiment evidence.
R0, the scientific contract stage, remains active.
The TESS vertical slice runs on the local k3s cluster: database, worker, API, and frontend.
The frontend at `http://10.0.0.47:30871/` shows the sky sphere with the development targets, search, target selection, the result plots, and the measurements.
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
| [ROADMAP.md](ROADMAP.md) | Delivery status, open decisions, and next actions. |
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
| [database/](database/README.md) | Schema, migrations, and the cross-component contracts in [database/contracts/](database/contracts/README.md). |
| [workers/](workers/README.md) | Worker with the `tess-spoc-index` and `tess-bls` methods. |
| [backend/](backend/README.md) | Stateless application API. |
| [frontend/](frontend/README.md) | Interactive application in React, Three.js, TypeScript, and Vite. [DESIGN-DECISIONS.md](frontend/DESIGN-DECISIONS.md) records the agreed design. |
| [kubernetes/](kubernetes/README.md) | k3s manifests, image builds, and migrations. |
| [agents/](agents/README.md) | Tooling for research agents that use the API. No agent code exists. |
| `scripts/` | Workspace documentation and structure checks. |
| `raw/` | Local downloaded observations in `raw/<dataset-id>/`. Git does not track this directory. |

The workspace contains ten independent Git repositories on `main`: the root and the nine component directories.
The root excludes all component directories.
No remote addresses are configured.
[VERSION-CONTROL.md](VERSION-CONTROL.md) defines repository boundaries, exclusions, and verification commands.

Store downloaded observations in `raw/<dataset-id>/` at the workspace root.
Each directory name must exactly match a dataset directory in [datasets/](datasets/README.md).
Keep execution attempts outside documentation directories.
Retained papers, small scientific results, and documented synthetic examples are intentional assets.
Licensed upstream snapshots and repeated experiment code preserve historical reproducibility.
Do not remove those snapshots as ordinary duplication.

## Current scientific evidence

The [experiment index](experiments/README.md) records 10 completed bounded investigations. All are closed.
The eight DECam investigations have a shared record checker.
The Photutils comparison rejected its fixed empirical configuration.
The TESS investigation recovered both selected known planets' periods and transit phases.
It does not validate transit depth, completeness, false-alarm rates, or planet confirmation.

Scientific calibration, independent evaluation, and the application contract remain incomplete.
[Experiment support](experiments/SUPPORT.md) provides shared validation, cohort registration, and complete-run deadlines.
G01 and G02 require experiment-specific protocols and new independent evaluation selections.
G03 uses the closed image and brightness-series records to propose the application contract.
The roadmap controls application delivery after that contract.

## Workspace checks

Run the structural check from the workspace root:

```bash
python3 scripts/check_workspace.py
```

Read [CHECKS.md](CHECKS.md) for additional checks and their exact scope.
