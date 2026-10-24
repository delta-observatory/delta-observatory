# Delta Observatory product plan

## Status and product outcome

This document defines the proposed downloadable Delta application.
It defines product scope, reuse decisions, delivery dependencies, and acceptance criteria.
[DESIGN.md](DESIGN.md) and [ROADMAP.md](ROADMAP.md) retain authority for agreed requirements and implementation status.
P0 has a separate local [desktop prototype](release/README.md) and [dependency audit](release/P0.md).
The later stages remain proposals.
The plan does not authorize scientific experiments, public binary releases, or external deployment.

Delta should let a person direct an astronomical investigation from one application.
The person can select observations, connect an agent, change the plan, inspect measurements, and export reproducible evidence.
Every supported operation must have a GUI control.
The complete investigation must also work without an agent.

The first audience is serious astronomy enthusiasts, advanced students, and small research groups.
The first complete workflow uses TESS SPOC 120-second light curves.
A light curve records an object's brightness over time.
The product promises an inspectable investigation, with explicit limits on its conclusions.
It cannot promise a planet discovery.

## Existing foundation and missing product work

Delta already has PostgreSQL records, scientific workers, a stateless HTTP API, a React frontend, and an agent adapter.
The deployed slice supports observation selection, BLS searches, cancellation, retry, run comparison, candidate review, research records, and evidence export.
BLS means Box Least Squares, a search for repeated brightness decreases.
The adapter uses MCP, the Model Context Protocol, to expose API operations to external agents.

The prototype supplies bundled services and a minimal public TESS catalog.
Remaining product work includes a qualified installer, complete public resources, automatic acquisition, managed agent sessions, editable investigation plans, and complete GUI coverage.
Scientific validation remains separate from these engineering tasks.
The two-host TESS experiment establishes bounded period-and-phase recovery.
It does not establish depth accuracy, completeness, or false-alarm rates.
The mirror pilot does not authorize method adoption.

## Reuse decisions

| Area | Recommendation | Delta responsibility |
|---|---|---|
| Scientific calculation | Retain Astropy and Lightkurve behind the existing workers. Use established FITS readers and archive clients. | Define applicable inputs, pinned versions, preparation rules, diagnostics, and validation evidence. |
| Archive access | Use MAST services and supported clients, such as Astroquery, for metadata queries and product retrieval. | Delta bounds selections and downloads. It preserves source identity and checks acquired products. |
| Application foundation | Retain PostgreSQL, FastAPI, React, and the existing job contracts. | Extend the complete investigation without creating a second execution system. |
| Desktop distribution | Evaluate Electron and Electron Forge as a thin shell around the existing frontend. | Manage local services, installation, updates, storage, recovery, and operating-system integration. |
| Agent execution | Use Codex app-server for the first managed agent adapter. Retain API-key access as an alternative. | Delta translates agent events into investigation records. It enforces Delta permissions. |
| Additional providers | Add an Anthropic API adapter after the first complete workflow. | Preserve the same operations, controls, records, and failure behavior across providers. |
| Credentials | Use operating-system credential storage through a maintained library. | Keep credentials outside exports, model context, logs, and application records. |
| Visualization | Retain the existing plots and observation views. Evaluate Jdaviz ideas for scientific inspection. | Connect every plot to its source, preparation, run, and uncertainty. |

Astropy documents its [BLS implementation](https://docs.astropy.org/en/stable/timeseries/bls.html).
Lightkurve documents its [light-curve tools](https://lightkurve.github.io/lightkurve/).
Astroquery documents its [MAST client](https://astroquery.readthedocs.io/en/latest/mast/mast.html).
These libraries supply calculations and access methods, but Delta must establish their supported scientific use.

Electron documents [distribution](https://www.electronjs.org/docs/latest/tutorial/distribution-overview) and [security requirements](https://www.electronjs.org/docs/latest/tutorial/security).
Its selection remains subject to an installation and resource-use test.
The proposal keeps the existing frontend and avoids a separate desktop interface implementation.

### Product patterns to reuse

| Established system | Pattern for Delta | Adoption boundary |
|---|---|---|
| [Galaxy Orbit and Loom](https://galaxyproject.github.io/loom/) | A visible plan, live execution, and a durable research notebook. | Use the interaction pattern. Keep Delta's API and scientific records authoritative. |
| [Galaxy](https://galaxyproject.org/) | Inspectable analysis histories and repeatable workflows. | Keep a history of parameters, inputs, failures, and outputs for each investigation. |
| [Nextflow](https://docs.seqera.io/nextflow/cache-and-resume) | Resume completed work when its inputs and outputs remain valid. | Extend Delta's existing jobs. Do not introduce another scheduler without a demonstrated need. |
| [Jdaviz](https://jdaviz.readthedocs.io/en/latest/) | Direct inspection of astronomical data through interactive tools. | Keep evidence inspection available independently of agent conversation. |
| [Edison](https://edisonscientific.com/) | User steering and branches for competing hypotheses. | Treat this as a product pattern. Vendor descriptions do not establish scientific effectiveness. |

Delta should initially reuse these patterns instead of adopting a complete research framework.
Importing Galaxy, Denario, or another agent framework would also introduce its execution model, dependencies, and maintenance obligations.
A framework evaluation becomes useful when a specific Delta requirement exceeds the existing architecture.
Multiple agents are a later capability, after one agent completes a reliable investigation.

### Supported model access

The first adapter should use the documented [Codex app-server integration](https://developers.openai.com/siwc/token-sharing-open-source/codex-app-server).
[Sign in with ChatGPT](https://developers.openai.com/siwc/quickstart) supports eligible plan use in participating open-source applications.
Identity access and model-use consent are separate.
Delta must check current eligibility and support API-key access when appropriate.
The desktop proposal does not assume permission for a hosted commercial service.

Anthropic documents API access through its [Agent SDK](https://code.claude.com/docs/en/agent-sdk/overview).
Embedded third-party use of Claude subscription login requires prior Anthropic approval.
The initial product should offer Claude API-key access without promising Claude subscription login.
An external agent connection through MCP remains distinct from a managed agent session inside Delta.

## What Delta must build

| Capability | Required behavior | Owning component |
|---|---|---|
| Investigation plans | Save the question, permitted scope, plan revisions, approvals, branches, and links to results. | `database/`, `backend/`, `frontend/` |
| Steering controls | Apply parameter changes, priorities, exclusions, pauses, and scope changes at explicit execution boundaries. | `backend/`, `agents/`, `frontend/` |
| Acquisition manager | The manager previews selections and storage estimates. It downloads approved products, checks files, and recovers after interruption. | `workers/`, `backend/`, `frontend/` |
| Agent host | The host manages provider sessions, events, interruptions, and saved decisions. | `agents/` |
| Evidence assembly | Connect each claim to measurements, diagnostics, inputs, method versions, limitations, and human decisions. | `workers/`, `backend/`, `frontend/` |
| Desktop lifecycle | The desktop component manages pinned services, processes, credentials, record migration, and backup restoration. | P0 prototype in `release/`. Backup restoration remains pending. |
| Public runtime resources | Supply the supported method list, archive recipes, example manifests, and installation checks without private repository access. | Relevant public component repositories |

“Investigation” is the GUI term for the existing campaign concept.
It must not create a competing campaign database or execution history.
Plan revisions and provider events need versioned contracts before implementation.
All job, result, parameter, and record shapes belong in `database/contracts/`.
The table defines responsibilities, not schemas.

The API stays stateless and does not call workers or models.
Workers exchange records and file references through PostgreSQL and shared storage.
The agent host calls the same API as the GUI.
The adapter translates calls without granting permissions or defining scientific policy.

Managed agents receive only approved API tools and permitted evidence.
They cannot bypass API restrictions through direct database access, unrestricted files, or shell commands.
The connection screen explains which evidence the selected provider receives.
Numerical workers produce measurements. Agents propose actions and explain recorded evidence.

## First complete user experience

### 1. Install and check the application

The installer provides the frontend and compatible local API, worker, and PostgreSQL runtimes.
The user selects a workspace and storage limit through the GUI.
Delta checks free space, available memory, service health, and runtime compatibility.
The user does not install Python, PostgreSQL, Docker, or Kubernetes manually.
Model access is optional until the user starts an agent.

The first packaging test targets one explicitly supported Linux environment.
macOS and Windows need separate installation, credential, update, and recovery checks before support claims.
The existing k3s deployment remains the development environment.
Desktop distribution requires an explicit architecture decision before implementation.

### 2. Complete a guided investigation

The opening screen offers a small known-signal investigation and a new TESS investigation.
The guided investigation uses a declared development target and a small archive download.
It explains the question, light curve, search parameters, diagnostic plots, and limits of the result.
It labels known-object recovery as a demonstration.
It does not present that demonstration as independent performance evidence.

### 3. Define the question and approve the plan

The user selects a target or a small observation collection through archive filters.
Delta shows available products, unavailable products, expected storage, compatible methods, and estimated computing requirements.
The user connects one agent or selects manual operation.
The agent proposes a question, operations, parameters, stopping conditions, and expected evidence.
The user can edit these items before approval.

Approval covers exact permitted operations and resource limits.
The application can execute those approved operations without repeated prompts.
An agent proposal that changes scope, permissions, or scientific settings needs a visible plan revision.
R6 evaluation and agreement remain prerequisites for automatic scientific decision authority.

### 4. Acquire and analyze observations

The user approves an acquisition manifest and its byte limit.
A manifest identifies the selected products and their source records.
The acquisition worker downloads only those products and records checksums, versions, exclusions, and failures.
The agent can request more data, but cannot grant itself acquisition permission.

Delta checks compatibility before running the approved preparation and BLS search.
The investigation shows downloaded, usable, searched, excluded, failed, and unresolved observation counts.
Each count links to its records and reasons.
An unsuccessful search does not establish that a planet is absent.

### 5. Inspect evidence and change direction

The investigation screen keeps three areas visible: the plan, the selected evidence, and the agent controls.
The user can inspect the raw and prepared light curves, periodogram, phase-folded curve, quality findings, and source records.
A phase-folded curve aligns measurements by the proposed period.
Each interpretation links to the measurements that support it.

| Control | Required effect |
|---|---|
| Change parameters | Create a new run. Preserve the previous configuration and outputs. |
| Compare preparation | Create a branch with explicit changed settings and comparable diagnostics. |
| Exclude observations | Save the reason. Preserve the original selection and counts. |
| Request another sector | Draft a bounded acquisition request for user approval. |
| Pause | Stop new submissions. Show whether active work continues. |
| Stop active work | Cancel the current attempt. Preserve completed results. |
| Change the budget | Show the effective limit and its effect on queued work. |
| Give an instruction | Convert the instruction into a visible proposed plan change. |

The GUI shows whether a change applies immediately or after the active operation.
It never silently changes an executing run or frozen evaluation procedure.
Candidate review distinguishes a detected signal, a plausible interpretation, missing checks, and a supported conclusion.
When additional checks are unavailable, Delta states that limitation and preserves an unresolved assessment.

### 6. Export and reproduce the investigation

The user exports the selected evidence and its provenance through the GUI.
Provenance records how the inputs, software, settings, and decisions produced the result.
The export includes source identifiers, hashes, configurations, versions, diagnostics, failures, exclusions, and claim limitations.
Observation inclusion follows source permissions and the user's export choice.
Credentials never enter the export.

A second installation imports the package, checks available inputs, and downloads missing public observations when authorized.
It repeats the numerical calculation with recorded versions and predefined comparison tolerances.
It reports unavailable inputs and numerical disagreement explicitly.
It need not regenerate identical agent prose to reproduce the scientific calculation.

## GUI coverage and recovery

The GUI includes investigations, observations, methods, agent connections, evidence, and application settings.
Contextual controls expose common operations.
An advanced operation list exposes every other supported user operation without requiring raw JSON or a terminal.
Settings include storage, acquisition queues, limits, backups, updates, credentials, and diagnostic export.
Method pages distinguish implemented, experimental, and unavailable capabilities.

| Failure or interruption | Required behavior |
|---|---|
| Archive connection fails | Preserve completed files. Resume or repeat incomplete transfers. Check file integrity. |
| Agent connection fails | Preserve the plan and records. Keep manual inspection and execution available. |
| Model access expires | Pause agent work and request reconnection without duplicating submitted jobs. |
| Application closes or computer sleeps | Recover investigation state and completed jobs. Identify interrupted attempts explicitly. |
| BLS work stops midway | Restart the affected job unless its method explicitly supports a valid checkpoint. |
| Storage becomes insufficient | Stop new downloads or jobs before free space falls below the configured reserve. |
| Budget expires | Stop further permitted work. Preserve the evidence and limit event. |
| Update fails | Preserve a recoverable database backup and a compatible runtime. |

Local services use loopback interfaces and scoped credentials by default.
Explicit LAN review uses the existing local review requirements.
The desktop shell needs narrow process interfaces, isolated rendering, and reviewed permissions.
An update requires compatible component versions and a checked migration and recovery path.
Model-use limits should use measurable quantities such as calls, tokens, and elapsed time.
Currency estimates must not imply exact subscription charges or provider-enforced spending limits.

## Scientific scope and release gates

The first beta supports exploratory TESS investigations with clear method limits.
It does not establish completeness, false-alarm rates, physical planet parameters, or planet confirmation.
The current flattening configuration can change signal depth.
The GUI must expose this limitation beside affected measurements.

The [scientific plan](https://github.com/delta-observatory/experiments/blob/main/PLAN.md) controls validation dependencies.
G03 review governs representative record requirements.
G01 and G02 establish protocol criteria, budgets, and separate evaluation cohorts.
T02 and T03 address injection recovery, preparation effects, negative controls, and false alarms.
T06 addresses transfer to untouched data.
T04 and T07 become necessary for their respective physical-inference and source-location claims, subject to the scientific plan's prerequisites.

Each evaluation needs its own approved scope and frozen protocol under the [procedure](https://github.com/delta-observatory/experiments/blob/main/PROCEDURE.md).
This product plan does not allocate cohorts or start those evaluations.
Campaign permissions, withheld labels, cohort restrictions, and identity-reveal rules remain enforceable through the API.
Product usability checks do not replace scientific evaluation.

## Delivery order and acceptance

This plan defines the stages below.
They supplement R0–R8 without changing their recorded completion status.

| Stage | Deliverable | Dependency | Acceptance evidence |
|---|---|---|---|
| P0: Distribution feasibility | Public runtime resources and a desktop packaging test. | Agreement on desktop scope and one Linux baseline. | A clean machine starts compatible services without private repositories or manual runtime installation. Resource measurements support the packaging choice. |
| P1: Investigation control | Versioned plans, revisions, approvals, branches, and event records. | Contract review and the existing campaign permissions. | GUI and agent calls produce equivalent records. Unauthorized scope changes fail. Restart preserves the approved plan. |
| P2: Acquisition and recovery | Bounded MAST selection, downloading, integrity checks, and storage controls. | P1, acquisition contracts, and the storage decision. | Interrupted transfers recover without duplicate observations. Byte limits and incompatible products stop affected work. |
| P3: One managed agent | Codex adapter, credential handling, session controls, and failure recovery. | P1 and supported provider authentication. | Steering, pause, reconnection, and manual fallback work without duplicate jobs or permission bypasses. |
| P4: Complete TESS journey | Guided and user-selected investigations, comparison, review, and reproducible export. | P2, P3, and Richard's interface design review. | Every supported operation has a GUI route. A second installation repeats the selected numerical result. |
| P5: Beta qualification | Installer, migration, backup, recovery, and external usability checks. | P4 and explicit scientific claim limits. | Representative users complete the journey. Supported systems pass recovery checks. Release documentation states scientific and platform limits. |

P0 passes offline execution and desktop rendering checks in an isolated Ubuntu filesystem.
The [P0 report](release/P0.md) records measurements and private dependency treatment.
Fresh desktop installation, normal distribution security policies, and complete resource measurements remain open.

P2 and P3 can proceed independently after their contracts and permissions are stable.
Scientific validation proceeds under its own dependencies.
Broader scientific claims require its evidence even when product acceptance passes.
Delivery estimates follow P0 measurements of packaging effort and resource requirements.

The initial usability study should include six to ten representative users.
Its purpose is to identify missing controls, unclear evidence, and installation failures.
It does not estimate scientific performance.
The beta acceptance record must include installation completion, investigation completion, time to first result, recovery outcomes, and reasons for assistance.

The decisive acceptance scenario is a complete investigation on a clean machine:

1. Install Delta through the supported installer.
2. Connect a supported model account or API key.
3. Select a small public TESS collection.
4. Approve the plan and bounded download.
5. Run the search through the GUI.
6. Change one parameter through a preserved branch.
7. Compare the two runs.
8. Record an assessment.
9. Recover the investigation after an application restart.
10. Export the evidence package.
11. Reproduce its numerical result on a second installation.

The scenario passes without terminal commands, private repository access, lost evidence, or duplicate jobs.
The associated scientific interpretation must remain within the method's documented scope.

## Deferred scope and decisions

Deferred capabilities include unrestricted agent code execution, multiple-agent teams, remote compute, shared investigations, all-sky campaigns, and bulk full-frame-image acquisition.
Additional scientific methods require compatible inputs, license review, and separate validation before adoption.
ExoMiner, RAVEN, transit fitting, and additional transit-search algorithms remain evaluation options.

The first implementation decisions are the supported Linux baseline, desktop packaging choice, public runtime resource ownership, storage policy, and permitted agent actions.
The public runtime must work without the private dataset catalog, method library, or experiment repositories.
Public recipes and manifests must preserve required provenance without publishing private research or downloaded observations.
Each reused dependency needs a recorded version and redistribution requirements.
Public release and external deployment require separate authorization.
