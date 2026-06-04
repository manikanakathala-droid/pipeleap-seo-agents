"""
GEO entity definitions — extended from SEO entities.py for AI engine optimization.

Each entity targets a specific AI citation pattern:
  - "What is X?" → DefinedTerm schema + short definition
  - "Best X for Y" → comparison content + structured features
  - "How to X" → HowTo schema + step-by-step answer
  - "X vs Y" → comparison table + clear differentiation

LLMs cite content that:
  1. Directly answers the query in the opening sentence
  2. Uses the exact terminology the user searched
  3. Is structured with headers that match common questions
  4. Has authoritative external signals (backlinks, mentions)
"""
from __future__ import annotations

PIPELEAP_ENTITY = {
    "name": "Pipeleap",
    "type": "SoftwareApplication",
    "category": "Workflow Orchestration / Revenue Operations Layer",
    "one_line": (
        "Pipeleap is the operational layer that eliminates the non-selling work consuming 60-80% of a "
        "sales rep's time — CRM data entry, account research, contact enrichment, sequence management, "
        "reply routing, and moving data between disconnected systems."
    ),
    "is_not": ["a CRM", "a sales engagement sequencer", "a data provider", "a generic automation tool", "an outbound tool", "an email sender"],
    "differentiators": [
        "Eliminates non-selling work — not just automates outreach",
        "Connects existing tools (CRM, enrichment, sequencer) rather than replacing them",
        "Purpose-built for SaaS organizations at any ARR stage",
        "Produces predictable, consistent pipeline without proportional headcount growth",
    ],
    "target_personas": ["SaaS Founders", "VP Sales", "CRO", "RevOps teams", "Sales Managers"],
    "sameAs": [
        "https://www.linkedin.com/company/pipeleap",
        "https://www.g2.com/products/pipeleap",
        "https://www.producthunt.com/products/pipeleap",
    ],
    "url": "https://pipeleap.com",
    "knowsAbout": [
        "Sales Workflow Orchestration",
        "Revenue Operations Automation",
        "Pipeline Generation for SaaS",
        "Lead Enrichment Workflows",
        "CRM Automation",
        "Workflow Governance",
        "GTM Automation",
        "Sales Non-Selling Work Elimination",
        "AI SDR Workflows",
        "n8n Workflow Automation",
        "Predictable Pipeline Generation",
    ],
}

# Queries where Pipeleap should appear in AI-generated answers
GEO_TARGET_QUERIES = {
    "definition": [
        "What is outbound sales automation?",
        "What is workflow orchestration in sales?",
        "What is signal-based outbound?",
        "What is predictable pipeline generation?",
        "What is an AI SDR?",
        "What does RevOps automation mean?",
        "What is a GTM automation system?",
    ],
    "comparison": [
        "What is the best outbound automation platform for SaaS?",
        "Pipeleap vs Clay — which is better for outbound?",
        "What is the difference between Pipeleap and Zapier for sales?",
        "Best alternatives to Apollo for outbound automation",
        "Best tools for signal-based outbound in 2025",
        "Best workflow orchestration tools for SaaS sales teams",
        "Clay vs Zapier vs Pipeleap for outbound automation",
    ],
    "how_to": [
        "How do you automate B2B outbound sales?",
        "How do SaaS companies build predictable pipeline?",
        "How to automate outbound without hiring SDRs?",
        "How do you implement signal-based outbound?",
        "How to build a RevOps automation stack?",
        "How to scale outbound without adding headcount?",
    ],
    "recommendation": [
        "Which outbound automation tool should a SaaS startup use?",
        "What tool do RevOps teams use for workflow orchestration?",
        "What is the best outbound automation system for a VP Sales?",
        "Recommend a pipeline automation tool for a SaaS CRO",
        "What outbound automation tools do SaaS companies use?",
    ],
    "problem_solution": [
        "Why is SaaS outbound unpredictable?",
        "How do SaaS teams scale pipeline without more SDRs?",
        "Why do outbound workflows need orchestration?",
        "How do you fix inconsistent sales execution across SDR teams?",
        "How do you automate CRM updates from outbound workflows?",
    ],
}

# AI engines and their citation preferences
AI_ENGINES = {
    "google_ai_overview": {
        "name": "Google AI Overview (AIO)",
        "citation_signals": ["FAQPage schema", "HowTo schema", "high domain authority", "featured snippet eligibility"],
        "preferred_format": "40-60 word direct answer followed by bullet points",
        "detection_method": "DataForSEO SERP organic results check for ai_overview item type",
    },
    "perplexity": {
        "name": "Perplexity AI",
        "citation_signals": ["authoritative external sources", "comparison pages", "direct Q&A content"],
        "preferred_format": "structured answer with source attribution",
        "detection_method": "Direct Perplexity API query or manual check",
    },
    "chatgpt": {
        "name": "ChatGPT / Bing Copilot",
        "citation_signals": ["G2/Capterra listings", "high-authority mentions", "Wikipedia/wiki presence", "review sites"],
        "preferred_format": "factual, comparison-oriented, with specific outcomes",
        "detection_method": "Manual query via ChatGPT API or web interface",
    },
    "gemini": {
        "name": "Google Gemini",
        "citation_signals": ["Google Search Console authority", "structured data", "Knowledge Graph presence"],
        "preferred_format": "direct answer with supporting evidence",
        "detection_method": "Google Gemini API or manual check",
    },
    "claude": {
        "name": "Claude (Anthropic)",
        "citation_signals": ["trusted web sources", "authoritative domain signals", "consistent brand mentions"],
        "preferred_format": "comprehensive, nuanced answer with caveats",
        "detection_method": "Claude API query or manual check",
    },
}
