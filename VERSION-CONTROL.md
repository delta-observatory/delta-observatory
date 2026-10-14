# Local version control

The workspace contains nine independent Git repositories.
Each repository uses the `main` branch.
No remote addresses are configured.
Agents commit every completed change under the [commit rules](AGENTS.md#commits).
Richard controls pushes and external publication.

| Repository | Intended tracked contents |
|---|---|
| Workspace root | Coordination documents, workspace checks, and repository guidance. |
| `datasets/` | Catalog, metadata, acquisition instructions, manifests, and small acquisition evidence. |
| `detection/` | Methods, citations, retained papers, supporting code, and documented synthetic demonstrations. |
| `experiments/` | Procedures, protocols, code, dependency pins, manifests, small results, figures, reviews, and decisions. |
| `database/` | Schema definitions, migrations, and cross-component contracts. |
| `workers/` | Ingestion and scientific processing code, and vendored contracts. |
| `backend/` | Application API code, and vendored contracts. |
| `frontend/` | Application interface code, design decisions, and sky display assets. |
| `kubernetes/` | Deployment manifests, build and migration templates, and scripts. |

The root excludes every component directory.
The components are independent repositories, without submodules or shared release requirements.
A component repository does not indicate application implementation.

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

## Future reconstruction

Restore the coordination repository into `delta-observatory/`.
Restore each component into its corresponding directory.
Keep this sibling layout because documentation uses relative links between repositories.
Remote addresses and compatible commit references require a publication or release decision.
