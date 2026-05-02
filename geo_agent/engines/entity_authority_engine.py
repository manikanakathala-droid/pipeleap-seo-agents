"""
Entity Authority Engine — builds and tracks Pipeleap's entity signals.

LLMs recognize brands as citable entities based on:
  1. Consistent structured data (Organization, SoftwareApplication schema)
  2. sameAs links to trusted directories (LinkedIn, G2, Crunchbase)
  3. knowsAbout declarations matching query topics
  4. Cross-web citation consistency (same name, URL, description everywhere)
  5. Wikipedia/Wikidata presence (highest LLM entity weight)

This engine audits current signals, scores entity authority, and generates
the structured data payloads needed to strengthen entity recognition.
"""
from __future__ import annotations

from typing import Any

from geo_agent.data.geo_entities import PIPELEAP_ENTITY
from geo_agent.data.ai_source_sites import AI_SOURCE_SITES, citation_score
from geo_agent.models import EntitySignal

SITE_URL = "https://pipeleap.com"


class EntityAuthorityEngine:
    """
    Audits and strengthens Pipeleap's entity authority for AI engine recognition.
    """

    def audit(self) -> dict[str, Any]:
        """
        Run full entity authority audit.
        Returns scores, gaps, and recommended schema payloads.
        """
        same_as_score   = self._score_same_as()
        schema_score    = self._score_schema_completeness()
        citation_s      = citation_score()
        knowledge_score = self._score_knowledge_graph_signals()

        overall = round((same_as_score + schema_score + citation_s + knowledge_score) / 4, 1)

        return {
            "overall_entity_score": overall,
            "same_as_score":        same_as_score,
            "schema_score":         schema_score,
            "citation_score":       citation_s,
            "knowledge_graph_score":knowledge_score,
            "gaps":                 self._identify_gaps(),
            "schema_payloads":      self.generate_schema_payloads(),
            "recommendations":      self._recommendations(overall),
        }

    def generate_schema_payloads(self) -> list[dict[str, Any]]:
        """Return all schema objects to inject across Pipeleap pages."""
        return [
            self._organization_schema(),
            self._software_application_schema(),
            self._website_schema(),
            self._defined_term_set_schema(),
        ]

    def entity_signals(self) -> list[EntitySignal]:
        """Return all entity signals with current status."""
        signals = []
        # sameAs link signals
        same_as_urls = PIPELEAP_ENTITY.get("sameAs", [])
        for url in same_as_urls:
            platform = url.split("/")[2].replace("www.", "")
            signals.append(EntitySignal(
                signal_type="sameAs_link",
                platform=platform,
                url=url,
                description=f"sameAs declaration linking Pipeleap to {platform}",
                status="active",
                impact_score=0.8,
                implementation_effort="low",
            ))

        # Directory listing signals from AI source sites
        for site in AI_SOURCE_SITES:
            if site["status"] in ("not_listed", "not_mentioned", "not_present"):
                signals.append(EntitySignal(
                    signal_type="external_mention",
                    platform=site["site"],
                    url=site["url"],
                    description=site["why"],
                    status="missing",
                    impact_score=site["citation_weight"] / 10,
                    implementation_effort="medium",
                ))

        # Wikipedia/Wikidata (highest weight, currently missing)
        signals.append(EntitySignal(
            signal_type="knowledge_graph",
            platform="Wikipedia",
            url="https://en.wikipedia.org/wiki/Pipeleap",
            description="Wikipedia article provides highest-weight LLM entity recognition signal",
            status="missing",
            impact_score=1.0,
            implementation_effort="high",
        ))
        signals.append(EntitySignal(
            signal_type="knowledge_graph",
            platform="Wikidata",
            url="https://www.wikidata.org/",
            description="Wikidata entity record strengthens Knowledge Graph presence",
            status="missing",
            impact_score=0.9,
            implementation_effort="medium",
        ))

        return sorted(signals, key=lambda s: s.impact_score, reverse=True)

    # ── Schema payloads ────────────────────────────────────────────────────────

    def _organization_schema(self) -> dict:
        return {
            "@context": "https://schema.org",
            "@type": "Organization",
            "@id": f"{SITE_URL}/#organization",
            "name": PIPELEAP_ENTITY["name"],
            "url": SITE_URL,
            "logo": {
                "@type": "ImageObject",
                "url": f"{SITE_URL}/favicon.png",
                "width": 512, "height": 512,
            },
            "description": PIPELEAP_ENTITY["one_line"],
            "knowsAbout": PIPELEAP_ENTITY["knowsAbout"],
            "sameAs": PIPELEAP_ENTITY["sameAs"],
            "contactPoint": {
                "@type": "ContactPoint",
                "contactType": "sales",
                "url": f"{SITE_URL}/contact",
                "availableLanguage": "English",
            },
            "foundingDate": "2024",
            "areaServed": "Worldwide",
            "audience": {
                "@type": "Audience",
                "audienceType": "SaaS Organizations, B2B Sales Teams, RevOps Teams",
            },
        }

    def _software_application_schema(self) -> dict:
        return {
            "@context": "https://schema.org",
            "@type": "SoftwareApplication",
            "@id": f"{SITE_URL}/#software",
            "name": "Pipeleap",
            "applicationCategory": "BusinessApplication",
            "applicationSubCategory": "Sales Automation, Workflow Orchestration",
            "operatingSystem": "Web",
            "url": SITE_URL,
            "description": PIPELEAP_ENTITY["one_line"],
            "featureList": PIPELEAP_ENTITY["differentiators"],
            "offers": {
                "@type": "Offer",
                "priceCurrency": "USD",
                "url": f"{SITE_URL}/pricing",
            },
            "publisher": {"@type": "Organization", "@id": f"{SITE_URL}/#organization"},
            "softwareVersion": "2.0",
            "releaseNotes": f"{SITE_URL}/how-it-works",
        }

    def _website_schema(self) -> dict:
        return {
            "@context": "https://schema.org",
            "@type": "WebSite",
            "@id": f"{SITE_URL}/#website",
            "url": SITE_URL,
            "name": "Pipeleap",
            "description": PIPELEAP_ENTITY["one_line"],
            "publisher": {"@type": "Organization", "@id": f"{SITE_URL}/#organization"},
            "potentialAction": {
                "@type": "SearchAction",
                "target": {"@type": "EntryPoint", "urlTemplate": f"{SITE_URL}/blog?q={{search_term_string}}"},
                "query-input": "required name=search_term_string",
            },
        }

    def _defined_term_set_schema(self) -> dict:
        return {
            "@context": "https://schema.org",
            "@type": "DefinedTermSet",
            "@id": f"{SITE_URL}/glossary#termset",
            "name": "Pipeleap SaaS Outbound & Workflow Automation Glossary",
            "url": f"{SITE_URL}/glossary",
            "description": "Authoritative definitions of outbound sales automation, workflow orchestration, and pipeline generation for SaaS teams.",
            "publisher": {"@type": "Organization", "@id": f"{SITE_URL}/#organization"},
        }

    # ── Scoring ────────────────────────────────────────────────────────────────

    def _score_same_as(self) -> float:
        active = len(PIPELEAP_ENTITY.get("sameAs", []))
        return min(100, active * 15)  # 15 points per sameAs link, max 100

    def _score_schema_completeness(self) -> float:
        required = ["Organization", "SoftwareApplication", "WebSite", "DefinedTermSet"]
        # All four are now implemented
        return 80.0  # 80/100 — missing aggregateRating (needs G2 reviews first)

    def _score_knowledge_graph_signals(self) -> float:
        # Currently: LinkedIn + Product Hunt listed = 2 × 15 = 30
        listed_high_authority = sum(
            1 for s in AI_SOURCE_SITES
            if s["status"] == "listed" and s.get("citation_weight", 0) >= 7
        )
        return min(100, listed_high_authority * 15)

    def _identify_gaps(self) -> list[str]:
        gaps = []
        if citation_score() < 50:
            gaps.append(f"Citation score {citation_score()}/100 — need G2, Capterra, TrustRadius listings")
        if not any(s["site"] == "G2" and s["status"] == "listed" for s in AI_SOURCE_SITES):
            gaps.append("G2 listing missing — highest-weight LLM citation source for tool comparisons")
        if not any(s["site"] == "Capterra" and s["status"] == "listed" for s in AI_SOURCE_SITES):
            gaps.append("Capterra listing missing — critical for 'best X tools' AI recommendations")
        if self._score_knowledge_graph_signals() < 30:
            gaps.append("Wikipedia/Wikidata entity missing — adds highest LLM training weight")
        if len(PIPELEAP_ENTITY.get("sameAs", [])) < 5:
            gaps.append(f"Only {len(PIPELEAP_ENTITY.get('sameAs', []))} sameAs links — target 8+")
        return gaps

    def _recommendations(self, overall_score: float) -> list[str]:
        recs = []
        if overall_score < 30:
            recs.append("CRITICAL: Create G2 and Capterra listings immediately — these are the #1 LLM citation sources for SaaS tools")
        if overall_score < 50:
            recs.append("Add Pipeleap to StackShare, AlternativeTo, and Crunchbase")
            recs.append("Publish guest articles on Sales Hacker and HubSpot Blog with Pipeleap references")
        if overall_score < 70:
            recs.append("Answer Quora questions about outbound automation with Pipeleap context")
            recs.append("Expand sameAs links to include G2, Capterra, Crunchbase once listed")
        recs.append("Create Wikipedia article once 3+ independent editorial sources exist")
        return recs
