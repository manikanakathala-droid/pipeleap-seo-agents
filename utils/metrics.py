"""
Prometheus metrics for observability and monitoring.
Tracks pipeline execution, API calls, content generation, and system health.
"""

import logging
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    Summary,
    CollectorRegistry,
    generate_latest,
    REGISTRY,
)
from typing import Dict, Any

log = logging.getLogger(__name__)


class MetricsCollector:
    """
    Prometheus metrics for SEO pipeline.
    Tracks execution, content generation, API calls, and errors.
    """
    
    def __init__(self, registry: CollectorRegistry = REGISTRY):
        self.registry = registry
        
        # Pipeline execution metrics
        self.pipeline_runs = Counter(
            "seo_pipeline_runs_total",
            "Total pipeline runs",
            registry=registry,
        )
        
        self.pipeline_run_duration = Histogram(
            "seo_pipeline_run_duration_seconds",
            "Pipeline run duration in seconds",
            buckets=(60, 300, 600, 1800, 3600),
            registry=registry,
        )
        
        self.pipeline_run_errors = Counter(
            "seo_pipeline_run_errors_total",
            "Total pipeline run errors",
            ["stage"],
            registry=registry,
        )
        
        # Stage execution metrics
        self.stage_duration = Histogram(
            "seo_stage_duration_seconds",
            "Stage execution duration in seconds",
            ["stage"],
            buckets=(10, 30, 60, 120, 300),
            registry=registry,
        )
        
        self.stage_completions = Counter(
            "seo_stage_completions_total",
            "Stage completions",
            ["stage"],
            registry=registry,
        )
        
        self.stage_failures = Counter(
            "seo_stage_failures_total",
            "Stage failures",
            ["stage"],
            registry=registry,
        )
        
        # Content generation metrics
        self.content_generated = Counter(
            "seo_content_generated_total",
            "Content items generated",
            ["content_type"],
            registry=registry,
        )
        
        self.content_quality_score = Histogram(
            "seo_content_quality_score",
            "Content quality scores",
            ["content_type"],
            buckets=(0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0),
            registry=registry,
        )
        
        self.content_published = Counter(
            "seo_content_published_total",
            "Content items published",
            ["content_type", "platform"],
            registry=registry,
        )
        
        # API metrics
        self.api_calls = Counter(
            "seo_api_calls_total",
            "Total API calls",
            ["service", "endpoint", "method", "status"],
            registry=registry,
        )
        
        self.api_request_duration = Histogram(
            "seo_api_request_duration_seconds",
            "API request duration in seconds",
            ["service", "endpoint"],
            buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0),
            registry=registry,
        )
        
        self.api_errors = Counter(
            "seo_api_errors_total",
            "API errors",
            ["service", "endpoint", "error_type"],
            registry=registry,
        )
        
        self.api_retries = Counter(
            "seo_api_retries_total",
            "API call retries",
            ["service", "endpoint"],
            registry=registry,
        )
        
        # Rate limiting metrics
        self.rate_limit_hits = Counter(
            "seo_rate_limit_hits_total",
            "Rate limit hits",
            ["service"],
            registry=registry,
        )
        
        self.rate_limit_wait_time = Histogram(
            "seo_rate_limit_wait_seconds",
            "Time spent waiting for rate limit",
            ["service"],
            buckets=(0.1, 0.5, 1.0, 5.0, 10.0),
            registry=registry,
        )
        
        # Deduplication metrics
        self.duplicate_submissions_prevented = Counter(
            "seo_duplicate_submissions_prevented_total",
            "Duplicate submissions prevented by deduplication",
            ["operation"],
            registry=registry,
        )
        
        # Crawl metrics
        self.pages_crawled = Counter(
            "seo_pages_crawled_total",
            "Pages crawled",
            registry=registry,
        )
        
        self.crawl_errors = Counter(
            "seo_crawl_errors_total",
            "Crawl errors",
            registry=registry,
        )
        
        self.crawl_duration = Histogram(
            "seo_crawl_duration_seconds",
            "Crawl duration in seconds",
            buckets=(60, 300, 600, 1800),
            registry=registry,
        )
        
        # Database metrics
        self.db_queries = Counter(
            "seo_db_queries_total",
            "Database queries",
            ["operation"],
            registry=registry,
        )
        
        self.db_query_duration = Histogram(
            "seo_db_query_duration_seconds",
            "Database query duration in seconds",
            ["operation"],
            buckets=(0.001, 0.01, 0.1, 0.5, 1.0),
            registry=registry,
        )
        
        self.db_errors = Counter(
            "seo_db_errors_total",
            "Database errors",
            registry=registry,
        )
        
        # System metrics
        self.memory_usage_bytes = Gauge(
            "seo_memory_usage_bytes",
            "Memory usage in bytes",
            registry=registry,
        )
        
        self.cpu_usage_percent = Gauge(
            "seo_cpu_usage_percent",
            "CPU usage percentage",
            registry=registry,
        )
        
        self.circuit_breaker_trips = Counter(
            "seo_circuit_breaker_trips_total",
            "Circuit breaker trips",
            ["reason"],
            registry=registry,
        )
    
    # Timing context manager
    def time_stage(self, stage: str):
        """Context manager to time stage execution."""
        class TimerContext:
            def __init__(self, metrics, stage_name):
                self.metrics = metrics
                self.stage_name = stage_name
                self.start_time = None
            
            def __enter__(self):
                self.start_time = __import__("time").time()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                duration = __import__("time").time() - self.start_time
                self.metrics.stage_duration.labels(stage=self.stage_name).observe(duration)
                
                if exc_type:
                    self.metrics.stage_failures.labels(stage=self.stage_name).inc()
                else:
                    self.metrics.stage_completions.labels(stage=self.stage_name).inc()
                
                return False
        
        return TimerContext(self, stage)
    
    def time_api_call(self, service: str, endpoint: str):
        """Context manager to time API calls."""
        class TimerContext:
            def __init__(self, metrics, service, endpoint):
                self.metrics = metrics
                self.service = service
                self.endpoint = endpoint
                self.start_time = None
            
            def __enter__(self):
                self.start_time = __import__("time").time()
                return self
            
            def __exit__(self, exc_type, exc_val, exc_tb):
                duration = __import__("time").time() - self.start_time
                self.metrics.api_request_duration.labels(
                    service=self.service,
                    endpoint=self.endpoint,
                ).observe(duration)
                return False
        
        return TimerContext(self, service, endpoint)
    
    def record_api_call(
        self,
        service: str,
        endpoint: str,
        method: str = "GET",
        status_code: int = 200,
        duration_seconds: float = 0.0,
    ):
        """Record API call metrics."""
        self.api_calls.labels(
            service=service,
            endpoint=endpoint,
            method=method,
            status=status_code,
        ).inc()
        
        self.api_request_duration.labels(
            service=service,
            endpoint=endpoint,
        ).observe(duration_seconds)
    
    def record_api_error(
        self,
        service: str,
        endpoint: str,
        error_type: str = "unknown",
    ):
        """Record API error."""
        self.api_errors.labels(
            service=service,
            endpoint=endpoint,
            error_type=error_type,
        ).inc()
    
    def record_content_generated(
        self,
        content_type: str,
        count: int = 1,
        quality_score: float = None,
    ):
        """Record content generation."""
        self.content_generated.labels(content_type=content_type).inc(count)
        
        if quality_score is not None:
            self.content_quality_score.labels(
                content_type=content_type,
            ).observe(quality_score)
    
    def record_content_published(
        self,
        content_type: str,
        platform: str = "cms",
        count: int = 1,
    ):
        """Record content publication."""
        self.content_published.labels(
            content_type=content_type,
            platform=platform,
        ).inc(count)
    
    def record_rate_limit_hit(self, service: str, wait_time_seconds: float = 0.0):
        """Record rate limit hit."""
        self.rate_limit_hits.labels(service=service).inc()
        if wait_time_seconds > 0:
            self.rate_limit_wait_time.labels(service=service).observe(wait_time_seconds)
    
    def record_duplicate_prevented(self, operation: str):
        """Record prevented duplicate submission."""
        self.duplicate_submissions_prevented.labels(operation=operation).inc()
    
    def record_circuit_breaker_trip(self, reason: str):
        """Record circuit breaker trip."""
        self.circuit_breaker_trips.labels(reason=reason).inc()
    
    def get_metrics(self) -> bytes:
        """Get Prometheus metrics in text format."""
        return generate_latest(self.registry)


# Global metrics instance
_metrics_collector = None


def get_metrics_collector() -> MetricsCollector:
    """Get or create global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def metrics_endpoint() -> bytes:
    """Handler for GET /metrics endpoint (Prometheus format)."""
    collector = get_metrics_collector()
    return collector.get_metrics()
