"""
Health check and readiness probe system.
Provides /health and /ready endpoints for container orchestrators.
"""

import logging
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
import json

log = logging.getLogger(__name__)


class HealthChecker:
    """
    Comprehensive health check system for monitoring agent readiness.
    Checks configuration, credentials, database, and external services.
    """
    
    def __init__(self, config_schema=None):
        self.config_schema = config_schema
        self.last_check_time = None
        self.last_check_result = None
        self.check_cache_seconds = 10  # Cache health checks for 10 seconds
    
    def check_all(self, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Run all health checks.
        
        Returns:
            {
                "status": "healthy|degraded|unhealthy",
                "timestamp": "2024-01-15T...",
                "checks": {
                    "config": {...},
                    "credentials": {...},
                    "database": {...},
                    "storage": {...},
                }
            }
        """
        now = datetime.utcnow()
        
        # Return cached result if fresh
        if (
            self.last_check_time
            and (now - self.last_check_time).total_seconds() < self.check_cache_seconds
            and self.last_check_result
        ):
            return self.last_check_result
        
        checks = {
            "config": self.check_config(config),
            "credentials": self.check_credentials(config),
            "database": self.check_database(config),
            "storage": self.check_storage(config),
            "system": self.check_system(),
        }
        
        # Determine overall status
        statuses = [c.get("status") for c in checks.values()]
        if all(s == "healthy" for s in statuses):
            overall_status = "healthy"
        elif any(s == "unhealthy" for s in statuses):
            overall_status = "unhealthy"
        else:
            overall_status = "degraded"
        
        result = {
            "status": overall_status,
            "timestamp": now.isoformat(),
            "checks": checks,
        }
        
        self.last_check_time = now
        self.last_check_result = result
        
        return result
    
    def check_config(self, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Check if configuration is valid."""
        if config is None:
            return {"status": "unknown", "message": "No config provided"}
        
        issues = []
        
        # Check required fields
        if not config.get("site", {}).get("site_url"):
            issues.append("site.site_url is not configured")
        
        if not config.get("site", {}).get("domain"):
            issues.append("site.domain is not configured")
        
        if self.config_schema:
            try:
                self.config_schema.validate_config(config)
            except Exception as e:
                issues.append(f"Config validation failed: {e}")
        
        if issues:
            return {
                "status": "unhealthy",
                "issues": issues,
            }
        
        return {
            "status": "healthy",
            "message": "Configuration valid",
        }
    
    def check_credentials(self, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Check if credential files are accessible."""
        if config is None:
            return {"status": "unknown"}
        
        issues = []
        credentials_checked = 0
        credentials_ok = 0
        
        # Check GSC credentials
        gsc_creds = config.get("integrations", {}).get("gsc", {}).get("credentials_path")
        if gsc_creds:
            credentials_checked += 1
            if Path(gsc_creds).exists():
                credentials_ok += 1
            else:
                issues.append(f"GSC credentials not found: {gsc_creds}")
        
        # Check Analytics credentials
        ga_creds = config.get("integrations", {}).get("analytics", {}).get("credentials_path")
        if ga_creds:
            credentials_checked += 1
            if Path(ga_creds).exists():
                credentials_ok += 1
            else:
                issues.append(f"Analytics credentials not found: {ga_creds}")
        
        if credentials_checked == 0:
            return {"status": "healthy", "message": "No credentials required"}
        
        if credentials_ok == credentials_checked:
            return {"status": "healthy", "message": f"All {credentials_ok} credentials accessible"}
        
        return {
            "status": "degraded" if credentials_ok > 0 else "unhealthy",
            "credentials_checked": credentials_checked,
            "credentials_ok": credentials_ok,
            "issues": issues,
        }
    
    def check_database(self, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Check if database is accessible."""
        try:
            import sqlite3
            
            db_path = "outputs/pipeleap_seo_memory.sqlite"
            if config:
                db_path = config.get("execution", {}).get("memory_db", db_path)
            
            # Try to connect
            conn = sqlite3.connect(db_path, timeout=2)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            conn.close()
            
            return {
                "status": "healthy",
                "database": db_path,
                "message": "Database accessible",
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "database": db_path,
                "error": str(e),
            }
    
    def check_storage(self, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Check if output directory is writable."""
        output_dir = "outputs"
        if config:
            output_dir = config.get("execution", {}).get("output_dir", output_dir)
        
        try:
            path = Path(output_dir)
            path.mkdir(parents=True, exist_ok=True)
            
            # Test write
            test_file = path / ".health_check_test"
            test_file.touch()
            test_file.unlink()
            
            return {
                "status": "healthy",
                "output_dir": str(path),
                "message": "Output directory writable",
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "output_dir": str(path),
                "error": str(e),
            }
    
    def check_system(self) -> Dict[str, Any]:
        """Check system resources."""
        import psutil
        
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            
            issues = []
            if cpu_percent > 90:
                issues.append(f"High CPU usage: {cpu_percent}%")
            if memory.percent > 90:
                issues.append(f"High memory usage: {memory.percent}%")
            
            status = "healthy"
            if issues:
                status = "degraded" if len(issues) == 1 else "unhealthy"
            
            return {
                "status": status,
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available // (1024 * 1024),
                "issues": issues,
            }
        except Exception as e:
            return {
                "status": "unknown",
                "error": str(e),
            }


class ReadinessProbe:
    """
    Readiness probe for Kubernetes.
    Checks if service is ready to handle requests.
    """
    
    def __init__(self, health_checker: HealthChecker):
        self.health_checker = health_checker
    
    def is_ready(self, config: Dict[str, Any] = None) -> bool:
        """Check if service is ready."""
        health = self.health_checker.check_all(config)
        return health["status"] != "unhealthy"
    
    def get_status(self, config: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get readiness status."""
        health = self.health_checker.check_all(config)
        return {
            "ready": health["status"] != "unhealthy",
            "health": health,
        }


class LivenessProbe:
    """
    Liveness probe for Kubernetes.
    Simply checks if process is responsive.
    """
    
    def is_alive(self) -> bool:
        """Process is alive if this returns."""
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get liveness status."""
        return {
            "alive": True,
            "timestamp": datetime.utcnow().isoformat(),
        }


# Global instances
_health_checker = None
_readiness_probe = None
_liveness_probe = None


def get_health_checker(config_schema=None) -> HealthChecker:
    """Get or create global health checker."""
    global _health_checker
    if _health_checker is None:
        _health_checker = HealthChecker(config_schema)
    return _health_checker


def get_readiness_probe(config_schema=None) -> ReadinessProbe:
    """Get or create global readiness probe."""
    global _readiness_probe
    if _readiness_probe is None:
        checker = get_health_checker(config_schema)
        _readiness_probe = ReadinessProbe(checker)
    return _readiness_probe


def get_liveness_probe() -> LivenessProbe:
    """Get or create global liveness probe."""
    global _liveness_probe
    if _liveness_probe is None:
        _liveness_probe = LivenessProbe()
    return _liveness_probe


# Endpoint handlers
def health_endpoint(config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Handler for GET /health endpoint."""
    checker = get_health_checker()
    return checker.check_all(config)


def ready_endpoint(config: Dict[str, Any] = None) -> Dict[str, Any]:
    """Handler for GET /ready endpoint."""
    probe = get_readiness_probe()
    return probe.get_status(config)


def alive_endpoint() -> Dict[str, Any]:
    """Handler for GET /alive endpoint."""
    probe = get_liveness_probe()
    return probe.get_status()
