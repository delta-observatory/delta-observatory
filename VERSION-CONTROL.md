# Local version control

The workspace contains eleven independent Git repositories.
Each repository uses the `main` branch.
Each repository has the remote `origin` in the GitHub organization `delta-observatory`.
Agents commit every completed change under the [commit rules](AGENTS.md#commits).
Agents push completed commits to each repository's existing GitHub remote after the applicable checks pass.
Richard controls release publication, deployment, and repository visibility changes.
Agents do not force-push without Richard's explicit request.

| Repository | Intended tracked contents | Release visibility |
|---|---|---|
| Workspace root | Coordination documents, workspace checks, repository guidance, the component manifest, and the example investigation. | Public entry repository |
| `datasets/` | Catalog, metadata, acquisition instructions, manifests, and small acquisition evidence. | Private |
| `detection/` | Methods, citations, retained papers, supporting code, and documented synthetic demonstrations. | Private |
| `experiments/` | Procedures, protocols, code, dependency pins, manifests, small results, figures, reviews, and decisions. | Private |
| `database/` | Schema definitions, migrations, and cross-component contracts. | Public |
| `workers/` | Ingestion and scientific processing code, and vendored contracts. | Public |
| `backend/` | Application API code, and vendored contracts. | Public |
| `frontend/` | Application interface code, design decisions, and sky display assets. | Public |
| `kubernetes/` | Deployment manifests, build and migration templates, and scripts. | Public |
| `agents/` | Agent instructions, templates, and tooling. Agent code uses the API only. | Public |
| `community/` | The organization profile and the default security policy, as the GitHub repository `.github`. | Public |

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

## Reconstruction

[components.json](components.json) lists each component, its visibility, and, for a public component, its address in the GitHub organization `delta-observatory` and its pinned commit.
Restore the coordination repository into `delta-observatory/`. Then clone the public components into it:

```bash
python3 scripts/components.py clone
python3 scripts/components.py check
```

Keep this sibling layout because documentation and build scripts use relative paths between repositories.
Restore the private components from their private copies into the directories of the same names.
Pin the current commits with `python3 scripts/components.py pin` before a release, after each component is committed.
[RELEASE.md](RELEASE.md) gives the publication state and the repository settings.
