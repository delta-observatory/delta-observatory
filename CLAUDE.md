# Delta Observatory agent instructions

Read [README.md](README.md) before work in this workspace.
Read [ROADMAP.md](ROADMAP.md) for current status.
Read [DESIGN.md](DESIGN.md) for intended requirements.
Follow [experiments/PROCEDURE.md](experiments/PROCEDURE.md) for scientific planning, execution, review, or reproduction.
Read [experiments/PLAN.md](experiments/PLAN.md) before assigning scientific task scope.
Read [REFERENCE-CATALOGS.md](REFERENCE-CATALOGS.md) before reference acquisition or identity comparison.
Read [detection/TOOLING.md](detection/TOOLING.md) before adding a scientific implementation.
Store downloaded observations in `raw/<dataset-id>/` at the workspace root.
Use the exact dataset directory name from `datasets/` for each `raw/` directory.
Read [database/contracts/](database/contracts/README.md) before work on the API, workers, or database.
Define job, result, method-parameter, and record shapes only in `database/contracts/`.
Keep the API stateless. Do not add runtime calls between the API and workers.

Use the ASD-STE100 writing instructions supplied by Richard.
Read the `asd-ste100` skill before writing user-facing text.
Codex uses `/home/richardtidwell/.codex/skills/asd-ste100/SKILL.md`. Claude uses `/home/richardtidwell/.claude/skills/asd-ste100/SKILL.md`.
Use at most 20 words for instructions and 25 words for descriptions.
Give one instruction in each sentence.
Use active voice for instructions.
Give each paragraph one topic and at most six sentences.
Use one term for each item.
Do not claim full dictionary conformity without the required dictionary check.
Preserve scientific facts, conditions, units, identifiers, citations, and uncertainty when editing documentation.
Keep current standards at stable paths without date or version suffixes.
Keep historical experiment and review evidence unchanged.
Protect another thread's task, environment, inputs, and outputs.
Do not start experiments merely because they appear in the plan.
Do not claim implemented capabilities from target-design prose or directory names.
Do not push, publish, or deploy unless Richard requests that action.

Run [scripts/check_workspace.py](scripts/check_workspace.py) after changes to documentation or structure.
Run the applicable component or scientific record checks when their evidence changes.
Read [CHECKS.md](CHECKS.md) before claiming audit coverage.

## Documentation style

Write documentation as the current state of the project.
Do not narrate history, sessions, threads, or who asked for a change.
Do not add dated progress logs, "now", "no longer", or "was added" statements.
Git history records changes. Closed experiment records keep their own chronology.
Name an owner only for active work, and remove the name when the work closes.

## Commits

Commit every completed change.
Commit each change in the repository that owns the changed files.
Commit documentation changes, new datasets, new detection material, and code changes.
Commit every valid experiment when it closes under [experiments/PROCEDURE.md](experiments/PROCEDURE.md).
A valid experiment completes without technical errors and passes its record validation.
Commit `positive`, `negative`, and `inconclusive` outcomes. A result that shows a method fails is valid evidence.
Do not commit a `not_evaluated` closure caused by a technical error. Fix the error and run the experiment again.
Do not commit an active experiment's partial outputs.
Run the applicable checks before each commit.
Inspect the staged files before each commit.
Do not commit credentials, environment files, or downloaded observation files.
Commit only your own changes. Do not commit another thread's active work.
Write a commit message that states what changed and why.
Keep [AGENTS.md](AGENTS.md) and [CLAUDE.md](CLAUDE.md) identical.
