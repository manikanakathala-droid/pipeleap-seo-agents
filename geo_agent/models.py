"""GEO agent data models."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class GEOPage:
    """A page generated or optimised by the GEO agent."""
    slug: str
    page_type: str                   # "geo_answer", "comparison_geo", "citation_target", "qa_hub"
    title: str
    meta_description: str
    primary_query: str               # The exact AI-engine query this page targets
    query_category: str              # "definition" | "comparison" | "howto" | "recommendation"
    answer_block: str                # The 40-70 word AI-citation-ready answer
    body_markdown: str
    schema_markup: list[dict[str, Any]] = field(default_factory=list)
    target_ai_engines: list[str] = field(default_factory=list)
    citation_signals: list[str] = field(default_factory=list)
    publish_date: str = ""
    word_count: int = 0

    def __post_init__(self) -> None:
        if not self.publish_date:
            self.publish_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if not self.word_count:
            self.word_count = len(self.body_markdown.split())

    def to_dict(self) -> dict[str, Any]:
        return {
            "slug": self.slug,
            "page_type": self.page_type,
            "title": self.title,
            "meta_description": self.meta_description,
            "primary_query": self.primary_query,
            "query_category": self.query_category,
            "answer_block": self.answer_block,
            "body_markdown": self.body_markdown,
            "schema_markup": self.schema_markup,
            "target_ai_engines": self.target_ai_engines,
            "citation_signals": self.citation_signals,
            "publish_date": self.publish_date,
            "word_count": self.word_count,
        }


@dataclass
class CitationGap:
    """A query where Pipeleap should be cited but isn't."""
    query: str
    query_category: str
    ai_engine: str
    expected_position: str           # "should be cited" | "should be top-3" | "should own"
    current_status: str              # "not_cited" | "partially_cited" | "cited_incorrectly"
    recommended_action: str
    priority_score: float = 0.0
    has_ai_overview: bool = False
    has_paa: bool = False
    search_volume: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "query_category": self.query_category,
            "ai_engine": self.ai_engine,
            "expected_position": self.expected_position,
            "current_status": self.current_status,
            "recommended_action": self.recommended_action,
            "priority_score": self.priority_score,
            "has_ai_overview": self.has_ai_overview,
            "has_paa": self.has_paa,
            "search_volume": self.search_volume,
        }


@dataclass
class EntitySignal:
    """A structured signal to strengthen Pipeleap's entity authority."""
    signal_type: str                 # "schema_markup" | "external_mention" | "sameAs_link" | "knowledge_graph"
    platform: str
    url: str
    description: str
    status: str                      # "active" | "planned" | "missing"
    impact_score: float = 0.0
    implementation_effort: str = "medium"   # "low" | "medium" | "high"

    def to_dict(self) -> dict[str, Any]:
        return {
            "signal_type": self.signal_type,
            "platform": self.platform,
            "url": self.url,
            "description": self.description,
            "status": self.status,
            "impact_score": self.impact_score,
            "implementation_effort": self.implementation_effort,
        }


@dataclass
class GEORunReport:
    """Output report from one GEO agent run."""
    generated_at: str
    pages_generated: list[GEOPage]
    citation_gaps: list[CitationGap]
    entity_signals: list[EntitySignal]
    ai_overview_queries: list[dict]  # Queries confirmed to have AI Overviews
    citation_score: float            # 0-100: current estimated AI citation readiness
    recommendations: list[str]
    output_directory: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "generated_at": self.generated_at,
            "total_pages": len(self.pages_generated),
            "pages_generated": [p.to_dict() for p in self.pages_generated],
            "citation_gaps": [c.to_dict() for c in self.citation_gaps],
            "entity_signals": [e.to_dict() for e in self.entity_signals],
            "ai_overview_queries": self.ai_overview_queries,
            "citation_score": self.citation_score,
            "recommendations": self.recommendations,
            "output_directory": self.output_directory,
        }
