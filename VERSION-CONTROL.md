# Local version control

The workspace contains nine independent Git repositories.
Each repository uses the `main` branch.
Initialization creates local Git metadata without creating a commit or remote repository.
Initial commits record the root, datasets, detection, experiments, and database repositories.
The database repository contains contract documentation only.
The four other application repositories contain exclusion rules only and remain without commits.
Agents commit every completed change under the [commit rules](AGENTS.md#commits).
Richard controls pushes and external publication.

| Repository | Intended tracked contents |
|---|---|
| Workspace root | Coordination documents, workspace checks, and repository guidance. |
| `datasets/` | Catalog, metadata, acquisition instructions, manifests, and small acquisition evidence. |
| `detection/` | Methods, citations, retained papers, supporting code, and documented synthetic demonstrations. |
| `experiments/` | Procedures, protocols, code, dependency pins, manifests, small results, figures, reviews, and decisions. |
| `database/` | Future schema definitions, migrations, and cross-component contracts. |
| `workers/` | Future ingestion and scientific processing code. |
| `backend/` | Future application API and coordination code. |
| `frontend/` | Future application interface code. |
| `kubernetes/` | Future deployment manifests and configuration templates. |

The root excludes every component directory.
The components are independent repositories, without submodules or shared release requirements.
Application repositories currently contain exclusion rules and documentation only.
Repository initialization does not indicate application implementation.

## Exclusions

Each repository excludes local credentials, environment files, dependency environments, and generated caches.
An `.env.example` file can contain documented placeholder values.
Research repositories also exclude observation FITS files and local download or run directories.
Experiments retain their existing array exclusions.
The detection library retains its documented synthetic array and reference PDFs.

Store downloaded observations in `raw/<dataset-id>/` at the workspace root.
The root repository excludes `raw/`.
Keep large execution outputs outside these repositories.
Inspect proposed files before committing them.
Exclusion rules do not identify every possible credential or large scientific file.

## Checks

Run the workspace check from the root:

```bash
python3 scripts/check_workspace.py
```

Inspect a component separately:

```bash
git -C experiments status --short
git -C experiments remote -v
git -C experiments ls-files --others --exclude-standard
```

Inspect the root separately:

```bash
git status --short
```

A clean root status does not establish clean component repositories.
Before the first commit, Git cannot provide a committed recovery point for the current files.

## Future reconstruction

Restore the coordination repository into `delta-observatory/`.
Restore each component into its corresponding directory.
Keep this sibling layout because documentation uses relative links between repositories.
Remote addresses and compatible commit references require a later publication or release decision.
