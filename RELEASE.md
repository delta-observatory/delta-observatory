# Public release

This document defines the public release structure, the reviewed public material, the access model, the publication state, and the planned CI/CD.
All eleven repositories are on GitHub in the organization [`delta-observatory`](https://github.com/delta-observatory).

## Structure

The release uses separate repositories in the GitHub organization `delta-observatory`.
The workspace root is the entry repository. [components.json](components.json) lists every component and pins the commit of each public component.

| Repository | Visibility | Builds |
|---|---|---|
| `delta-observatory` (workspace root) | Public | Local P0 desktop prototype in `release/`. Documents, `components.json`, the example investigation, and workspace checks. |
| `database` | Public | Migration image `delta-database`. |
| `workers` | Public | Worker image `delta-workers`. |
| `backend` | Public | API image `delta-backend`. |
| `frontend` | Public | Frontend image `delta-frontend`. |
| `kubernetes` | Public | None. Manifests and scripts that build and deploy the four images. |
| `agents` | Public | None. The MCP adapter and the importer run from source. |
| `.github` (local directory `community`) | Public | None. The organization profile and the default security policy. |
| `datasets`, `detection`, `experiments` | Private | None. |

Each public repository keeps its existing history. No history is rewritten.
`python3 scripts/components.py clone` restores the sibling layout from GitHub. The documents and `kubernetes/scripts/build.sh` use that layout.
A GitHub Project can track issues across the organization. It does not hold code.

The [P0 desktop prototype](release/README.md) produces a local Linux application directory and archive.
Its [dependency report](release/P0.md) defines the engineering checks and remaining distribution requirements.
The local prototype is separate from published releases and the k3s deployment.
Public binary distribution requires separate authorization and complete redistribution review.

## Public material review

**Credentials.** A scan of every blob in the history of all ten repositories found no credential.
The scan used pattern rules and `detect-secrets`, so it cannot prove that no secret exists. No token or environment file is tracked or untracked.

**Accepted history details.** Older commits keep the LAN address of the node, the host name `machine`, and home-directory paths.
Commit messages of nine repositories have `Claude-Session` trailers. These links need a claude.ai login.
The current files of the public repositories use `localhost` defaults or `<node>` instead of the LAN address.
The `kubernetes` base manifests keep the host paths of the reference node.

**Licences.** Each public repository has the MIT `LICENSE`. The Python projects and the frontend package state the licence.
The frontend keeps the d3-celestial BSD 3-Clause notice for the sky data.
[ACKNOWLEDGMENTS.md](ACKNOWLEDGMENTS.md) gives the data acknowledgments.

**Private material.** The three research repositories are private repositories in the same organization. The 65 retained papers in `detection` stay private. 53 of them do not permit redistribution, and two are unclear.
The closed experiment evidence in `experiments` stays private and unchanged.

**Example exports.** [examples/wasp-18b/](examples/wasp-18b/README.md) holds three API exports. They contain no host address or home path.

## Access

The deployment serves the LAN only. The API needs a token for each request and checks each permission.
Reviewer access is deferred. The planned form gives invited reviewers personal clients with only the `read` permission.
Cloudflare Tunnel and Cloudflare Access would give them the frontend without an open inbound port.
The frontend disables the controls that a client's permissions do not allow. This display authorizes nothing.
No anonymous access is planned.

## Fresh checkout verification

A fresh checkout restores the entry repository and the seven other public repositories in an empty directory.
The [verification record](#verification-record) gives the commands, the commits, and the results.

## Publication state

| Item | State |
|---|---|
| Repositories | Eight public repositories and three private repositories, each with a description and the entry repository as homepage. The public repositories have topics. |
| Branches | Each local `main` tracks `origin/main`. |
| Vulnerability reports | Private vulnerability reporting is on in each public repository. `.github` holds the default `SECURITY.md`. |
| Secret scanning | Secret scanning and push protection are on in each public repository. |
| Branch protection | The ruleset "Protect main" blocks deletion and force pushes of `main` in each public repository. The GitHub Free plan does not give rulesets to private repositories. |
| Release | Tag `v0.1.0` marks the pinned commit of each public repository. The entry repository has the GitHub release `v0.1.0`. |

These steps need the GitHub web interface:

1. Upload `docs/social-preview.png` in the entry repository: **Settings**, **General**, **Social preview**, **Edit**, **Upload an image**.
2. Pin the entry repository on the organization page: open https://github.com/delta-observatory, select **Customize pins**, and select `delta-observatory`.

These steps are separate decisions:

- Build and deploy the frontend image that disables the write controls: `scripts/build.sh frontend`, `scripts/set-tag.sh frontend <tag>`, and `kubectl apply -k base`.
- Reviewer access through Cloudflare Tunnel and Cloudflare Access.

Keep `raw/`, `~/backups/delta-observatory/`, and every token file local.

## Planned CI/CD

This outline is not implemented. Each repository gets its own workflow and version.
The four application components produce separate images.
Standard GitHub-hosted Linux runners perform tests and builds.
Flux applies the cloud deployment from the `kubernetes` repository.
The [hosting plan](https://github.com/delta-observatory/kubernetes/blob/main/HOSTING.md#github-actions-and-flux-workflow) defines deployment ordering, credentials, and free usage conditions.

| Repository | Pull request checks | Release |
|---|---|---|
| `database` | `check_contracts.py`, and the migrations on a PostgreSQL service | A tag builds the migration image. It also sends a `contracts-changed` event to `backend` and `workers`. |
| `backend` | `uv run pytest` with `pgserver`, and a check that `vendor/contracts/SOURCE` names a tagged `database` commit | A tag builds the API image. A change to `tests/vectors/` or the API description sends an event to `frontend` and `agents`. |
| `workers` | `pytest`, and the same contract source check | A tag builds the worker image. The T01 regression needs two public TESS light curves, which a cached download step can supply. |
| `frontend` | `npm ci`, `npm test`, `npm run typecheck`, and `npm run build` | A tag builds the frontend image. |
| `kubernetes` | Render the home base and cloud overlay, check schemas, and check release compatibility | A checked deployment PR selects image digests. After merge, Flux applies the cloud configuration without inbound runner access. |
| `agents` | Both unittest suites, and the adapter generation against the current API description | None. |
| `delta-observatory` | `python3 -m unittest scripts/test_components.py`, and a check that each pinned commit exists in its repository | None. |

**Dependent checks.** A contract change starts in `database`.
The `contracts-changed` event opens a pull request in `backend` and in `workers` that runs `scripts/sync_contracts.sh <tag>` and their tests.
A `backend` change to the shared vectors or the API description opens the same kind of pull request in `frontend` (`scripts/sync-api-vectors.sh`) and in `agents` (adapter generation).
After the component releases, a pull request in the entry repository updates `components.json` with `python3 scripts/components.py pin`.

**Images.** GitHub Actions builds images after successful tests on trusted `main` commits or release tags.
GHCR holds the four images with version and commit tags.
A deployment pull request selects exact image digests for the cloud installation.
The home deployment retains its local build procedure.
The cloud plan uses GitHub-hosted runners and requires no build runner on the VPS.
A published image contains GPL and LGPL packages. It must include their licence texts and offer their source.

## Verification record

Checked on 2026-10-18 in an empty directory on the reference node, with Python 3.14.7 for the scripts, `uv` 0.12.7 with Python 3.12 for the tests, Node 25.9.0, npm 11.12.1, and Git 2.55.0.
An anonymous HTTPS clone copied the entry repository from GitHub at commit `43c1cc8`. Later commits change documents and the message of the workspace check only.

| Step | Command | Result |
|---|---|---|
| Restore the components | `python3 scripts/components.py clone` | Exit 0. Seven public repositories from GitHub at their pinned commits. Three private components not cloned. |
| Check the pins | `python3 scripts/components.py check` | Exit 0. All seven match. The entry repository has no untracked or changed files. |
| Example file hashes | `(cd examples/wasp-18b && sha256sum -c SHA256SUMS)` | Exit 0. Three files OK. |
| Example export | `python3 backend/scripts/verify_export.py examples/wasp-18b/run-4dc34144-max-period-20d.zip --manifest-sha256 70c0c9b6…` | Exit 0. Passed, 13 files checked, no failures. |
| Contracts | `uv run -q --no-project --with jsonschema==4.25.1 python scripts/check_contracts.py` in `database` | Exit 0. 14 schemas, 36 examples, 0 failures. |
| API | `uv run pytest -q` in `backend` | Exit 0. 82 passed. |
| Worker | `.venv/bin/python -m pytest -q` in `workers` | Exit 0. 1 passed, 8 skipped: no TESS light curves and no T01 record. |
| Frontend | `npm ci`, `npm test`, and `npm run build` in `frontend` | 90 tests passed. The build exited 0. |
| Agents | Both unittest suites in `agents` | 12 and 6 tests OK. |
| Entry repository | `python3 -m unittest scripts/test_components.py` | 10 tests OK. |
| Workspace check | `python3 scripts/check_workspace.py` | Status `unavailable`, exit 2: the private repositories are absent. In the full workspace, the check passes. |

In the full workspace, with the light curves and the private repositories, the worker suite gives 9 passed.

**Permission-aware display.** A headless Chromium session loaded the frontend build against the running API.
It replaced the `GET /api/me` response with a client that has only `read`, and it blocked every request except `GET` and the run estimate.
The run form and the record controls were disabled with the missing permission, the top bar showed "read only", and no page error occurred.
The same session with Richard's permissions showed every control enabled. The session sent no write request.

**Not tested.** These checks do not build the container images, deploy to k3s, run the full stack from the public repositories, or use Node 22.
They do not run the MCP adapter against the running API.
The deployed frontend image does not include the permission-aware display.
