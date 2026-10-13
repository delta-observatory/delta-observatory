# Delta Observatory implementation roadmap

This roadmap defines delivery stages, their status, open decisions, and next actions.
[DESIGN.md](DESIGN.md) defines the desired system.
Git history records changes. Experiment records hold scientific results.

[README.md](README.md) describes workspace structure and document responsibilities.
[experiments/PROCEDURE.md](experiments/PROCEDURE.md) controls scientific execution and evidence quality.
[experiments/PLAN.md](experiments/PLAN.md) defines scientific tasks and dependencies.
[CHECKS.md](CHECKS.md) defines workspace checks and their limits.

**Current position**

- R0, the scientific contract, is active. No application code exists.
- Ten bounded experiments are closed. The [experiment index](experiments/README.md) lists their results and limits.
- The DECam series recovers known moving objects on development data. Threshold three is provisional. The default mask policy is unchanged.
- The Gaussian source model remains the baseline. The tested Photutils empirical-profile configuration failed its criteria.
- The TESS experiment recovers the periods and phases of two known planets. Depth accuracy, completeness, and false-alarm rates are not validated.
- No independent evaluation data exists. N1, N2, N3, the Photutils stars, and both TESS hosts are development data.

The build follows Richard's preferred sequence:

**Scientific contract → database → ingestion → scientific workers → API → frontend → decision assistance → expanded coverage.**

One complete investigation will connect these layers before the project expands into additional scientific workflows.
Kubernetes configuration develops alongside each runnable component.

**Status conventions**

| Status | Meaning |
|---|---|
| Pending | Work has not started. |
| Active | Work is underway. |
| Waiting | A named decision or dependency prevents further work. |
| Complete | The completion criteria have supporting evidence. |

Completion requires a reference to code, a reviewed specification, an experiment, or another inspectable result.
A completed stage can reopen when changed requirements invalidate its evidence.

**Delivery sequence**

| ID | Stage | Status | Depends on | Main location |
|---|---|---|---|---|
| R0 | First investigation and scientific contract | Active | Dataset and method review with Richard | `datasets/`, `detection/`, `experiments/` |
| R1 | Database | Pending | R0 | `database/` |
| R2 | Storage and ingestion | Pending | R1 | `workers/`, `database/`, `kubernetes/` |
| R3 | Scientific workers | Pending | R2 | `workers/` |
| R4 | Application API | Pending | R3 | `backend/` |
| R5 | Interactive frontend | Pending | R4 for implementation | `frontend/` |
| R6 | Decision assistance | Pending | R3 and R4, plus evaluation evidence | `workers/`, `backend/` |
| R7 | Expanded scientific coverage | Pending | A validated complete investigation | Relevant component repositories |

The sequence defines delivery priorities, not a requirement to postpone all interface discussion.
Job and result contracts begin before the API implementation.
Frontend design discussions can begin when real observations and diagnostics are available.

**R0 — First investigation and scientific contract**

Choose one dataset–method pair with Richard.
Use the existing catalogs and cited method descriptions as the starting material.
Confirm the location and availability of the actual observation files separately from their catalog entries.
The checkboxes below describe application-contract work.
Completed feasibility experiments provide evidence without completing that contract.

Tasks:

- [ ] Select the target population and scientific objective.
- [ ] Select a bounded observation collection and confirm its local availability.
- [ ] Select the detection method and candidate scientific libraries.
- [ ] Define required images, masks, uncertainty arrays, metadata, and calibration products.
- [ ] Define coordinate frames, time scales, units, and uncertainty conventions.
- [ ] Describe representative measurements, diagnostics, candidate evidence, and artifact formats.

Validation data, resource budgets, and baseline experiments belong to the [scientific plan](experiments/PLAN.md).
G01 defines budgets and baselines. G02 separates tuning data from evaluation data.
These tasks govern scientific acceptance. They do not block R1.

Completion: a reviewed contract describes the path from observations to candidate evidence.
Representative input and output records provide concrete examples for database design.
Numerical acceptance targets follow dataset inspection and baseline measurements where necessary.

**R1 — Database**

Design the records required by the first complete investigation.
Use the desired system's record model without creating speculative tables for every method in the research library.

Tasks:

- [ ] Define datasets, observations, campaigns, runs, jobs, measurements, candidates, artifacts, and decisions as required.
- [ ] Establish identifiers, relationships, constraints, and record ownership.
- [ ] Define source versions, duplicate exposure handling, and immutable run configurations.
- [ ] Define units, uncertainties, quality flags, and missing-value semantics.
- [ ] Define job states, claims, retries, and duplicate prevention.
- [ ] Establish migrations and database compatibility expectations.
- [ ] Publish the first job, result, method-parameter, and record schemas in [database/contracts/](database/contracts/README.md).
- [ ] Add the G03 example records as valid and invalid schema examples.
- [ ] Exercise the schema with representative scientific records.

Completion: representative observations and method outputs fit the schema without losing scientific meaning.
Constraint and migration checks demonstrate the required integrity behavior.
Database hosting and persistent storage requirements are recorded in `kubernetes/`.

**R2 — Storage and ingestion**

Make existing local observations available through automatic indexing and validation.
The user does not manually register each dataset.

Tasks:

- [ ] Configure dataset locations and storage access for workers.
- [ ] Map the selected dataset's metadata into the agreed observation records.
- [ ] Index files without unnecessary copies or source modification.
- [ ] Record checksums, source identifiers, processing versions, and supporting-product relationships.
- [ ] Validate dimensions, timing, coordinates, units, and method prerequisites.
- [ ] Report missing, changed, incomplete, or incompatible inputs.
- [ ] Implement repeatable refreshes and recovery after interruption.
- [ ] Produce the image previews needed for early exploration and frontend design discussions.

Completion: a real observation collection becomes queryable and usable by the selected scientific method.
Repeated indexing preserves identity and does not duplicate unchanged observations.
The k3s ingestion workload can access persistent source data and output storage.

**R3 — Scientific workers**

Implement the selected method before designing the full application API around its outputs.
Record the scientific calculations and intermediate products that the interface must expose.

Tasks:

- [ ] Implement required preparation and calibration checks.
- [ ] Implement the selected detection and measurement method.
- [ ] Expose parameters, equations, assumptions, and applicability limits.
- [ ] Persist measurements, uncertainty, diagnostics, and artifact references.
- [ ] Implement known-object comparison independently of blind detection.
- [ ] Execute validation with known objects, inserted signals, and suitable negative examples.
- [ ] Measure recovery, false detections, runtime, memory, and storage use.
- [ ] Verify interruption, retry, and duplicate prevention behavior.
- [ ] Record worker and scientific-library versions for every run.

Completion: a recorded job produces reproducible candidate evidence from real observations.
Validation results identify the method's usable conditions and limitations.
Worker manifests request appropriate k3s resources and preserve outputs across workload replacement.

**R4 — Application API**

Expose the complete investigation through the separate backend repository.
Use the scientific outputs established by workers to define useful result and diagnostic interfaces.

Tasks:

- [ ] Expose dataset inventory, observations, quality findings, and artifact access.
- [ ] Expose supported methods, parameter definitions, and compatibility requirements.
- [ ] Support campaign configuration and analysis submission.
- [ ] Expose progress, cancellation, retry, failures, and resource use.
- [ ] Expose measurements, candidates, provenance, and comparisons between runs.
- [ ] Provide reproducible evidence exports.
- [ ] Verify API, job, result, and database contract compatibility.
- [ ] Define access controls for the intended local deployment.

Completion: a programmatic client can conduct the complete investigation through the API.
The API and workers remain independently built and deployed.
Backend manifests provide local connectivity and configured access to storage and PostgreSQL.

**R5 — Interactive frontend**

Build a polished, information-dense, performant interface around working scientific capabilities.
Richard directs the visual style and interaction design before frontend code is written.
Each design step requires his review and direction before implementation.

Tasks:

- [ ] Review visual references, layout options, and interaction paradigms with Richard.
- [ ] Use real observations and diagnostics in design discussions.
- [ ] Agree on measurable loading, interaction, animation, and memory targets.
- [ ] Implement dataset exploration and observation inspection.
- [ ] Implement method selection, parameter controls, and execution status.
- [ ] Implement exposure animation, time controls, and measured motion overlays.
- [ ] Implement candidate evidence, scientific diagnostics, and run comparisons.
- [ ] Distinguish observations from predictions and preserve visible uncertainty.
- [ ] Verify performance with representative collections and review hardware.

Completion: Richard can investigate observations visually and inspect the scientific evidence.
The interface meets the agreed design and performance criteria.
Frontend manifests provide access through the local k3s environment.

**R6 — Decision assistance**

Evaluate decision models against recorded scientific investigations before granting automatic execution authority.
The scientific workflow remains usable with the decision service disabled.

Tasks:

- [ ] Select concrete judgments that could improve candidate assessment or subsequent analysis.
- [ ] Select a provider compatible with the required evidence.
- [ ] Define questions, permitted actions, evaluation labels, and comparison baselines.
- [ ] Record advisory recommendations without changing execution.
- [ ] Measure errors, cost, and benefits against rules and relevant conventional models.
- [ ] Agree on thresholds, fallback behavior, and automatic authority with Richard.
- [ ] Enable only validated actions within campaign resource limits.

Completion: evidence establishes which decisions improve outcomes and under what conditions.
Provider failures and uncertain responses produce the defined fallback behavior.

**R7 — Expanded scientific coverage**

Add datasets and methods through the existing contracts.
The initial scientific focus covers asteroids and exoplanets, with asteroid experiments first.
TESS with Lightkurve is the first exoplanet workflow for application integration.
Use the bounded recovery record to define its contract while preserving the unresolved scientific validation requirements.

Tasks:

- [ ] Select the next dataset or method for a specific scientific objective.
- [ ] Identify required contract changes and migration effects.
- [ ] Validate calibration compatibility before combining datasets.
- [ ] Add observation association or orbit fitting where sufficient evidence exists.
- [ ] Implement the agreed exoplanet capabilities with separate scientific validation.
- [ ] Expand worker concurrency when measured workloads justify it.
- [ ] Evaluate sustained campaigns against resource and scientific quality targets.

Completion applies separately to each addition.
Each capability has reproducible results, documented limitations, and compatible component releases.

**Kubernetes work throughout delivery**

Kubernetes is the operating environment throughout implementation.
Manifests live in `kubernetes/` and develop alongside runnable components.
Each component must demonstrate connectivity, persistent data access, restart behavior, and appropriate resource assignments.
Deployment configuration selects compatible component versions explicitly.

Local review uses a LAN URL.
Development servers bind to `0.0.0.0` when required for review.
External deployment requires Richard's explicit request.

**Decisions and dependencies**

| Item | State | Required decision or evidence |
|---|---|---|
| Back-to-front delivery | Agreed | Database, ingestion, scientific workers, API, then frontend. |
| Separate component repositories | Agreed | Independently versioned components within the umbrella workspace. |
| Automatic dataset indexing | Agreed | Existing local collections appear without manual registration. |
| Local k3s deployment | Agreed | Manifests remain in `kubernetes/`. |
| Frontend design authority | Agreed | Richard directs each design step before implementation. |
| Cross-component contracts | Agreed | Versioned schemas in `database/contracts/`. The stateless API and the workers connect only through PostgreSQL, file storage references, and these schemas. |
| Record contract source | Agreed | G03 uses closed experiment records. It does not wait for G01 successor protocols. |
| First dataset–method pair | Provisional | DECam images with SEP extraction, position association, and a third-observation prediction check. |
| Initial scientific focus | Agreed | Asteroids and exoplanets, with asteroid experiments first. Additional targets require datasets, methods, references, and validation criteria. |
| First exoplanet workflow | Bounded recovery complete | TESS SPOC brightness series with Lightkurve and Astropy BLS. Production integration and broader validation remain open. |
| Known-object references | Agreed | Dated local copies from official downloads or APIs, with experiment-specific provenance. See [policy](REFERENCE-CATALOGS.md). |
| Local observation storage | Agreed | `raw/<dataset-id>/` at the workspace root. Names match `datasets/`. Git does not track it. |
| Database hosting and storage | Open | Select the local deployment arrangement and persistent storage. |
| Scientific acceptance targets | Open | Dataset inspection and baseline measurements. |
| Decision provider and authority | Open | Evidence requirements and comparative evaluation. |

**Immediate next actions**

Follow the scientific [plan](experiments/PLAN.md) and the [procedure](experiments/PROCEDURE.md) for each successor experiment.

1. Draft the G03 scientific input and output contract from the DECam and TESS records for Richard's review.
2. Define G01 criteria and budgets for each successor protocol.
3. Reserve G02 evaluation cohorts before any independent-performance evaluation.
4. Define separate transit-injection and negative-control protocols (T02, T03) before claims about depth accuracy, completeness, or false alarms.
5. Keep the Gaussian source model provisional. A profile successor (A08) needs separate convergence work and new evaluation stars.
6. Include DS9 and TOPCAT/STILTS checks when image-calibration work requires them.
7. Reopen mask or threshold evaluation only under the [documented restart conditions](experiments/README.md#closure-decisions).
8. Begin database design (R1) after agreement on the scientific contract.

Use the [external supervisor](experiments/SUPPORT.md) for all TESS reproductions.

ExoMiner is a candidate-assessment option, subject to compatible inputs and validation.
THOR and ADAM Precovery are evaluation options for asteroid association and historical observations.
None of these is installed or integrated.

**Maintenance**

- Update stage status when work starts, pauses for a dependency, completes, or reopens.
- Attach completion evidence before marking a stage complete.
- Record a changed decision in the decisions table with its consequence.
- Keep the current position and next actions current. Remove completed actions.
- Do not add a dated progress log. Git history records changes.
- Update `DESIGN.md` when the desired system changes.
