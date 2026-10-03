# AGENTS.md

Home Assistant OS setup for a Raspberry Pi 4 hub, plus Home Assistant apps.
Setup, commands and known breaks for agents: [AGENT-SETUP.md](AGENT-SETUP.md).

## Layout

- `oled_status/`: the OLED Status Home Assistant app. `config.yaml` and
  `Dockerfile` are what the Supervisor reads; the Python package is
  `oled_status/src/oled_status`. Pages live in `pages/`, one `Page` per screen.
- `tests/oled_status/`: pytest, mirroring the package.
- `ha-os/boot/`: boot partition settings; `scripts/`: card and setup scripts.
- `ha-config/`: Home Assistant configuration recorded from the hub (for
  example automations), for reference and rebuilds.
- `docs/`: people-facing docs, hub `docs/readme.md`.

## Rules

- Commands live in `package.json` scripts; editor and agent surfaces only call
  them. `pnpm verify` must pass before a pull request.
- Python here because the display stack (Pillow, luma.oled, I2C) is Python;
  TypeScript is the house default elsewhere. Typed, `mypy --strict`, ruff.
- Home Assistant app options (`config.yaml` `options` and `schema`) are the
  configuration surface. Keep `settings.py`, `config.yaml`,
  `translations/en.yaml` and `DOCS.md` in step when an option changes.
- Every source file carries the FCL-1.0-MIT header (`pnpm house:fix`). ASCII
  hyphens only; no en or em dashes.
- Real Home Assistant entity IDs are fine in the repo, including in
  `ha-config/`, so recorded automations can be pasted onto the hub as they
  are. Still no addresses, account emails, phone numbers, device serials,
  IP addresses or tokens; refer to people in prose by role ("partner").
- Read library source rather than guessing APIs. luma.core and luma.oled are
  plain Python, readable after setup under
  `.venv/lib/python3.*/site-packages/luma/`, so they are not vendored into
  `externals/`. Vendor with `git subtree --squash` under `externals/` if a
  dependency ever ships only compiled or minified code.
- Version control uses GitButler (`but`). Commits: `type(scope): summary`.
