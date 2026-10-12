# Delta Observatory agent instructions

Read [README.md](README.md) before work in this workspace.
Read [ROADMAP.md](ROADMAP.md) for current status.
Read [DESIGN.md](DESIGN.md) for intended requirements.
Follow [experiments/PROCEDURE.md](experiments/PROCEDURE.md) for scientific planning, execution, review, or reproduction.
Read [experiments/PLAN.md](experiments/PLAN.md) before assigning scientific task scope.
Read [REFERENCE-CATALOGS.md](REFERENCE-CATALOGS.md) before reference acquisition or identity comparison.
Read [detection/TOOLING.md](detection/TOOLING.md) before adding a scientific implementation.

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

## Commits

Commit every completed change.
Commit each change in the repository that owns the changed files.
Commit documentation changes, new datasets, new detection material, and code changes.
Commit an experiment when it closes under [experiments/PROCEDURE.md](experiments/PROCEDURE.md).
Do not commit an active experiment's partial outputs.
Run the applicable checks before each commit.
Inspect the staged files before each commit.
Do not commit credentials, environment files, or downloaded observation files.
Commit only your own changes. Do not commit another thread's active work.
Write a commit message that states what changed and why.
Keep [AGENTS.md](AGENTS.md) and [CLAUDE.md](CLAUDE.md) identical.
