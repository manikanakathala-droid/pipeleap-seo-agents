"""
Structured logging with JSON output for parsing and aggregation.
Integrates with logging framework and provides request tracing.
"""

import logging
import json
import uuid
import sys
from typing import Any, Dict, Optional
from pythonjsonlogger import jsonlogger
from datetime import datetime
from pathlib import Path


class StructuredLogger:
    """
    Wrapper for structured JSON logging.
    Logs to both stdout and file with correlation IDs.
    """
    
    def __init__(self, name: str, log_dir: str = "outputs/logs"):
        self.logger = logging.getLogger(name)
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.correlation_id = str(uuid.uuid4())
        
        # Clear existing handlers
        self.logger.handlers = []
        self.logger.setLevel(logging.DEBUG)
        
        # Setup JSON handler for stdout
        json_handler = logging.StreamHandler(sys.stdout)
        json_formatter = jsonlogger.JsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s %(correlation_id)s',
            timestamp=True,
        )
        json_handler.setFormatter(json_formatter)
        self.logger.addHandler(json_handler)
        
        # Setup rotating file handler
        try:
            from logging.handlers import RotatingFileHandler
            
            log_file = self.log_dir / f"{name}.log"
            file_handler = RotatingFileHandler(
                str(log_file),
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
            )
            file_handler.setFormatter(json_formatter)
            self.logger.addHandler(file_handler)
        except Exception as e:
            self.logger.warning(f"Could not setup file logging: {e}")
    
    def set_correlation_id(self, correlation_id: str):
        """Set request correlation ID for tracing."""
        self.correlation_id = correlation_id
    
    def log_event(
        self,
        level: str,
        message: str,
        **kwargs: Any,
    ):
        """
        Log structured event with context.
        
        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            message: Log message
            **kwargs: Additional context fields
        """
        extra = {
            "correlation_id": self.correlation_id,
            **kwargs,
        }
        
        log_method = getattr(self.logger, level.lower(), self.logger.info)
        log_method(message, extra=extra)
    
    def debug(self, msg: str, **kwargs):
        self.log_event("DEBUG", msg, **kwargs)
    
    def info(self, msg: str, **kwargs):
        self.log_event("INFO", msg, **kwargs)
    
    def warning(self, msg: str, **kwargs):
        self.log_event("WARNING", msg, **kwargs)
    
    def error(self, msg: str, **kwargs):
        self.log_event("ERROR", msg, **kwargs)
    
    def critical(self, msg: str, **kwargs):
        self.log_event("CRITICAL", msg, **kwargs)
    
    def log_stage_start(self, stage: str, **context):
        """Log pipeline stage start."""
        self.info(
            f"Stage started: {stage}",
            stage=stage,
            event="stage_start",
            **context,
        )
    
    def log_stage_end(self, stage: str, duration_seconds: float = None, **context):
        """Log pipeline stage completion."""
        self.info(
            f"Stage completed: {stage}",
            stage=stage,
            event="stage_end",
            duration_seconds=duration_seconds,
            **context,
        )
    
    def log_stage_error(self, stage: str, error: str, **context):
        """Log pipeline stage error."""
        self.error(
            f"Stage failed: {stage}",
            stage=stage,
            event="stage_error",
            error=error,
            **context,
        )
    
    def log_api_call(
        self,
        service: str,
        endpoint: str,
        method: str = "GET",
        status_code: int = None,
        duration_ms: float = None,
        **context,
    ):
        """Log API call."""
        self.info(
            f"API call: {service} {method} {endpoint}",
            event="api_call",
            service=service,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration_ms=duration_ms,
            **context,
        )
    
    def log_api_error(
        self,
        service: str,
        endpoint: str,
        error: str,
        retry_count: int = None,
        **context,
    ):
        """Log API error."""
        self.error(
            f"API error: {service} {endpoint}",
            event="api_error",
            service=service,
            endpoint=endpoint,
            error=error,
            retry_count=retry_count,
            **context,
        )
    
    def log_content_generated(
        self,
        content_type: str,
        count: int,
        quality_score: float = None,
        **context,
    ):
        """Log content generation."""
        self.info(
            f"Generated {count} {content_type} assets",
            event="content_generated",
            content_type=content_type,
            count=count,
            quality_score=quality_score,
            **context,
        )
    
    def log_content_published(
        self,
        url: str,
        content_type: str,
        **context,
    ):
        """Log content publication."""
        self.info(
            f"Published {content_type}: {url}",
            event="content_published",
            url=url,
            content_type=content_type,
            **context,
        )
    
    def log_metric(self, metric_name: str, value: float, unit: str = None, **context):
        """Log metric value."""
        self.info(
            f"Metric: {metric_name}={value}{unit or ''}",
            event="metric",
            metric_name=metric_name,
            metric_value=value,
            metric_unit=unit,
            **context,
        )


class CorrelationIdMiddleware:
    """
    ASGI middleware for adding correlation IDs to requests.
    For use with FastAPI/Flask health endpoints.
    """
    
    def __init__(self, app, logger: StructuredLogger = None):
        self.app = app
        self.logger = logger
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Extract or generate correlation ID
        correlation_id = None
        for header_name, header_value in scope.get("headers", []):
            if header_name == b"x-correlation-id":
                correlation_id = header_value.decode()
                break
        
        if not correlation_id:
            correlation_id = str(uuid.uuid4())
        
        # Add to scope
        scope["correlation_id"] = correlation_id
        
        # Set logger correlation ID
        if self.logger:
            self.logger.set_correlation_id(correlation_id)
        
        # Add correlation ID to response headers
        async def send_with_correlation(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                headers.append(
                    (
                        b"x-correlation-id",
                        correlation_id.encode(),
                    )
                )
                message["headers"] = headers
            await send(message)
        
        await self.app(scope, receive, send_with_correlation)


# Global logger instances
_loggers: Dict[str, StructuredLogger] = {}


def get_logger(name: str, log_dir: str = "outputs/logs") -> StructuredLogger:
    """Get or create structured logger instance."""
    if name not in _loggers:
        _loggers[name] = StructuredLogger(name, log_dir)
    return _loggers[name]


def configure_logging(
    log_level: str = "INFO",
    log_dir: str = "outputs/logs",
):
    """
    Configure all logging for the application.
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_dir: Directory for log files
    """
    # Get root logger
    root_logger = get_logger("root", log_dir)
    
    # Set level
    level = getattr(logging, log_level.upper(), logging.INFO)
    root_logger.logger.setLevel(level)
    
    # Log configuration
    root_logger.info(
        f"Logging configured: level={log_level}, log_dir={log_dir}",
        event="logging_configured",
        log_level=log_level,
        log_dir=log_dir,
    )
