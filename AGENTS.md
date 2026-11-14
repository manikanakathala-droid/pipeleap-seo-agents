# Current system (read this first)

## Growth loop retired

The automated Pipeleap growth loop was retired on November 14, 2026. Its GitHub Actions workflow has been removed, and `run_growth_loop.py` now exits with a retirement notice. The remaining `growth/` modules, `growth.yaml`, tests and `growth_state/` files are kept as archival reference only; do not run or reactivate them.

The workflow no longer drafts pages, writes site changes, pushes branches, or submits changed URLs to search engines. The site itself remains a separate static HTML project in `manikanakathala-droid/Pipeleap-web-redesign`.


All code, data, workflows and secrets for the previous Pipeleap website were removed from this repository on November 14, 2026. The only connectors left are `connectors/gsc_connector.py` and `connectors/ga4_connector.py`, which the archived `growth/measure.py` imports.
