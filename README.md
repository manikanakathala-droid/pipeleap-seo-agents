# pipeleap-seo-agents

SEO agent library, CI/CD pipelines, and entry points for Pipeleap. Contains all engines, connectors, utilities, workflows, and configuration in a single repository.

## Structure

```
pipeleap-seo-agents/
├── agents/              # High-level orchestration agents
│   ├── seo_orchestrator.py   # Main SEO pipeline coordinator (12 stages)
│   ├── seo_os_agent.py       # Autonomous SEO OS (observe-diff-decide-execute)
│   ├── serp_visibility_agent.py
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
├── geo_agent/           # Generative Engine Optimization agent
├── modules/             # Advanced growth engine module
│   └── pipeleap_seo_engine/
├── utils/               # Shared utilities
├── scripts/             # Validation, auditing, automation scripts
├── .github/workflows/   # CI/CD pipelines
│   ├── daily_seo_run.yml        # SEO + growth engine (daily 12:00 UTC)
│   ├── daily_geo_run.yml        # GEO agent (daily 13:00 UTC)
│   ├── daily_seo_os_run.yml     # SEO OS agent (daily 11:30 UTC)
│   ├── daily_serp_run.yml       # SERP visibility (daily 14:00 UTC)
│   ├── duplicate_audit.yml      # Content deduplication audit
│   ├── validate.yml             # Repository validation on push/PR
│   └── deploy_dashboard.yml     # GitHub Pages dashboard
├── main.py                    # SEO orchestrator entry point
├── run_growth_engine.py       # Growth engine standalone runner
├── run_geo_agent.py           # GEO agent standalone runner
├── run_seo_os.py              # SEO OS agent standalone runner
├── run_serp_visibility.py     # SERP visibility standalone runner
├── config.yaml                # Main SEO agent configuration
├── config_geo.yaml            # GEO agent configuration
├── content/                   # Generated blog and glossary drafts
├── dashboard/                 # Live SEO dashboard data
├── seo/                       # Structured SEO OS outputs
└── requirements.txt           # Python dependencies
```

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env
# Fill in your API keys in .env
```

## Entry Points

| Runner | Command | Description |
|--------|---------|-------------|
| SEO Orchestrator | `python main.py` | 12-stage SEO pipeline |
| Growth Engine | `python run_growth_engine.py` | Competitive content generation |
| GEO Agent | `python run_geo_agent.py` | AI Overview & citation optimization |
| SEO OS Agent | `python run_seo_os.py` | Autonomous SEO execution |
| SERP Visibility | `python run_serp_visibility.py` | SERP monitoring & analysis |

All API integrations (GSC, DataForSEO, PageSpeed, Ahrefs) are optional — the system degrades gracefully when credentials are absent.

## CI/CD

Each workflow runs on a schedule and/or via `workflow_dispatch`. The SEO and GEO workflows check out `pipeleap-launchpad-040053e5` as a publish target and commit generated content directly to it.

### Required GitHub Secrets

| Secret | Required | Description |
|--------|----------|-------------|
| `LAUNCHPAD_DEPLOY_TOKEN` | Yes | GitHub token for pushing to pipeleap-launchpad |
| `GSC_SERVICE_ACCOUNT_JSON` | Yes | Google Search Console service account JSON |
| `DATAFORSEO_LOGIN` | No | DataForSEO API login |
| `DATAFORSEO_PASSWORD` | No | DataForSEO API password |
| `PAGESPEED_API_KEY` | No | Google PageSpeed Insights API key |
| `AHREFS_API_KEY` | No | Ahrefs API key |
| `SUPABASE_SERVICE_ROLE_KEY` | No | Supabase service role key |
| `OPENAI_API_KEY` | No | OpenAI API key (SEO OS) |
| `ANTHROPIC_API_KEY` | No | Anthropic API key (SEO OS) |
| `GH_PAT` | Yes | GitHub personal access token (SEO OS workflows) |
