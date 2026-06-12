from __future__ import annotations

"""
Static strategy data for the SERP visibility agent.

Covers all 7 pillars:
  1. SERP snippet optimization targets
  2. Breadcrumb hierarchy
  3. Keyword demand clusters
  4. Off-page expansion (directories, guests, communities)
  5. GSC action rules
  6. Internal linking cluster map
  7. Authority building tiers
"""

# 1. Page-level meta targets
META_TARGETS: list[dict] = [
    {
        "path": "/",
        "title": "Revenue Operations & Pipeline Automation | Pipeleap",
        "meta_description": (
            "Pipeleap builds and runs your entire revenue engine - 11 connected modules "
            "covering ICP scoring, personalised outreach, and CRM handoff. Zero manual setup."
        ),
    },
    {
        "path": "/about",
        "title": "About Pipeleap - Sales Operations Platform",
        "meta_description": (
            "Pipeleap is a sales operations platform that orchestrates CRM, enrichment, and execution. "
            "No tool sprawl, no setup Saturdays. One working engine that gets smarter over time."
        ),
    },
    {
        "path": "/sales-ops-audit",
        "title": "Free Sales Ops Audit | Pipeleap",
        "meta_description": (
            "Get a full audit of your sales operations - targeting, messaging, workflows, and "
            "pipeline health. Identify what is broken and get a fix plan in under 2 weeks."
        ),
    },
    {
        "path": "/faq",
        "title": "Revenue Operations FAQ - Pipeleap",
        "meta_description": (
            "Answers to common questions about how Pipeleap builds, deploys, and operates "
            "revenue systems for B2B teams."
        ),
    },
    {
        "path": "/pricing",
        "title": "Revenue Operations Pricing | Pipeleap",
        "meta_description": (
            "Pipeleap pricing for sales operations platform. "
            "No seat licences, no duct tape."
        ),
    },
]

# 2. High-CTR headline variants
CTR_VARIANTS: list[dict] = [
    {"intent": "problem_aware",  "headline": "Why Your Sales Stack Is Not Working (And How to Fix It)"},
    {"intent": "outcome_driven", "headline": "How to Get 3x More Meetings Without Hiring More Reps"},
    {"intent": "urgency",        "headline": "Your Sales Reps Are Spending 65% of Their Day on Admin. Stop It."},
    {"intent": "curiosity",      "headline": "The 11 Modules Every Revenue Engine Needs (Most Teams Have 3)"},
]

# 3. FAQ topics for Google rich results
FAQ_RICH_RESULT_TOPICS: list[str] = [
    "What is revenue operations?",
    "How long does it take to build a working revenue system?",
    "What is a sales ops audit and why does it matter?",
    "What is ICP scoring in sales?",
    "How does AI personalisation improve reply rates in cold outreach?",
    "What is the difference between a sales engagement platform and a sales operations platform?",
    "How many touches does it take to book a B2B sales meeting?",
    "What does a sales operations platform do?",
    "Can sales workflows be fully automated?",
    "How do I fix an unpredictable sales pipeline?",
]

# 4. Keyword clusters
SERP_KEYWORD_CLUSTERS: list[dict] = [
    {
        "cluster_name": "problem_pain",
        "intent": "informational",
        "funnel_stage": "awareness",
        "conversion_probability": 0.62,
        "business_fit": 0.87,
        "estimated_difficulty": 28.0,
        "speed_to_rank_score": 0.78,
        "keywords": [
            "why is my sales pipeline not working",
            "sales reps spending too much time on admin",
            "pipeline not predictable",
            "how to fix sales process",
            "sales not generating leads",
        ],
    },
    {
        "cluster_name": "solution_evaluation",
        "intent": "commercial",
        "funnel_stage": "consideration",
        "conversion_probability": 0.85,
        "business_fit": 0.95,
        "estimated_difficulty": 46.0,
        "speed_to_rank_score": 0.55,
        "keywords": [
            "sales operations platform",
            "best AI sales tools 2026",
            "sales workflow automation software",
        ],
    },
    {
        "cluster_name": "how_to",
        "intent": "informational",
        "funnel_stage": "awareness",
        "conversion_probability": 0.58,
        "business_fit": 0.84,
        "estimated_difficulty": 32.0,
        "speed_to_rank_score": 0.72,
        "keywords": [
            "how to build a revenue system",
            "how to automate B2B prospecting",
            "how to write cold outreach that gets replies",
            "how to do a sales ops audit",
            "what is sales orchestration",
            "how to build predictable pipeline",
        ],
    },
    {
        "cluster_name": "broad_category",
        "intent": "commercial",
        "funnel_stage": "awareness",
        "conversion_probability": 0.45,
        "business_fit": 0.90,
        "estimated_difficulty": 65.0,
        "speed_to_rank_score": 0.35,
        "keywords": [
            "sales productivity",
            "sales automation",
            "pipeline generation",
            "workflow orchestration",
            "lead enrichment",
            "crm automation",
            "sales workflow",
            "sales operations",
        ],
    },
    {
        "cluster_name": "brand_navigational",
        "intent": "navigational",
        "funnel_stage": "decision",
        "conversion_probability": 0.95,
        "business_fit": 1.0,
        "estimated_difficulty": 5.0,
        "speed_to_rank_score": 0.95,
        "keywords": [
            "pipeleap",
            "pipeleap pricing",
            "pipeleap demo",
            "pipeleap login",
            "pipeleap reviews",
        ],
    },
]

# 5. Content plan - 10 blog post briefs
CONTENT_PLAN: list[dict] = [
    {
        "slug": "what-is-sales-orchestration",
        "page_type": "blog_post",
        "title": "What Is Sales Orchestration? (And Why Point Tools Do Not Do It)",
        "seo_title": "What Is Sales Orchestration? Definition, Examples, and Tools",
        "meta_description": (
            "Sales orchestration connects every revenue motion into one coordinated system. "
            "Learn what it is, how it differs from automation, and why it matters for pipeline."
        ),
        "target_keyword": "what is sales orchestration",
        "cluster": "how_to",
        "pillar_link": "/about",
        "internal_links": ["/about", "/glossary/outbound-sales"],
        "persona": "RevOps leader unfamiliar with orchestration",
        "eeat_notes": [
            "Include diagram: point tools vs orchestrated system",
            "Contrast with sales engagement platforms",
        ],
    },
    {
        "slug": "how-to-run-sales-ops-audit",
        "page_type": "blog_post",
        "title": "How to Run a Sales Ops Audit in 5 Steps",
        "seo_title": "How to Run a Sales Ops Audit: 5-Step Framework",
        "meta_description": (
            "A sales ops audit identifies exactly where your pipeline is leaking. Follow this 5-step "
            "framework to audit targeting, messaging, workflows, and pipeline health."
        ),
        "target_keyword": "how to do a sales ops audit",
        "cluster": "how_to",
        "pillar_link": "/sales-ops-audit",
        "internal_links": ["/sales-ops-audit", "/glossary/icp-scoring"],
        "persona": "Head of Sales who suspects pipeline is underperforming",
        "eeat_notes": [
            "Include inline audit checklist",
            "Add real signals that indicate an audit is overdue",
        ],
    },
    {
        "slug": "predictable-pipeline-without-sdrs",
        "page_type": "blog_post",
        "title": "How to Build Predictable Pipeline Without Hiring More SDRs",
        "seo_title": "How to Build Predictable Pipeline Without Hiring More SDRs | Pipeleap",
        "meta_description": (
            "Most companies hire SDRs to fix a pipeline problem that is actually a systems problem. "
            "Here is how to build predictable pipeline through automation instead."
        ),
        "target_keyword": "predictable pipeline",
        "cluster": "solution_evaluation",
        "pillar_link": "/",
        "internal_links": ["/", "/sales-ops-audit"],
        "persona": "Founder frustrated with headcount not delivering pipeline results",
        "eeat_notes": [
            "Open with cost of SDR hire vs automation ROI",
            "Include pipeline model showing how automation compounds over time",
        ],
    },
    {
        "slug": "outbound-stack-too-many-tools",
        "page_type": "blog_post",
        "title": "Why Your Sales Stack Has Too Many Tools and Not Enough Pipeline",
        "seo_title": "Too Many Sales Tools, Not Enough Pipeline | Pipeleap",
        "meta_description": (
            "Adding more tools does not fix pipeline problems. Here is why fragmented stacks fail and "
            "what a unified revenue engine looks like instead."
        ),
        "target_keyword": "sales stack",
        "cluster": "problem_pain",
        "pillar_link": "/",
        "internal_links": ["/", "/about"],
        "persona": "RevOps leader drowning in tool sprawl",
        "eeat_notes": [
            "Lead with stat: average B2B sales stack has 10+ tools",
            "Show the integration tax: each connector equals maintenance debt",
        ],
    },
    {
        "slug": "icp-scoring-guide",
        "page_type": "blog_post",
        "title": "ICP Scoring 101: How to Stop Wasting Cold Outreach on the Wrong Leads",
        "seo_title": "ICP Scoring Guide for B2B Sales Teams | Pipeleap",
        "meta_description": (
            "ICP scoring tells you who to reach out to first. Learn how to build a scoring model "
            "that filters noise and sends outreach only to accounts most likely to convert."
        ),
        "target_keyword": "ICP scoring",
        "cluster": "how_to",
        "pillar_link": "/glossary/icp-scoring",
        "internal_links": ["/glossary/icp-scoring", "/sales-ops-audit"],
        "persona": "SDR manager or RevOps analyst building lead qualification",
        "eeat_notes": [
            "Include a sample scoring rubric with firmographic and behavioural signals",
        ],
    },
    {
        "slug": "ai-personalization-cold-email",
        "page_type": "blog_post",
        "title": "How AI Personalisation Changes Cold Email Reply Rates",
        "seo_title": "AI Personalisation for Cold Email | Pipeleap",
        "meta_description": (
            "Generic cold email is dead. Here is how AI personalisation at scale works, "
            "what it takes to do it without sounding robotic, and what reply rates to expect."
        ),
        "target_keyword": "AI cold email personalisation",
        "cluster": "how_to",
        "pillar_link": "/",
        "internal_links": ["/", "/blog/outbound-stack-too-many-tools"],
        "persona": "SDR leader or founder running cold outreach campaigns",
        "eeat_notes": [
            "Include benchmark reply rates: generic vs personalised",
        ],
    },
    {
        "slug": "cost-of-manual-prospecting",
        "page_type": "blog_post",
        "title": "The Real Cost of Manual Prospecting for B2B Sales Teams",
        "seo_title": "The Real Cost of Manual Prospecting | Pipeleap",
        "meta_description": (
            "Manual prospecting costs more than most sales leaders realise. "
            "Here is what it actually costs in time, rep attention, and missed pipeline."
        ),
        "target_keyword": "manual prospecting cost",
        "cluster": "problem_pain",
        "pillar_link": "/",
        "internal_links": ["/", "/sales-ops-audit"],
        "persona": "Sales leader trying to justify automation investment",
        "eeat_notes": [
            "Build a cost calculator: hours per rep x hourly rate x number of reps",
        ],
    },
    {
        "slug": "11-modules-outbound-engine",
        "page_type": "blog_post",
        "title": "The 11 Modules Every Revenue Engine Needs",
        "seo_title": "The 11 Modules of a Complete Revenue Engine | Pipeleap",
        "meta_description": (
            "Most revenue stacks cover 3 of the 11 modules a complete engine needs. "
            "Here is what the full system looks like and why each module matters."
        ),
        "target_keyword": "revenue engine modules",
        "cluster": "solution_evaluation",
        "pillar_link": "/about",
        "internal_links": ["/about", "/"],
        "persona": "RevOps leader or Head of Sales architecting a revenue system",
        "eeat_notes": [
            "Use the actual Pipeleap 11-module framework as the structure",
        ],
    },
]

# 6. Directory submission queue
DIRECTORY_TARGETS: list[dict] = [
    {"name": "G2",              "url": "https://www.g2.com",             "category": "Revenue Operations",       "priority": 1, "da": 90},
    {"name": "Capterra",        "url": "https://www.capterra.com",       "category": "Revenue Operations Software", "priority": 1, "da": 88},
    {"name": "Clutch.co",       "url": "https://clutch.co",              "category": "Sales Consulting / GTM",    "priority": 1, "da": 82},
    {"name": "Product Hunt",    "url": "https://www.producthunt.com",    "category": "Full product launch",       "priority": 1, "da": 90},
    {"name": "Trustpilot",      "url": "https://www.trustpilot.com",     "category": "Business Services",         "priority": 2, "da": 92},
    {"name": "GetApp",          "url": "https://www.getapp.com",         "category": "Revenue Operations Software", "priority": 2, "da": 84},
    {"name": "Software Advice", "url": "https://www.softwareadvice.com", "category": "Revenue Operations",          "priority": 2, "da": 80},
    {"name": "Futurepedia",     "url": "https://www.futurepedia.io",     "category": "Revenue Operations AI",       "priority": 2, "da": 55},
    {"name": "SourceForge",     "url": "https://sourceforge.net",        "category": "Revenue Software",            "priority": 3, "da": 82},
    {"name": "Indie Hackers",   "url": "https://www.indiehackers.com",   "category": "Founder story",             "priority": 3, "da": 74},
]

# 7. Guest post targets
GUEST_POST_TARGETS: list[dict] = [
    {
        "publication": "Sales Hacker",
        "url": "https://www.saleshacker.com",
        "da": 76,
        "pitch_angle": "The Death of the Point-Tool Stack: Why Managed Revenue Operations Is Winning",
        "contact": "contributors@saleshacker.com",
    },
    {
        "publication": "HubSpot Blog",
        "url": "https://blog.hubspot.com",
        "da": 93,
        "pitch_angle": "How B2B Teams Are Using AI to Automate Revenue Operations at Scale",
        "contact": "https://blog.hubspot.com/marketing/guest-blogging-guidelines",
    },
    {
        "publication": "G2 Learning Hub",
        "url": "https://learn.g2.com",
        "da": 90,
        "pitch_angle": "Revenue Operations: A Practical Guide for B2B Teams",
        "contact": "content@g2.com",
    },
    {
        "publication": "Demand Gen Report",
        "url": "https://www.demandgenreport.com",
        "da": 68,
        "pitch_angle": "GTM Implementation in 2025: What Has Changed and What Has Not",
        "contact": "editorial@demandgenreport.com",
    },
    {
        "publication": "Close.com Blog",
        "url": "https://www.close.com/blog",
        "da": 72,
        "pitch_angle": "How to Automate Prospecting Without Losing the Human Element",
        "contact": "https://www.close.com/blog/write-for-us",
    },
    {
        "publication": "Predictable Revenue",
        "url": "https://predictablerevenue.com",
        "da": 66,
        "pitch_angle": "Why Revenue Operations Compounds: The Case for a Managed Engine",
        "contact": "hello@predictablerevenue.com",
    },
]

# 8. Internal linking cluster map
LINKING_CLUSTERS: list[dict] = [
    {
        "cluster": "Revenue Operations",
        "pillar_page": "/",
        "spoke_articles": [
            "/blog/ai-personalization-cold-email",
            "/blog/cost-of-manual-prospecting",
            "/blog/outbound-stack-too-many-tools",
            "/blog/predictable-pipeline-without-sdrs",
        ],
        "glossary_links": ["/glossary/sales-automation"],
    },
    {
        "cluster": "Sales Orchestration",
        "pillar_page": "/about",
        "spoke_articles": [
            "/blog/what-is-sales-orchestration",
            "/blog/11-modules-outbound-engine",
        ],
        "glossary_links": ["/glossary/sales-orchestration"],
    },
]

# 9. LinkedIn content cadence
LINKEDIN_CADENCE: dict = {
    "author": "Rajiv Maanik",
    "frequency": "2x per week",
    "slots": [
        {
            "day": "Monday",
            "format": "insight",
            "prompt_template": (
                "Share one non-obvious observation about sales operations. "
                "Open with a counter-intuitive statement. "
                "End: Pipeleap runs the entire system for sales teams. Link in bio."
            ),
        },
        {
            "day": "Thursday",
            "format": "system_or_howto",
            "prompt_template": (
                "Share an exact playbook or internal sequence Pipeleap uses. "
                "Be specific: step numbers, tool names, outcomes. "
                "CTA: Deploys in 2 to 4 weeks. DM me if you want to see it."
            ),
        },
    ],
    "newsletter_name": "The Pipeline Letter",
    "newsletter_frequency": "weekly",
}

# 10. Authority tiers
AUTHORITY_TIERS: list[dict] = [
    {
        "tier": 1,
        "label": "High-value, high-effort",
        "tactics": [
            "Sales Hacker guest post",
            "LinkedIn Pulse article by Rajeev",
            "Podcast: 30 Minutes to Presidents Club, The Sales Evangelist, Make It Happen Mondays",
            "Product Hunt full launch",
            "Clutch client reviews leading to editorial coverage",
        ],
    },
    {
        "tier": 2,
        "label": "Medium-effort, fast results",
        "tactics": [
            "HARO / Connectively daily responses for sales, AI, GTM queries",
            "LinkedIn Newsletter: The Pipeline Letter",
            "Partner co-marketing with Clay, Apollo, HubSpot for directory mentions",
        ],
    },
    {
        "tier": 3,
        "label": "Low-effort, compound over time",
        "tactics": [
            "Consistent NAP across all directories",
            "Engage on high-traffic LinkedIn posts in sales and GTM",
            "Natural brand mentions in r/sales, RevOps Co-op Slack, Quora",
        ],
    },
]

# 11. GSC CTR improvement rules
GSC_CTR_RULES: list[dict] = [
    {
        "rule": "high_impression_low_ctr",
        "condition": "impressions > 100 and ctr < 0.03",
        "action": (
            "Identify top query driving impressions. Rewrite meta description to match "
            "that query intent precisely. Add keyword phrase to H1 or opening paragraph."
        ),
    },
    {
        "rule": "page_two_opportunity",
        "condition": "average_position >= 11 and average_position <= 20",
        "action": (
            "Publish a supporting blog post targeting the same query cluster. "
            "Add internal link from that post to the ranking page with exact-match anchor."
        ),
    },
    {
        "rule": "rich_result_eligible",
        "condition": "page_has_faq_content and not faq_schema_present",
        "action": (
            "Add FAQPage JSON-LD schema to the page. Ensure each answer is a "
            "standalone paragraph with no CTA-only text and no navigation links."
        ),
    },
]

# 12. Brand monitoring
BRAND_MONITORING_QUERIES: list[str] = [
    "Pipeleap",
    "pipeleap.com",
]

BACKLINK_ANCHOR_VARIANTS: list[str] = [
    "sales operations platform",
    "Pipeleap",
    "sales orchestration platform",
]
