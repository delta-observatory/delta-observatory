# Delta desktop prototype

This directory contains the P0 Linux desktop prototype.
The root repository owns its source.
It uses the pinned public frontend, API, worker, and database components.
[P0.md](P0.md) records dependencies, private repository boundaries, checks, and remaining qualification work.

The prototype starts its own PostgreSQL database, API, worker, and Electron window.
Its workspace contains its credentials, observations, results, and logs.
It does not connect to the k3s deployment.
The existing frontend provides analysis, comparison, review, and export controls.

## Run the local package

Open `release/.dist/delta-observatory-desktop-linux-x64/Delta Observatory.sh` from the file manager.
Alternatively, run this command from the workspace root:

```bash
"release/.dist/delta-observatory-desktop-linux-x64/Delta Observatory.sh"
```

The default workspace is `$XDG_DATA_HOME/delta-observatory-prototype/workspace`.
When `XDG_DATA_HOME` is absent, the application uses `~/.local/share/delta-observatory-prototype/workspace`.
The adjacent `.electron-profile` directory stores the browser profile.
The application signs the local owner into its desktop window.

Select **File → Import TESS light curves** to copy local `_lc.fits` files into the prototype.
The worker checks the files before analysis.
The prototype starts empty and includes no astronomical observations.
File import supports at most 128 files and 2 GiB per operation.
Automatic archive acquisition and managed agents remain outside P0.

Select **File → Quit** to stop the desktop and its services.
The workspace remains available for the next start.
Startup refuses foreign directories, conflicting workspace ownership, incompatible PostgreSQL versions, and database downgrades.

## Separate review workspace

Run this command from the workspace root to expose the prototype for LAN review:

```bash
"release/.dist/delta-observatory-desktop-linux-x64/Delta Observatory.sh" \
  --workspace="$PWD/release/.state/preview" \
  --review-host=0.0.0.0 --review-port=41871
```

The browser address is `http://<machine-LAN-address>:41871/`.
The desktop window receives the workspace owner's credential.
A LAN browser receives read access through the existing GUI reader.
The server does not attach the owner credential to browser requests.
The **Prototype** menu identifies the workspace and provides its owner token.
Authenticated browser operations require that token.
The default start binds the frontend to loopback on an available port.
The API always binds to loopback on an available port.
PostgreSQL uses a private Unix socket and does not listen on TCP.

## Build from public source

Build the runtime on Ubuntu 24.04 x86-64 with glibc 2.39.
The build needs Git, Python 3.12 or later, Node.js 22 or later, npm, and uv.
It also needs a C compiler, Make, Bison, Flex, pkg-config, tar, and bzip2.
The checked build uses Node.js 22.22.3 and uv 0.12.7.
Build downloads require network access.
The completed package runs without network access.

1. Restore the public component checkouts from the root repository:

   ```bash
   python3 scripts/components.py clone
   ```

2. Export the pinned public sources:

   ```bash
   python3 release/scripts/prepare.py --output release/.build/sources
   ```

3. Install the pinned desktop build packages:

   ```bash
   npm ci --prefix release
   ```

4. Build the exported frontend:

   ```bash
   npm ci --prefix release/.build/sources/frontend
   npm run build --prefix release/.build/sources/frontend
   ```

5. Download the checked PostgreSQL source:

   ```bash
   python3 release/scripts/fetch-source.py postgresql
   ```

6. Build the private runtime directory:

   ```bash
   sh release/scripts/build-runtime.sh
   ```

7. Assemble the application in an unused output directory:

   ```bash
   python3 release/scripts/package.py \
     --output release/.dist/delta-observatory-desktop-linux-x64
   ```

`prepare.py` exports Git commits, not working files.
It checks all vendored JSON contracts and SQL migrations against the pinned database component.
The API and worker keep separate Python dependency directories because their pinned versions differ.
Packaging replaces remote font references in the exported frontend with local, licensed fonts.
The public frontend source remains unchanged.

`BUILD.json` records source commits, runtime versions, and every regular file's size and SHA-256.
Dependency metadata and license files remain inside the package.
This prototype has no automatic updater, system installer, or application menu entry.
Public binary distribution requires a complete license and source-offer review.

## Checks

Run the desktop unit checks:

```bash
node --test release/tests/*.test.cjs
```

Run the runtime check with unused workspace and report paths:

```bash
python3 release/scripts/smoke.py \
  --app release/.dist/delta-observatory-desktop-linux-x64/resources/app \
  --workspace /tmp/delta-desktop-check-workspace \
  --output /tmp/delta-desktop-check-report
```

The fixture contains synthetic brightness samples for an engineering check.
It does not measure scientific performance.
The check exercises indexing, BLS execution, permissions, evidence hashes, shutdown, and restart.

The isolated check also needs Bubblewrap and an Ubuntu filesystem with the desktop libraries and Xvfb.
Run the isolated check with an unused output directory:

```bash
python3 release/scripts/check-clean.py \
  --rootfs release/.build/ubuntu \
  --package release/.dist/delta-observatory-desktop-linux-x64 \
  --output release/.build/checks/ubuntu-review
```

The check hides host files and system language runtimes.
It disables network access and checks the Electron window on an isolated X display.
[P0.md](P0.md) describes the filesystem preparation and the limits of this test.
The root workspace check retains its separate private repository requirement.

## Local files

| Directory | Contents |
|---|---|
| `desktop/` | Electron shell, import controls, local frontend server, and service supervisor. |
| `resources/` | Minimal public TESS catalog. |
| `scripts/` | Source export, runtime build, packaging, and integration checks. |
| `tests/` | Desktop unit checks, synthetic fixture, and isolated execution. |
| `evidence/` | Checked engineering report and desktop screenshot. |
| `.build/` | Ignored build sources, runtime payload, and temporary test workspaces. |
| `.cache/` | Ignored downloaded build dependencies. |
| `.dist/` | Ignored application directory and archive. |
| `.state/` | Ignored local preview workspace. |

Application state and downloaded observations must remain outside Git.
