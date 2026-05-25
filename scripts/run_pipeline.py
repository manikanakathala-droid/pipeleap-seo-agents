import logging
import sys
from pathlib import Path

# Ensure the root directory is in the path for imports
sys.path.append(str(Path(__file__).resolve().parent.parent))

from utils.structured_logging import configure_logging, get_logger
from utils.config_loader import load_config
from utils.config_schema import validate_config, validate_credentials_accessible
from utils.health_check import get_readiness_probe, get_liveness_probe
from utils.alert_logger import AlertLogger
from agents.seo_orchestrator import SEOOrchestrator

logger = logging.getLogger(__name__)


def run_full_pipeline() -> int:
    """Run full pipeline once. Returns exit code (0 success, 1 failure)."""
    try:
        config = load_config(Path(__file__).resolve().parent.parent / "config.yaml")
    except Exception as e:
        logger.error("Failed to load config: %s", e)
        return 1

    # Structured logging configuration
    log_level = config.get("execution", {}).get("log_level", "INFO")
    configure_logging(log_level)
    log = get_logger("run_pipeline")

    # Validate config with pydantic schema
    try:
        validated = validate_config(config)
    except Exception as e:
        log.error("Configuration validation failed: %s", e)
        return 1

    # Check credentials accessibility
    missing = validate_credentials_accessible(validated)
    if missing:
        log.error("Missing credential files: %s", missing)
        return 1

    alerts = AlertLogger(config)

    log.info("Starting Full SEO Pipeline")

    try:
        log.info("--- 1. SEO Orchestrator ---")
        seo = SEOOrchestrator(config)
        seo.run_once()
    except Exception as e:
        log.error("SEOOrchestrator failed: %s", e)
        try:
            alerts.alert_circuit_breaker(f"SEOOrchestrator failed: {e}")
        except Exception:
            log.warning("Failed to send circuit breaker alert")
        return 1

    try:
        log.info("--- 2. GEO Orchestrator ---")
        try:
            from geo_agent.geo_orchestrator import GEOOrchestrator
            geo = GEOOrchestrator(config)
            if hasattr(geo, 'run'):
                geo.run()
            elif hasattr(geo, 'run_once'):
                geo.run_once()
        except ImportError:
            log.warning("GEOOrchestrator not found (geo_agent.geo_orchestrator), skipping.")
    except Exception as e:
        log.error("GEOOrchestrator failed: %s", e)
        # non-fatal

    try:
        log.info("--- 3. Growth Engine Orchestrator ---")
        try:
            from modules.pipeleap_seo_engine.orchestrator import GrowthEngineOrchestrator
            growth = GrowthEngineOrchestrator(config)
            if hasattr(growth, 'run'):
                growth.run()
            elif hasattr(growth, 'run_once'):
                growth.run_once()
        except ImportError:
            log.warning("GrowthEngineOrchestrator not found (modules.pipeleap_seo_engine.orchestrator), skipping.")
    except Exception as e:
        log.error("GrowthEngineOrchestrator failed: %s", e)

    try:
        log.info("--- 4. SERP Visibility Agent ---")
        try:
            from agents.serp_visibility_agent import SerpVisibilityAgent
            serp = SerpVisibilityAgent(config)
            if hasattr(serp, 'run_once'):
                serp.run_once()
            elif hasattr(serp, 'run'):
                serp.run()
        except ImportError:
            log.warning("SerpVisibilityAgent not found, skipping.")
    except Exception as e:
        log.error("SERPVisibilityAgent failed: %s", e)
        
    log.info("Full SEO Pipeline Completed")

if __name__ == "__main__":
    run_full_pipeline()
