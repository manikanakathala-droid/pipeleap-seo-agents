# Pipeleap growth loop

A daily loop that grows qualified organic demand for www.pipeleap.com and learns from the results.

```
MEASURE  Search Console + GA4            what happened
LEARN    experiments, cluster beliefs    what worked, and for which kind of buyer
PLAN     guarded action queue            what to do next, and what to hold back
ACT      site foundation + pages         change the site (static HTML repository)
REPORT   funnel briefing                 impressions -> clicks -> sessions -> enquiries
```

```bash
pip install -r requirements-growth.txt
```

```bash
git clone https://github.com/manikanakathala-droid/Pipeleap-web-redesign site
```

```bash
python run_growth_loop.py --site-dir site --dry-run
```

```bash
python -m pytest tests -q
```

- Configuration: `growth.yaml`
- Memory: `growth_state/ledger.json`
- Latest briefing: `growth_state/briefing.md`
- Architecture and rules: `AGENTS.md`

The previous agents (`agents/`, `core/`, `modules/`, `geo_agent/`) targeted a site that no longer exists and are
retired; see `AGENTS.md`.
