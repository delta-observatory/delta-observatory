# Delta Observatory desktop

The desktop preview supports exploratory TESS investigations in a separate local workspace.
It bundles PostgreSQL, Python, the API, the scientific worker, the frontend, and the optional Codex agent host.
It uses five pinned public components and requires no private research repository.
[QUALIFICATION.md](QUALIFICATION.md) defines checked behavior and remaining acceptance requirements.
[P0.md](P0.md) preserves the initial packaging evidence.

## Open the application

Open `release/.dist/delta-observatory-preview-linux-x64/Delta Observatory.sh` from the file manager.
Alternatively, run this command from the workspace root:

```bash
"release/.dist/delta-observatory-preview-linux-x64/Delta Observatory.sh"
```

The first start requests a workspace directory.
The application remembers that directory in `$XDG_CONFIG_HOME/delta-observatory/desktop.json`, or `~/.config/delta-observatory/desktop.json`.
An explicit `--workspace=<directory>` selects a separate workspace without changing this preference.
The adjacent `.electron-profile` directory stores the browser profile.
The desktop window receives its workspace owner's token.

The Ubuntu 24.04 amd64 installer is `release/.dist/delta-observatory_0.2.0~preview1_amd64.deb`.
It installs the application under `/opt/delta-observatory` and supplies a desktop menu entry.
It supplies application-specific AppArmor permissions for the Chromium and Bubblewrap user namespaces.
The installer is a local preview artifact. Fresh operating-system installation qualification remains open.

## Complete an investigation

1. Select **Guided known-signal demonstration** or **New TESS investigation**.
2. Select **Acquire observations** to query MAST for a TIC target and sectors.
3. Inspect the exact product manifest and storage estimate.
4. Approve the manifest to download and check its files.
5. Select usable observations in the plan.
6. Review the question, scientific settings, exclusions, limits, and stopping conditions.
7. Save the investigation.
8. Approve its exact revision.
9. Select **Run approved plan**.
10. Select **Inspect plots** after the run completes.

The guided target is TIC 100100827, WASP-18, in sector 2.
It is a known-object demonstration on development data.
The package contains no downloaded astronomical observations.
**Workspace → Import TESS light curves** also accepts local `_lc.fits` files.

Each saved revision preserves its parent and settings.
An execution refers to an approved revision and a unique request key.
Repeated requests with that key return the same run.
**Pause new submissions** lets active jobs finish.
**Stop active work** cancels queued and active jobs while preserving completed results.
A recorded instruction does not change scientific parameters.
Parameter or scope changes require a saved revision and approval.

The evidence controls provide plots, complete results, run comparison, and export.
**Explore and inspect all records** provides the existing observation and research views.
**All operations** generates forms from the current API description and canonical record schemas.
These forms provide every API operation without requiring JSON input.
The API enforces permissions on every request.

## Optional managed agent

The connection controls use pinned Codex app-server 0.164.0 and the checked `gpt-5.4` model.
Model access requires an eligible account or an OpenAI API key.
The connection requests explicit consent before sending permitted investigation evidence and instructions to the provider.
Live account login and provider reconnection still require acceptance checks.

Credentials use memory or the operating-system credential store.
Memory credentials disappear when the isolated provider process ends.
The credential store requires a working desktop session bus and secret service.
Delta does not copy credentials into research records, exports, backups, or diagnostics.

The agent receives API tools scoped to its approved investigation.
The isolated process has no Delta database socket, access token, observation files, or artifact directory.
The checked model receives no shell, filesystem, browser, application, or delegation tools.
Unsupported models remain unavailable until their isolation checks pass.

Saved session records preserve provider references and measured use.
Reconnect rotates the scoped client token.
The API enforces approved job, compute, turn, and measured token limits.
Token notifications can arrive after use. These controls do not guarantee a provider spending cap.
Closing the investigation view disconnects the managed agent.
Manual controls remain available without a provider connection.

## Storage, reproduction, and recovery

**Workspace** provides storage limits, import, reproduction, backups, restore, diagnostics, and release metadata checks.
The default workspace limit is 20 GiB. The minimum free-space reserve is 512 MiB.
Downloads, imports, and worker outputs check these limits before writing.
Startup also requires at least 512 MiB of available memory.
Large campaigns need separate resource qualification.

**Export evidence** can create a portable reproduction package.
Original observation inclusion requires an explicit selection.
The package preserves input hashes, source identifiers, settings, software versions, research records, and numerical evidence.

A second workspace imports the package through normal indexing.
**Prepare repeat plan** creates a separate investigation for review and approval.
Missing inputs remain explicit. Acquire or import the exact files before preparing the repeat.
**Compare numerical results** checks input hashes, measurement metadata, parameters, and values.
Absolute tolerance is `1e-12`. Relative tolerance is `1e-10`.
These tolerances measure numerical agreement and do not represent scientific uncertainty.
Runtime differences appear separately in the report.

Backups contain checked CSV table values, artifacts, reproduction records, and optional original observations.
They exclude provider profiles, logs, and plaintext access credentials.
Restore uses trusted application migrations and never executes SQL supplied by a backup.
It creates a separate workspace and regenerates client credentials.
The original workspace remains available.
Startup saves a full backup before pending database migrations.

**Check published release** reads GitHub release metadata only.
It does not install an update.
The application refuses database downgrades and incomplete restores.
**File → Quit** stops the desktop and its local services.

## LAN review

Run this command from the workspace root:

```bash
"release/.dist/delta-observatory-preview-linux-x64/Delta Observatory.sh" \
  --workspace="$PWD/release/.state/product-preview" \
  --review-host=0.0.0.0 --review-port=41871
```

Open `http://<machine-LAN-address>:41871/?investigations` in a LAN browser.
Anonymous browser access uses the existing read-only GUI client.
The server does not attach the owner credential to browser requests.
**Workspace → Copy this workspace token** supplies the token for authorized browser operations.
Managed model connections and local file operations require the native desktop window.

The default frontend binds to loopback on an available port.
The API always binds to loopback.
PostgreSQL uses a private Unix socket and does not listen on TCP.
The desktop does not connect to the k3s deployment.

## Build from public source

Build on Ubuntu 24.04 x86-64 with glibc 2.39.
Build dependencies include Git, Python, Node.js, npm, uv, a C compiler, Make, Bison, Flex, pkg-config, tar, and bzip2.
The checked build uses Node.js 22.22.3 and uv 0.12.7.
Build downloads require network access. Manual analysis runs offline after acquisition.

1. Restore the public components:

   ```bash
   python3 scripts/components.py clone
   ```

2. Export the pinned public sources:

   ```bash
   python3 release/scripts/prepare.py --output release/.build/sources
   ```

3. Install the desktop dependencies:

   ```bash
   npm ci --prefix release
   ```

4. Install the frontend dependencies:

   ```bash
   npm ci --prefix release/.build/sources/frontend
   ```

5. Build the frontend:

   ```bash
   npm run build --prefix release/.build/sources/frontend
   ```

6. Download the checked PostgreSQL source:

   ```bash
   python3 release/scripts/fetch-source.py postgresql
   ```

7. Build the runtime directory:

   ```bash
   sh release/scripts/build-runtime.sh
   ```

8. Download the pinned Bubblewrap package inside the Ubuntu build environment:

   ```bash
   (cd /tmp && apt download bubblewrap=0.9.0-1ubuntu0.3)
   ```

9. Extract the package:

   ```bash
   dpkg-deb -x /tmp/bubblewrap_0.9.0-1ubuntu0.3_amd64.deb /tmp/delta-bwrap-package
   ```

10. Bundle the agent runtime and Ubuntu libraries:

    ```bash
    python3 release/scripts/bundle-agent.py --ubuntu-root /
    ```

11. Assemble the application in an unused directory:

    ```bash
    python3 release/scripts/package.py --output release/.dist/delta-observatory-preview-linux-x64
    ```

12. Create the installer without installing it:

    ```bash
    python3 release/scripts/installer.py \
      --package release/.dist/delta-observatory-preview-linux-x64 \
      --output 'release/.dist/delta-observatory_0.2.0~preview1_amd64.deb'
    ```

`prepare.py` exports Git commits and checks vendored contracts and migrations.
The API and worker keep separate Python dependency directories.
Packaging replaces remote fonts with local licensed fonts.
`BUILD.json` records component commits, runtime versions, file sizes, and SHA-256 hashes.
The package retains dependency metadata and license notices.
Public binary distribution requires separate authorization and complete redistribution review.

## Checks

Run these commands from the workspace root:

```bash
node --test release/tests/*.test.cjs
backend/.venv/bin/python -B -m unittest discover -s release/tests -p 'test_*.py'
python3 release/scripts/smoke.py --app <package>/resources/app --workspace <unused-workspace> --output <unused-report>
python3 release/scripts/product-check.py --app <package>/resources/app --output <unused-directory>
python3 release/scripts/migration-check.py --previous-app <previous-package>/resources/app --app <package>/resources/app --output <unused-directory>
python3 release/scripts/check-clean.py --rootfs <ubuntu-root> --package <package> --output <unused-directory>
```

The fixtures contain synthetic engineering samples. They do not measure scientific performance.
The product check covers plan approval, branches, review records, numerical reproduction, backups, credential rotation, and restart.
The migration check covers automatic backup and recovery from the previous desktop schema.
The isolated check hides host files and system language runtimes.
It disables external networking and checks the agent against a local fake provider.
It checks native desktop forms, plots, navigation, settings, scrolling, and screenshots on an isolated X display.
[QUALIFICATION.md](QUALIFICATION.md) records the evidence and limits.

## Local files

| Directory | Contents |
|---|---|
| `desktop/` | Native shell, agent bridge, file operations, recovery, and service supervision. |
| `resources/` | Public TESS catalog and runtime notices. |
| `scripts/` | Source export, runtime build, installer creation, and integration checks. |
| `tests/` | Unit checks, synthetic fixtures, and desktop checks. |
| `evidence/` | Retained engineering reports and screenshots. |
| `.build/` | Ignored build sources, runtime payload, and test workspaces. |
| `.cache/` | Ignored build downloads. |
| `.dist/` | Ignored application directories and installer. |
| `.state/` | Ignored local preview workspace. |

Application state and downloaded observations remain outside Git.
