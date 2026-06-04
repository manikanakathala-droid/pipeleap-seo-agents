"""
Pydantic schema for configuration validation with startup checks.
Ensures all required fields are present and valid before execution starts.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from pathlib import Path


class SiteConfig(BaseModel):
    brand: str = Field(..., min_length=1, description="Brand name")
    site_url: str = Field(..., pattern=r"^https?://", description="Site URL must start with http/https")
    domain: str = Field(..., min_length=1, description="Domain name")
    cta: Dict[str, str] = Field(default_factory=dict, description="CTA configuration")
    target_personas: List[str] = Field(default_factory=list, description="Target personas")
    core_features: List[str] = Field(default_factory=list, description="Core features")

    class Config:
        str_strip_whitespace = True


class ExecutionConfig(BaseModel):
    crawl_enabled: bool = True
    max_pages: int = Field(25, ge=1, le=1000)
    max_depth: int = Field(2, ge=1, le=5)
    landing_pages_per_run: int = Field(5, ge=0, le=50)
    blog_posts_per_run: int = Field(4, ge=0, le=50)
    comparison_pages_per_run: int = Field(2, ge=0, le=50)
    use_case_pages_per_run: int = Field(2, ge=0, le=50)
    case_studies_per_run: int = Field(0, ge=0, le=50)
    output_dir: str = "outputs"
    memory_db: str = "outputs/pipeleap_seo_memory.sqlite"
    log_level: str = Field("INFO", pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    use_renderer: bool = False


class GSCConfig(BaseModel):
    site_url: Optional[str] = Field(None, description="GSC site URL (sc-domain: format)")
    credentials_path: Optional[str] = None
    data_export_path: Optional[str] = None

    @field_validator("site_url")
    @classmethod
    def validate_site_url(cls, v: str) -> str:
        if v and not v.startswith("sc-domain:"):
            raise ValueError("GSC site_url must start with 'sc-domain:'")
        return v


class AnalyticsConfig(BaseModel):
    ga4_property_id: Optional[str] = None
    credentials_path: Optional[str] = None
    conversion_export_path: Optional[str] = None


class PageSpeedConfig(BaseModel):
    api_key: Optional[str] = None
    enabled: bool = False

    @model_validator(mode="after")
    def check_key_if_enabled(self) -> "PageSpeedConfig":
        if self.enabled and not self.api_key:
            raise ValueError("PageSpeed API key required if enabled=true")
        return self


class GitHubConfig(BaseModel):
    token: Optional[str] = None
    repo: Optional[str] = None
    enabled: bool = False

    @model_validator(mode="after")
    def check_credentials_if_enabled(self) -> "GitHubConfig":
        if self.enabled:
            if not self.token:
                raise ValueError("GitHub token required if enabled=true")
            if not self.repo:
                raise ValueError("GitHub repo required if enabled=true")
        return self


class CMSConfig(BaseModel):
    webhook_url: Optional[str] = None
    mode: str = Field("filesystem", pattern="^(filesystem|webhook)$")


class AlertConfig(BaseModel):
    webhook_url: Optional[str] = None
    enabled: bool = False
    threshold_warnings: int = Field(5, ge=1)
    threshold_errors: int = Field(3, ge=1)


class ScheduleConfig(BaseModel):
    continuous: bool = False
    interval_minutes: int = Field(1440, ge=1, le=1440)
    max_consecutive_failures: int = Field(3, ge=1, le=10)


class IntegrationsConfig(BaseModel):
    gsc: Optional[GSCConfig] = Field(default_factory=GSCConfig)
    analytics: Optional[AnalyticsConfig] = Field(default_factory=AnalyticsConfig)
    pagespeed: Optional[PageSpeedConfig] = Field(default_factory=PageSpeedConfig)
    github: Optional[GitHubConfig] = Field(default_factory=GitHubConfig)
    cms: Optional[CMSConfig] = Field(default_factory=CMSConfig)
    alerts: Optional[AlertConfig] = Field(default_factory=AlertConfig)


class SEOConfig(BaseModel):
    seed_keywords: Dict[str, Any] = Field(default_factory=dict)
    topic_map: Dict[str, Any] = Field(default_factory=dict)
    competitors: List[str] = Field(default_factory=list)
    min_search_volume: int = Field(100, ge=0)
    max_difficulty_score: int = Field(50, ge=0, le=100)


class AppConfig(BaseModel):
    """
    Root configuration schema for SEO agents.
    Validates all required and optional fields at startup.
    """
    site: SiteConfig
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    integrations: IntegrationsConfig = Field(default_factory=IntegrationsConfig)
    schedule: ScheduleConfig = Field(default_factory=ScheduleConfig)
    seo: Optional[SEOConfig] = Field(default_factory=SEOConfig)

    class Config:
        arbitrary_types_allowed = True
        extra = "allow"  # Allow additional fields for extensibility

    @field_validator("execution")
    @classmethod
    def validate_execution(cls, v: "ExecutionConfig") -> "ExecutionConfig":
        total_per_run = (
            v.landing_pages_per_run
            + v.blog_posts_per_run
            + v.comparison_pages_per_run
            + v.use_case_pages_per_run
            + v.case_studies_per_run
        )
        if total_per_run > v.max_pages:
            raise ValueError(
                f"Total content per run ({total_per_run}) exceeds max_pages ({v.max_pages})"
            )
        return v


def validate_config(config_dict: Dict[str, Any]) -> AppConfig:
    """
    Validate configuration dictionary against schema.
    
    Raises:
        ValueError: If any required fields are missing or invalid
        
    Returns:
        Validated AppConfig instance
    """
    return AppConfig(**config_dict)


def validate_credentials_accessible(config: AppConfig) -> List[str]:
    """
    Check if all configured credential files are readable.
    
    Returns:
        List of missing/inaccessible credential files
    """
    missing_files = []
    
    if config.integrations.gsc and config.integrations.gsc.credentials_path:
        path = Path(config.integrations.gsc.credentials_path)
        if not path.exists():
            missing_files.append(f"GSC credentials: {path}")
    
    if config.integrations.analytics and config.integrations.analytics.credentials_path:
        path = Path(config.integrations.analytics.credentials_path)
        if not path.exists():
            missing_files.append(f"Analytics credentials: {path}")
    
    return missing_files


def validate_directories_writable(config: AppConfig) -> List[str]:
    """
    Check if all output directories are writable.
    
    Returns:
        List of unwritable directories
    """
    unwritable = []
    
    output_dir = Path(config.execution.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        test_file = output_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
    except (IOError, OSError) as e:
        unwritable.append(f"Output directory {output_dir}: {e}")
    
    return unwritable
