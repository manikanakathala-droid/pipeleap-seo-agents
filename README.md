# pipeleap-seo-agents

Modular SEO agent library for Pipeleap. Contains all engines, connectors, and utilities used by the SEO automation system.

## Structure

```
pipeleap-seo-agents/
├── agents/              # High-level orchestration agents
│   ├── seo_orchestrator.py   # Main SEO pipeline coordinator (12 stages)
│   ├── content_agent.py      # Quality-gated asset selector
│   └── growth_agent.py       # Growth plan translator
├── core/                # Core SEO engines
│   ├── keyword_engine.py     # Keyword discovery & clustering
│   ├── content_engine.py     # Content generation & briefs
│   ├── blog_content_engine.py
│   ├── landing_page_engine.py
│   ├── linking_engine.py     # Internal linking recommendations
│   ├── backlink_engine.py    # Backlink opportunity discovery
│   ├── audit_engine.py       # Technical SEO audits
│   └── analytics_engine.py   # Analytics integration
├── connectors/          # External API integrations
│   ├── gsc_connector.py      # Google Search Console
│   ├── crawler.py            # Site crawler
│   ├── cms_connector.py      # CMS / filesystem publishing
│   ├── indexing_accelerator.py
│   ├── indexnow_connector.py
│   ├── search_engine_submitter.py
│   ├── post_publish_hook.py
│   ├── backlink_executor.py
│   └── api_backlinks.py      # Platform API backlink publisher
├── geo_agent/           # Generative Engine Optimization agent
│   ├── geo_orchestrator.py
│   ├── connectors/
│   ├── engines/
│   └── generators/
├── modules/             # Advanced growth engine module
│   └── pipeleap_seo_engine/
│       ├── orchestrator.py
│       ├── connectors/
│       ├── data/         # Competitors, personas, use cases, integrations
│       ├── engines/      # 15 analysis engines
│       └── generators/   # 13 page type generators
└── utils/               # Shared utilities
    ├── config_loader.py
    ├── models.py
    ├── storage.py
    ├── logger.py
    ├── telemetry.py
    ├── intent_classifier.py
    ├── ranking_model.py
    ├── scoring.py
    ├── text.py
    └── stage_messaging.py
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys in .env
```

## Agents

| Agent | Entry point | Description |
|-------|-------------|-------------|
| SEO Orchestrator | `agents/seo_orchestrator.py` | 12-stage SEO pipeline |
| Growth Engine | `modules/pipeleap_seo_engine/orchestrator.py` | Competitive content generation |
| GEO Agent | `geo_agent/geo_orchestrator.py` | AI Overview & citation optimization |

All API integrations (GSC, DataForSEO, PageSpeed, Ahrefs) are optional — the system degrades gracefully when credentials are absent.

## Deployment

This library is consumed by [pipeleap-seo-workflows](https://github.com/manikanakathala-droid/pipeleap-seo-workflows), which provides the CI/CD pipelines and entry points.
