# AGENT-SETUP

## Needs
- Linux, macOS or Windows. Python 3.13+ via uv. pnpm 12 (commands only; no node deps).
- No services. Hardware (OLED, I2C) never needed for tests.

## Env
| Var | Req | Source |
|---|---|---|
| `HA_URL` | optional, `pnpm dev` only | Home Assistant base URL, like `http://homeassistant.local:8123` |
| `HA_TOKEN` | optional, `pnpm dev` only | HA long-lived access token (HA profile page); keep in Proton Pass, inject with `pass-cli run` |
| `SUPERVISOR_TOKEN` | never set by hand | Injected by Supervisor inside app |

## Network
- `astral.sh`, `github.com` (uv install)
- `pypi.org`, `files.pythonhosted.org` (deps)
- `ghcr.io` (Docker base image, CI build only)

## Setup
- `scripts/agent-setup.sh` (Windows: `scripts/agent-setup.ps1`). Idempotent.
- Success prints `agent-setup: ok`.

## Run
| Job | Cmd |
|---|---|
| test | `pnpm test` |
| lint | `pnpm lint` |
| types | `pnpm typecheck` |
| headers, dashes | `pnpm house` (fix: `pnpm house:fix`) |
| licences | `pnpm license-check` |
| all | `pnpm verify` |
| previews | `pnpm preview`, PNGs in `previews/` |
| live | `pnpm dev`, needs `HA_URL` `HA_TOKEN`, writes `previews/live.png` |

No ports. No server.

## Verify
- `uv run pytest -q` all pass.

## Runner notes
- Claude Code web: setup script `scripts/agent-setup.sh`; network Trusted plus `astral.sh`.
- Codex cloud: setup and maintenance scripts both `scripts/agent-setup.sh`.
- Cursor cloud: `.cursor/environment.json`.
- Copilot: `.github/workflows/copilot-setup-steps.yml`.
- Orca Quick Commands: `pnpm verify`, `pnpm preview`.

## Breaks
| Break | Cause | Fix |
|---|---|---|
| `uv sync --locked` fails | lock stale | `uv lock`, commit `uv.lock` |
| `house` fails missing header | new file | `pnpm house:fix` |
| `pnpm dev` RuntimeError set SUPERVISOR_TOKEN | no `HA_URL`/`HA_TOKEN` | export both |
| Docker build fails locally | no Docker or not aarch64 | CI builds; or build on Pi via app store |
