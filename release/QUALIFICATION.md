# Desktop preview qualification

The preview implements exploratory TESS investigations and the complete manual workflow.
It includes bounded acquisition, versioned plans, managed agent controls, evidence export, numerical reproduction, storage settings, backups, and an Ubuntu installer.
Engineering checks use synthetic inputs. They do not establish astronomical validity.
The preview does not claim completed beta qualification.

## Checked scope

| Area | Evidence and result |
|---|---|
| Contracts | 25 schemas and 58 examples pass. Canonical contracts define plans, acquisition, sessions, reproduction, storage, and backups. |
| API | 102 tests pass against temporary PostgreSQL servers. Checks include scope, exact approval, concurrency, repeated execution keys, and cumulative session limits. |
| Workers | 14 tests pass. Coverage includes scientific regression, acquisition integrity and retry, indexing, cancellation, and storage limits. |
| Frontend | TypeScript and the production build pass. The component suite contains 108 passing tests. |
| Agent components | 12 adapter, 10 importer, and 19 managed-host tests pass with test services. |
| Isolated agent | Pinned Codex and Claude Code complete tool exchanges against local fake providers. Claude Code also resumes its saved conversation. |
| Filesystem isolation | The bundled Bubblewrap process cannot see the synthetic private token, host home, or database socket. |
| Login | Native provider processes start and cancel authorization. Process fixtures check account completion. Ten renderer checks cover both providers and error recovery. |
| Native interface | Automated desktop checks create, approve, and execute a plan. They inspect plots, operation forms, navigation, settings, and narrow-window scrolling. |
| Rendering | The native renderer keeps its sandbox enabled. Local fonts and plot pixels pass. The renderer reports no console errors. |
| Complete journey | A synthetic investigation creates review records and a changed-parameter branch. Exact execution requests remain idempotent. |
| Numerical reproduction | A second empty workspace repeats ten measurements with matching runtime versions and no numerical differences. |
| Recovery | Data-only backup restores records and results into a third workspace. Access credentials rotate. The original workspace stays available. |
| Migration | Startup creates a backup before pending migrations. Restoring the earlier schema permits forward migration with regenerated credentials. |
| Package integrity | The file list, file sizes, SHA-256 hashes, and internal symbolic links match `BUILD.json`. |

The [engineering report](evidence/product-check.json) retains command results, package identities, and check summaries.
The [investigation screenshot](evidence/investigation.png) shows synthetic engineering evidence in the native interface.
The [settings screenshot](evidence/settings.png) shows the storage section.
The [login screenshot](evidence/login.png) shows desktop workspace access.
The [provider screenshot](evidence/provider-login.png) shows provider login before an investigation exists.
The [login report](evidence/login-check.json) records the login and settings checks.
The [provider report](evidence/providers-check.json) records both provider integrations and their limits.
The [provider welcome screen](evidence/providers-welcome.png) offers both accounts.
The [Anthropic sign-in screen](evidence/anthropic-login.png) includes browser return and fallback code controls.
The initial [P0 report](P0.md) remains separate historical evidence.

## Environment

The build targets Ubuntu 24.04 amd64 with glibc 2.39.
The runtime includes Python 3.12.14, PostgreSQL 18.6, Electron 45.0.0, Codex 0.164.0, Claude Code 2.1.305, and Ubuntu Bubblewrap 0.9.0-1ubuntu0.3.
The isolated tool checks use the `gpt-5.4` and `sonnet` selectors.
The other Claude selectors use the same restricted tool configuration.
No check sends a request to a real model account.

The isolated check uses an Ubuntu userspace filesystem on the host kernel.
It hides host files, private repositories, and system Python, Node.js, PostgreSQL, Docker, and Kubernetes commands.
The check disables external network access.
A local fake provider supplies fixed agent responses without an account, credentials, or model charges.
Xvfb supplies the virtual screen.
This environment is not a booted Ubuntu installation.

A read-only MAST metadata query found the expected public WASP-18 sector 2 product.
Acquisition transfer checks use local fixtures for interruption, file integrity, size limits, and duplicate handling.
These checks do not establish live download reliability across archive failures or long sessions.

## Remaining acceptance requirements

| Requirement | Remaining evidence |
|---|---|
| Fresh Ubuntu installation | Install and remove the Debian package under the normal Ubuntu desktop, AppArmor policy, secret service, and session lifecycle. |
| Provider account access | Complete real OpenAI and Anthropic account approval. Check entitlement, expiration, interruption, and reconnection with the account owner. |
| Credential store | Check operating-system credential persistence and removal on the supported desktop. Memory-only isolation already has engineering coverage. |
| Interface acceptance | Complete Richard's design review and check the complete journey without test automation. |
| External usability | Six to ten representative users complete installation, investigation, recovery, and reproduction tasks. Record assistance and failure reasons. |
| Independent installation | Repeat an exported numerical result on a separate supported installation. Existing checks use separate workspaces on one host. |
| Resource envelope | Measure large selections, sustained storage pressure, sleep recovery, and application resource use on representative hardware. |
| Distribution review | Complete redistribution and source-offer review for every bundled dependency before public binary publication. |
| Scientific acceptance | Complete the applicable scientific protocols before claims about completeness, false alarms, physical parameters, or planet confirmation. |

The preview supports guided and exploratory investigations.
Its explicit standalone policy requires approved investigation scope for agents.
It does not provide private evaluation cohorts or replace the research cohort register.
The default server policy still refuses agent access when its required cohort register is absent.
The k3s deployment remains separate.

## Reproduction of engineering checks

[README.md](README.md#checks) gives the executable checks and their inputs.
[CHECKS.md](../CHECKS.md#desktop-preview-checks) defines their coverage within the workspace.
The checks preserve prior experiment records and do not start a scientific evaluation.
