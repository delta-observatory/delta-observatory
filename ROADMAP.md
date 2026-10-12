# Delta Observatory implementation roadmap

This document is the working implementation ledger.
[DESIGN.md](DESIGN.md) defines the desired system. This roadmap records delivery order, current work, decisions, and completion evidence.
Update this document as work progresses. Keep historical progress out of the design specification.

[README.md](README.md) describes current workspace structure and document responsibilities.
[experiments/PROCEDURE.md](experiments/PROCEDURE.md) controls scientific execution and evidence quality.
[experiments/PLAN.md](experiments/PLAN.md) defines scientific tasks, ownership, and dependencies.
[CHECKS.md](CHECKS.md) records workspace audit coverage and remaining limitations.

Last updated: 2026-10-11.

**Current position**

The target design and workspace organization are defined for review.
The dataset catalog and detection library provide the research foundation.
Application implementation has not started.
R0 is active. A bounded DECam experiment recovered one cataloged moving source across three observations.
An additional detector test produced seven possible pairs and no surviving candidate.
A masked injection pilot measured conditional recovery across five brightness levels and three motion rates.
Threshold comparison selected three times the local noise on N2. N3 evaluation stopped because calibration lacked enough matched stars.
A calibration audit reproduced the failure. One of ten otherwise eligible N3 pairs contains masked aperture pixels.
Legacy Surveys code resolves the V3.7 mask encoding. A diagnostic comparison retains code 7 and increases calibration coverage.
Both additional N2 candidates match known asteroids. The complete quality mask preserves candidate 11’s earlier detection.
Paired injections show slightly lower recovery under the retain-code-7 policy in common clean regions.
Recovery within code-7 regions and independent validation remain open.
The original eight DECam records are closed within scope. [Closure decisions](experiments/README.md#closure-decisions) define deferred questions and restart conditions.
The Photutils comparison is also closed. Its empirical configuration failed convergence and residual-improvement criteria, so the source model remains unchanged.
Broader calibration validation and scientific acceptance criteria remain open.
The bounded TESS experiment recovered both selected known planets with fixed Lightkurve and Astropy BLS settings.
Its complete numerical repeat passed. Detrending changed depths, so depth accuracy and discovery performance remain unvalidated.
Image and brightness-series evidence now provide concrete inputs for the scientific contract.

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
- [ ] Define validation data and prevent overlap with parameter-tuning data.
- [ ] Agree on an initial resource budget and baseline experiment.

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
| First dataset–method pair | Provisional | DECam images with SEP extraction, position association, and a third-observation prediction check. |
| Initial scientific focus | Agreed | Asteroids and exoplanets, with asteroid experiments first. Additional targets require datasets, methods, references, and validation criteria. |
| First exoplanet workflow | Bounded recovery complete | TESS SPOC brightness series with Lightkurve and Astropy BLS. Production integration and broader validation remain open. |
| Known-object references | Agreed | Dated local copies from official downloads or APIs, with experiment-specific provenance. See [policy](REFERENCE-CATALOGS.md). |
| Database hosting and storage | Open | Select the local deployment arrangement and persistent storage. |
| Scientific acceptance targets | Open | Dataset inspection and baseline measurements. |
| Decision provider and authority | Open | Evidence requirements and comparative evaluation. |

**Latest completed experiment**

[TESS known-planet recovery](experiments/tess-known-planet-recovery/README.md) recovered WASP-18 b and WASP-126 b in sector 2.
Period errors are 0.00718% and 0.00519%. Phase errors are 0.960 and 8.503 minutes.
Both targets passed all fixed recovery conditions, and a complete repeat produced identical numerical results.
Flattening changed transit depths, especially for WASP-126. The configuration remains provisional for scientific measurements.

**Immediate next actions**

Follow the scientific [plan](experiments/PLAN.md) and current [procedure](experiments/PROCEDURE.md) for each experiment successor.
G01 requires experiment-specific criteria and budgets, even though the common procedure now exists.
G02 must establish cohort reservations before dependent independent-performance evaluations.

1. Draft the scientific input and output contract from the recorded image and brightness-series examples for Richard's review.
2. Define separate transit-injection and negative-control protocols before claims about depth accuracy, completeness, or false alarms.
3. Keep the Gaussian source model provisional. A profile successor needs separate convergence work and new evaluation stars.
4. Include DS9 and TOPCAT/STILTS checks when further image-calibration work requires them.
5. Reopen mask or threshold evaluation only under the [documented restart conditions](experiments/README.md#closure-decisions).
6. Begin database design after agreement on the scientific contract.

The [common record validator](experiments/RECORD-CONTRACT.md) now checks new preflight and closure records.
The [cohort register](experiments/COHORTS.md) preserves historical development exclusions and supports serialized reservations.
The [external supervisor](experiments/SUPPORT.md) enforces the complete-run deadline around the unchanged historical TESS runner.
Use that supervisor for all TESS reproductions.
The supervised repeat preserved the original numerical results.
The workspace [checks](CHECKS.md) record these limits separately from structural consistency.

**TESS and Lightkurve: bounded recovery complete**

Status: the first [guided recovery experiment](experiments/tess-known-planet-recovery/README.md) is closed without retuning.
Two SPOC sector-2 light curves and a dated NASA reference subset support reproducible period and phase comparisons.
The dataset catalog now distinguishes processed target series from full-frame images.

The fixed preparation altered transit depths. A subsequent study needs injected transits before detrending and suitable negative examples.
It must separate tuning and evaluation observations and preserve upstream correction limits.
Pixel-centroid checks, physical transit fitting, and precision timing remain outside this completed experiment.
The asteroid and Photutils validation limits also remain open.

ExoMiner is a later candidate-assessment option, subject to compatible inputs and validation.
THOR and ADAM Precovery remain evaluation options for asteroid association and historical observations.
Neither option replaces the current evidence records or constitutes an installed integration.

**Progress ledger**

| Date | Work | Outcome and evidence | Next action |
|---|---|---|---|
| 2026-10-11 | Establish the target design and workspace organization. | [DESIGN.md](DESIGN.md) defines the system, separate components, automatic indexing, frontend requirements, and local k3s deployment. | Resolve the first investigation. |
| 2026-10-11 | Assemble scientific reference material. | [Dataset catalog](datasets/README.md) and [detection library](detection/README.md) provide inputs for method selection. | Review a dataset–method pair without treating catalog entries as downloaded observations. |
| 2026-10-11 | Agree on delivery sequence. | This roadmap records back-to-front construction with workers before the API and Kubernetes throughout. | Begin R0 with Richard. |
| 2026-10-11 | Test public DECam access and guided recovery. | Four calibrated exposures and one quality mask were downloaded with archive checksum checks. N1 yielded 12 possible pairs. One predicted a detection in another exposure within 1.41 pixels. It matched the reference tracklet. [Evidence](experiments/decam-moving-object-baseline/results/n1/third-exposure-check.json). | Test another detector before consulting its catalog. |
| 2026-10-11 | Complete the N2 detector test. | The unchanged baseline produced seven pairs and zero survivors. The subsequent catalog query returned zero records for N2. Runtime was 3.69 seconds. Peak memory was 489 MiB. [Report](experiments/decam-moving-object-baseline/README.md). | Validate calibration handling and recovery limits before application implementation. |
| 2026-10-11 | Preserve the baseline in experiments. | [Experiment record](experiments/decam-moving-object-baseline/README.md) includes original evidence, figures, input checksums, fixed settings, and portable scripts. Both detector results reproduced. | Record future scientific experiments separately from component software checks. |
| 2026-10-11 | Measure injection recovery on N2. | [Pilot record](experiments/decam-injection-recovery/README.md) preserves 300 trials, quality rules, and source-model assumptions. Recovery was 0/60, 22/60, 55/60, 60/60, and 60/60 across brightness levels. A second run reproduced the results. | Evaluate detection changes on new trajectories without replacing this pilot. |
| 2026-10-11 | Compare extraction thresholds on new N2 trajectories. | [Comparison record](experiments/decam-threshold-comparison/README.md) preserves all four settings. Threshold three recovered 106/180 trajectories, versus 73/180 at five. N3 evaluation failed calibration before any recovery measurement. | Inspect calibration coverage and define a new evaluation protocol. |
| 2026-10-11 | Define search scope and known-object references. | Asteroids and exoplanets are in scope. [Reference policy](REFERENCE-CATALOGS.md) requires dated copies, saved queries, and independent identity comparison. | Select reference inputs before the next experiment. |
| 2026-10-11 | Broaden the platform purpose. | Asteroids and exoplanets are the initial scientific focus, not permanent limits. Each experiment retains an explicit objective. | Continue the N3 calibration investigation. |
| 2026-10-11 | Audit N3 calibration selection. | [Audit record](experiments/decam-calibration-audit/README.md) reproduces N2 calibration and the N3 failure. N3 retains nine acceptable matches after aperture checks. | Investigate counterpart selection before revising calibration. |
| 2026-10-11 | Inspect missing N3 calibration counterparts. | [Counterpart audit](experiments/decam-counterpart-audit/README.md) finds masks at 15 of 17 missing exposure-4 positions. Five other matches fail the peak-brightness condition. | Establish the V3.7 mask encoding before changing policy. |
| 2026-10-11 | Select the next distinct scientific workflow. | TESS with Lightkurve will test brightness-series processing after the asteroid investigation. Established packages remain replaceable components. | Resolve the current mask question, then define the TESS experiment protocol. |
| 2026-10-11 | Reuse established mask handling and formalize software review. | [Mask comparison](experiments/decam-mask-policy-comparison/README.md) reuses a pinned Legacy Surveys mapper. N3 exposure-4 calibration matches increase from 9 to 68. [Reuse register](detection/TOOLING.md) records software and data-product gaps. | Assess new candidates and recovery before adopting the alternative mask policy. |
| 2026-10-11 | Review N2 candidates and measure paired mask recovery. | [Experiment record](experiments/decam-mask-recovery/README.md) gives candidate 11 an earlier match within 0.35 pixels. Clean-region recovery totals are 215/360 strict and 202/360 retaining code 7. | Obtain missing quality information and identify the supported candidate before broader mask evaluation. |
| 2026-10-11 | Complete N2 candidate quality and identity checks. | [Candidate identification](experiments/decam-candidate-identification/README.md) matches candidates 11 and 13 to 383733 and 192670. All six search positions agree within 0.374 arcseconds. The earlier quality mask preserves candidate 11. | Define representative mask evaluation and the bounded TESS protocol. |
| 2026-10-11 | Expand established-software coverage. | [Reuse register](detection/TOOLING.md) adds DS9, TOPCAT/STILTS, Astrometry.net, Find_Orb, batman, CASA, and blimpy/turboSETI. It defines immediate evaluations and requires evidence before duplicate scientific implementation. | Evaluate Photutils against the current source model, with image and catalog checks. |
| 2026-10-11 | Close the current DECam experiment series. | [Closure decisions](experiments/README.md#closure-decisions) preserve eight bounded outcomes and define restart conditions. Record checks verify saved inputs, execution hashes, and recovery totals. Generated caches were removed. | Define the bounded Photutils comparison. |
| 2026-10-11 | Evaluate Photutils on disjoint stellar samples. | [Profile comparison](experiments/decam-photutils-profile/README.md) records residual reductions of 7.2%, 52.5%, and 8.6%. All three profiles miss fixed convergence, so the empirical configuration is not adopted. | Define the bounded TESS protocol. Any profile successor needs separate convergence work and new evaluation stars. |
| 2026-10-11 | Execute the first TESS brightness-series experiment. | [Guided recovery](experiments/tess-known-planet-recovery/README.md) recovers both known planets and reproduces all numerical outputs. CFITSIO resolves the checksum-checking issue. Detrending changes depth, so measurement accuracy remains unvalidated. | Draft the scientific contract using both observation types. Define separate transit-injection and negative-control protocols. |
| 2026-10-11 | Establish the current scientific procedure. | [PROCEDURE.md](experiments/PROCEDURE.md) defines required design, execution, controls, reproduction, review, and closure. Agent instructions and the protocol template reference it. | Complete experiment-specific protocols and cohort reservations. |
| 2026-10-11 | Reconcile workspace guidance and structure. | [README.md](README.md) defines document responsibilities. [CHECKS.md](CHECKS.md) records integrity checks, preserved evidence, and unresolved scientific requirements. | Use the procedure and task register for the next authorized work. |
| 2026-10-11 | Initialize local repositories and complete testing support. | Nine local repositories preserve component boundaries. [Support tools](experiments/SUPPORT.md) provide cohort registration, record validation, and checked TESS supervision. | Commit when Richard requests it. Select new evaluation groups under completed protocols. |
| 2026-10-11 | Commit the populated repositories at Richard’s request. | Initial commits preserve the root, datasets, detection, and experiments. No remotes are configured. | Continue experiment-specific protocols and evaluation selection. |

**Ledger maintenance**

- Update stage status when work starts, pauses for a dependency, completes, or reopens.
- Attach completion evidence before marking a stage complete.
- Record the reason and consequence of a changed decision.
- Keep immediate next actions current.
- Update `DESIGN.md` when the desired system changes.
- Keep implementation progress and historical decisions in this roadmap.

