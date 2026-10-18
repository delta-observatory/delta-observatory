# Public release

This document defines the public release structure, the reviewed public material, the access model, the publication checklist, and the planned CI/CD.
Each external step needs Richard's approval. No repository is published, and no remote address is configured.

## Structure

The release uses separate repositories in the GitHub organization `delta-observatory`.
The workspace root is the entry repository. [components.json](components.json) lists every component and pins the commit of each public component.

| Repository | Visibility | Builds |
|---|---|---|
| `delta-observatory` (workspace root) | Public | None. Documents, `components.json`, the example investigation, and workspace checks. |
| `database` | Public | Migration image `delta-database`. |
| `workers` | Public | Worker image `delta-workers`. |
| `backend` | Public | API image `delta-backend`. |
| `frontend` | Public | Frontend image `delta-frontend`. |
| `kubernetes` | Public | None. Manifests and scripts that build and deploy the four images. |
| `agents` | Public | None. The MCP adapter and the importer run from source. |
| `datasets`, `detection`, `experiments` | Private | None. |

Each public repository keeps its existing history. No history is rewritten.
`python3 scripts/components.py clone` restores the sibling layout from GitHub. The documents and `kubernetes/scripts/build.sh` use that layout.
A GitHub Project can track issues across the organization. It does not hold code.

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

**Private material.** The 65 retained papers in `detection` stay private. 53 of them do not permit redistribution, and two are unclear.
The closed experiment evidence in `experiments` stays private and unchanged.

**Example exports.** [examples/wasp-18b/](examples/wasp-18b/README.md) holds three API exports. They contain no host address or home path.

## Access

The deployment serves the LAN only. The API needs a token for each request and checks each permission.
Invited reviewers will receive personal clients with only the `read` permission.
Cloudflare Tunnel and Cloudflare Access will give them the frontend without an open inbound port. That access is not deployed.
The frontend disables the controls that a client's permissions do not allow. This display authorizes nothing.
No anonymous access is planned.

## Fresh checkout verification

A fresh checkout restores the entry repository and the six public components in an empty directory.
Before publication, `--source` clones the components from the local repositories instead of GitHub.
The [verification record](#verification-record) gives the commands, the commits, and the results.

## Publication checklist

Do the steps in this order. Each step that changes something outside this computer needs Richard's approval.

1. Richard confirms that he owns the copyright of the public material and that no employment or client agreement claims it.
2. Review the release commits of the seven public repositories.
3. Create the GitHub organization `delta-observatory`.
4. Create seven empty public repositories with the names in `components.json`. Do not add a README or a licence on GitHub.
5. Add the `origin` remote to each of the seven local repositories and push `main`. Check each push with `git ls-remote`.
6. Protect `main`, and turn on secret scanning in each repository.
7. Clone the entry repository from GitHub into an empty directory. Run `python3 scripts/components.py clone` and `check`, and the [small demonstration](README.md#small-demonstration).
8. Build and deploy the frontend image that disables the write controls: `scripts/build.sh frontend`, `scripts/set-tag.sh frontend <tag>`, and `kubectl apply -k base`.
9. For reviewer access: create one read-only client for each reviewer, then configure Cloudflare Tunnel and an Access policy for the frontend host name. Test with one reviewer account first.

Keep `raw/`, the private repositories, `~/backups/delta-observatory/`, and every token file local.

## Planned CI/CD

This outline is not implemented. Each repository gets its own workflow, image, and version.

| Repository | Pull request checks | Release |
|---|---|---|
| `database` | `check_contracts.py`, and the migrations on a PostgreSQL service | A tag builds the migration image. It also sends a `contracts-changed` event to `backend` and `workers`. |
| `backend` | `uv run pytest` with `pgserver`, and a check that `vendor/contracts/SOURCE` names a tagged `database` commit | A tag builds the API image. A change to `tests/vectors/` or the API description sends an event to `frontend` and `agents`. |
| `workers` | `pytest`, and the same contract source check | A tag builds the worker image. The T01 regression needs two public TESS light curves, which a cached download step can supply. |
| `frontend` | `npm ci`, `npm test`, `npm run typecheck`, and `npm run build` | A tag builds the frontend image. |
| `kubernetes` | `kubectl kustomize base`, and a schema check of the rendered manifests | No automatic deployment. The node has no inbound access. A later decision can add a self-hosted runner or a pull-based deployment. |
| `agents` | Both unittest suites, and the adapter generation against the current API description | None. |
| `delta-observatory` | `python3 -m unittest scripts/test_components.py`, and a check that each pinned commit exists in its repository | None. |

**Dependent checks.** A contract change starts in `database`.
The `contracts-changed` event opens a pull request in `backend` and in `workers` that runs `scripts/sync_contracts.sh <tag>` and their tests.
A `backend` change to the shared vectors or the API description opens the same kind of pull request in `frontend` (`scripts/sync-api-vectors.sh`) and in `agents` (adapter generation).
After the component releases, a pull request in the entry repository updates `components.json` with `python3 scripts/components.py pin`.

**Images.** GitHub Container Registry can hold the four images with version and commit tags.
The node builds images locally and does not pull them. A change to registry images is a separate deployment decision.
A published image contains GPL and LGPL packages. It must include their licence texts and offer their source.

## Verification record

Checked on 2026-10-18 in an empty directory on the reference node, with Python 3.14.7 for the scripts, `uv` 0.12.7 with Python 3.12 for the tests, Node 25.9.0, npm 11.12.1, and Git 2.55.0.
The entry repository was at commit `f462e8a`. `git clone` copied it from the local repository.

| Step | Command | Result |
|---|---|---|
| Restore the components | `python3 scripts/components.py clone --source <local workspace>` | Exit 0. Six public components at their pinned commits. Three private components not cloned. |
| Check the pins | `python3 scripts/components.py check` | Exit 0. All six match. The entry repository has no untracked or changed files. |
| Example file hashes | `(cd examples/wasp-18b && sha256sum -c SHA256SUMS)` | Exit 0. Three files OK. |
| Example export | `python3 backend/scripts/verify_export.py examples/wasp-18b/run-4dc34144-max-period-20d.zip --manifest-sha256 70c0c9b6…` | Exit 0. Passed, 13 files checked, no failures. |
| Contracts | `uv run -q --no-project --with jsonschema==4.25.1 python scripts/check_contracts.py` in `database` | Exit 0. 14 schemas, 36 examples, 0 failures. |
| API | `uv run pytest -q` in `backend` | Exit 0. 82 passed. |
| Worker | `.venv/bin/python -m pytest -q` in `workers` | Exit 0. 1 passed, 8 skipped: no TESS light curves and no T01 record. |
| Frontend | `npm ci`, `npm test`, and `npm run build` in `frontend` | 90 tests passed. The build exited 0. |
| Agents | Both unittest suites in `agents` | 12 and 6 tests OK. |
| Entry repository | `python3 -m unittest scripts/test_components.py` | 8 tests OK. |

In the full workspace, with the light curves and the private repositories, the worker suite gives 9 passed.

**Permission-aware display.** A headless Chromium session loaded the frontend build against the running API.
It replaced the `GET /api/me` response with a client that has only `read`, and it blocked every request except `GET` and the run estimate.
The run form and the record controls were disabled with the missing permission, the top bar showed "read only", and no page error occurred.
The same session with Richard's permissions showed every control enabled. The session sent no write request.

**Not tested.** These checks do not clone from GitHub, because no repository is published.
They do not build the container images, deploy to k3s, run the full stack from the public repositories, or use Node 22.
They do not run the MCP adapter against the running API.
The deployed frontend image does not include the permission-aware display.

