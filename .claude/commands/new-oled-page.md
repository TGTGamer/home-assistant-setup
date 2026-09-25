Add a new page to the OLED Status app: $ARGUMENTS

1. Read `oled_status/src/oled_status/pages/common.py` for the `Page` and `Frame` contract and the drawing helpers.
2. If the page needs new data, add it to `Snapshot` in `snapshot.py`, read it in `build()`, and add an option in `settings.py`, `oled_status/config.yaml` (options and schema), `oled_status/translations/en.yaml` and `oled_status/DOCS.md`.
3. Define the page in `pages/house.py` or `pages/ambient.py` with a `relevant` check so it hides when it has nothing to show, and register it in that module's `PAGES`.
4. Add the page name to `DEFAULT_PAGES` and the `pages` list in `config.yaml` if it should be on by default, and give it sample data in `preview.py`.
5. Add tests under `tests/oled_status/`, run `pnpm preview` and look at the PNG, then `pnpm verify`.
