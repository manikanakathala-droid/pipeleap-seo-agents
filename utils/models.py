from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Optional


class SerializableMixin:
    """Provides a consistent dict serializer for nested dataclasses."""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class KeywordOpportunity(SerializableMixin):
    keyword: str
    topic_cluster: str
    intent: str
    funnel_stage: str
    source: str
    current_clicks: int = 0
    current_impressions: int = 0
    current_ctr: float = 0.0
    average_position: Optional[float] = None
    estimated_cpc_usd: Optional[float] = None
    cpc_source: str = "missing"
    estimated_difficulty: Optional[float] = None
    difficulty_source: str = "missing"
    conversion_probability: float = 0.0
    business_fit: float = 0.0
    traffic_potential_score: float = 0.0
    speed_to_rank_score: float = 0.0
    revenue_priority_score: float = 0.0
    semantic_expansions: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class KeywordCluster(SerializableMixin):
    cluster_name: str
    primary_keyword: str
    intent: str
    recommended_asset_type: str
    conversion_goal: str
    opportunities: list[KeywordOpportunity] = field(default_factory=list)
    aggregate_traffic_potential: float = 0.0
    aggregate_conversion_potential: float = 0.0
    strategic_rationale: str = ""


@dataclass
class PageSnapshot(SerializableMixin):
    url: str
    status_code: int
    title: str = ""
    meta_description: str = ""
    canonical: str = ""
    h1: str = ""
    headings: list[str] = field(default_factory=list)
    meta_robots: str = ""
    word_count: int = 0
    response_time_ms: int = 0
    internal_links: list[str] = field(default_factory=list)
    external_links: list[str] = field(default_factory=list)
    content_hash: str = ""
    schema_types: list[str] = field(default_factory=list)
    image_count: int = 0
    images_without_alt: int = 0
    links_without_anchor_text: int = 0
    links_with_generic_anchor: int = 0
    external_links_without_rel: int = 0
    non_indexable_file_links: int = 0
    links_with_hash_routing: int = 0
    script_count: int = 0
    stylesheet_count: int = 0
    has_viewport_meta: bool = False


@dataclass
class CrawlerReport(SerializableMixin):
    site_url: str
    pages: list[PageSnapshot] = field(default_factory=list)
    robots_txt_present: bool = False
    robots_rules: list[str] = field(default_factory=list)
    sitemap_urls: list[str] = field(default_factory=list)
    sitemap_relative_url_count: int = 0
    sitemap_index_detected: bool = False
    sitemap_cross_host_child_count: int = 0
    sitemap_image_count: int = 0
    sitemap_deprecated_image_tag_count: int = 0
    sitemap_news_article_count: int = 0
    sitemap_news_stale_article_count: int = 0
    sitemap_news_missing_required_tags: int = 0
    sitemap_video_count: int = 0
    sitemap_video_missing_required_tags: int = 0
    sitemap_video_deprecated_tag_count: int = 0
    sitemap_hreflang_url_count: int = 0
    sitemap_hreflang_missing_self_ref: int = 0
    crawl_errors: list[str] = field(default_factory=list)
    discovered_at: str = ""


@dataclass
class AuditIssue(SerializableMixin):
    severity: str
    category: str
    url: str
    description: str
    fix_instructions: str
    impact_score: float
    title: str = ""
    auto_fix_script: Optional[str] = None


@dataclass
class LinkSuggestion(SerializableMixin):
    source_url: str
    target_url: str
    anchor_text: str
    reason: str
    confidence: float
    link_type: str = "contextual"
    placement_hint: str = ""


@dataclass
class BacklinkOpportunity(SerializableMixin):
    prospect_name: str
    prospect_url: str
    category: str
    relevance_reason: str
    outreach_angle: str
    outreach_email_subject: str
    outreach_email_body: str
    estimated_authority: Optional[float] = None


@dataclass
class ContentBrief(SerializableMixin):
    primary_keyword: str
    keyword_cluster: str
    secondary_keywords: list[str]
    target_persona: str
    page_type: str
    funnel_stage: str
    conversion_goal: str
    unique_angle: str
    internal_link_targets: list[str]
    cta_label: str
    schema_types: list[str]
    stage: str = ""          # "early" | "growth" | "scale" — empty = stage-agnostic
    role: str = ""           # "cro" | "cso" | "vp_sales" | "sales_manager" | "founder"
    industry: str = "SaaS"
    use_case: str = ""
    competitor: str = ""


@dataclass
class ContentAsset(SerializableMixin):
    slug: str
    page_type: str
    title: str
    seo_title: str
    meta_description: str
    h1: str
    body_markdown: str
    schema_markup: list[dict[str, Any]]
    internal_link_suggestions: list[LinkSuggestion]
    call_to_action: str
    source_keywords: list[str]
    target_persona: str
    eeat_notes: list[str] = field(default_factory=list)
    stage: str = ""          # "early" | "growth" | "scale"
    role: str = ""
    industry: str = "SaaS"
    use_case: str = ""
    competitor: str = ""
    uniqueness_score: float = 1.0
    publish_path: Optional[str] = None
    date_published: str = ""
    date_modified: str = ""
    author_name: str = ""
    cta_variants: list[dict[str, Any]] = field(default_factory=list)
    hreflang_hints: list[dict[str, str]] = field(default_factory=list)
    eeat_checklist: list[dict[str, Any]] = field(default_factory=list)
    # AI content transparency — per Google's guidance on AI-generated content
    ai_assisted: bool = True
    generation_disclosure: str = (
        "This page was written with AI assistance and reviewed for accuracy, "
        "relevance, and alignment with Pipeleap's product and audience. "
        "All claims reflect Pipeleap's documented capabilities."
    )


@dataclass
class ExecutionAction(SerializableMixin):
    title: str
    description: str
    revenue_impact: str
    ranking_difficulty: str
    speed_to_rank: str
    effort: str
    owner: str
    related_keywords: list[str] = field(default_factory=list)
    supporting_urls: list[str] = field(default_factory=list)
    due_window: str = ""
    rationale: str = ""


@dataclass
class RoadmapStep(SerializableMixin):
    timebox: str
    objective: str
    outputs: list[str]
    success_metric: str


@dataclass
class RunResult(SerializableMixin):
    site: str
    generated_at: str
    seo_growth_opportunities: list[KeywordCluster]
    execution_plan: list[ExecutionAction]
    assets_generated: list[ContentAsset]
    audit_issues: list[AuditIssue]
    internal_links: list[LinkSuggestion]
    backlink_opportunities: list[BacklinkOpportunity]
    analytics_summary: dict[str, Any]
    roadmap_30_day: list[RoadmapStep]
    content_calendar: list[dict[str, Any]]
    integration_requests: list[str]
    output_directory: str
