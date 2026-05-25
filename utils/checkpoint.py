"""
Checkpoint system for resumable pipeline execution.
Saves state after each major stage so pipeline can resume from last completed stage.
"""

import logging
import json
from typing import Dict, Any, Optional, List
from pathlib import Path
from datetime import datetime

log = logging.getLogger(__name__)


class CheckpointManager:
    """
    Manages execution checkpoints for pipeline resumability.
    Saves stage completion status and intermediate results.
    """
    
    def __init__(self, checkpoint_dir: str = "outputs/checkpoints"):
        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        self.current_run_id = datetime.utcnow().isoformat()
        self.checkpoints: Dict[str, Dict[str, Any]] = {}
        self._load_checkpoints()
    
    def _get_checkpoint_file(self, run_id: str = None) -> Path:
        """Get path to checkpoint file."""
        if run_id is None:
            run_id = self.current_run_id
        return self.checkpoint_dir / f"checkpoint_{run_id}.json"
    
    def _load_checkpoints(self):
        """Load existing checkpoints from disk."""
        checkpoint_file = self._get_checkpoint_file()
        if checkpoint_file.exists():
            try:
                with open(checkpoint_file, "r") as f:
                    self.checkpoints = json.load(f)
                log.info("Loaded checkpoints from %s", checkpoint_file)
            except Exception as e:
                log.error("Failed to load checkpoints: %s", e)
    
    def _save_checkpoints(self):
        """Persist checkpoints to disk."""
        checkpoint_file = self._get_checkpoint_file()
        try:
            with open(checkpoint_file, "w") as f:
                json.dump(self.checkpoints, f, indent=2, default=str)
            log.debug("Saved checkpoints to %s", checkpoint_file)
        except Exception as e:
            log.error("Failed to save checkpoints: %s", e)
    
    def get_last_completed_stage(self) -> Optional[str]:
        """Get the last completed stage from previous run."""
        for stage_name in ["crawl", "gsc", "keywords", "landing_pages", "content",
                           "linking", "audit", "backlinks", "analytics", "growth", "publish"]:
            if stage_name in self.checkpoints and self.checkpoints[stage_name].get("completed"):
                return stage_name
        return None
    
    def should_resume_from_stage(self, stage_name: str) -> bool:
        """Check if this stage was already completed."""
        if stage_name in self.checkpoints:
            return self.checkpoints[stage_name].get("completed", False)
        return False
    
    def save_stage_checkpoint(
        self,
        stage_name: str,
        completed: bool = False,
        data: Dict[str, Any] = None,
        error: str = None,
    ) -> bool:
        """
        Save checkpoint for a pipeline stage.
        
        Args:
            stage_name: Name of the stage (e.g., "crawl", "content")
            completed: Whether stage completed successfully
            data: Stage output data to save
            error: Error message if stage failed
            
        Returns:
            True if checkpoint saved
        """
        try:
            self.checkpoints[stage_name] = {
                "timestamp": datetime.utcnow().isoformat(),
                "completed": completed,
                "data": data,
                "error": error,
            }
            self._save_checkpoints()
            
            status = "✓" if completed else "✗"
            log.info(f"Checkpoint [{status}] {stage_name}")
            
            return True
        except Exception as e:
            log.error("Failed to save checkpoint for %s: %s", stage_name, e)
            return False
    
    def get_stage_data(self, stage_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve saved data from a stage checkpoint."""
        if stage_name in self.checkpoints:
            return self.checkpoints[stage_name].get("data")
        return None
    
    def get_stage_error(self, stage_name: str) -> Optional[str]:
        """Get error from a failed stage checkpoint."""
        if stage_name in self.checkpoints:
            return self.checkpoints[stage_name].get("error")
        return None
    
    def get_all_completed_stages(self) -> List[str]:
        """Get list of all completed stages."""
        return [
            name
            for name, checkpoint in self.checkpoints.items()
            if checkpoint.get("completed", False)
        ]
    
    def reset(self):
        """Clear all checkpoints (start fresh run)."""
        self.checkpoints = {}
        checkpoint_file = self._get_checkpoint_file()
        if checkpoint_file.exists():
            checkpoint_file.unlink()
        log.info("Checkpoints reset")
    
    def get_checkpoint_summary(self) -> Dict[str, Any]:
        """Get summary of all checkpoints."""
        return {
            "run_id": self.current_run_id,
            "total_stages": len(self.checkpoints),
            "completed_stages": len(self.get_all_completed_stages()),
            "stages": {
                name: {
                    "completed": cp.get("completed", False),
                    "timestamp": cp.get("timestamp"),
                    "has_error": cp.get("error") is not None,
                }
                for name, cp in self.checkpoints.items()
            },
        }


class StageContext:
    """Context manager for pipeline stages with automatic checkpointing."""
    
    def __init__(self, manager: CheckpointManager, stage_name: str):
        self.manager = manager
        self.stage_name = stage_name
        self.data = None
        self.error = None
    
    def __enter__(self):
        """Enter stage context."""
        log.info(f"Starting stage: {self.stage_name}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit stage context and save checkpoint."""
        if exc_type is not None:
            self.error = f"{exc_type.__name__}: {exc_val}"
            log.error(f"Stage {self.stage_name} failed: {self.error}")
            self.manager.save_stage_checkpoint(
                self.stage_name,
                completed=False,
                error=self.error,
            )
            return False
        
        self.manager.save_stage_checkpoint(
            self.stage_name,
            completed=True,
            data=self.data,
        )
        log.info(f"Stage {self.stage_name} completed")
        return True


# Global checkpoint manager instance
_checkpoint_manager = None


def get_checkpoint_manager(
    checkpoint_dir: str = "outputs/checkpoints",
) -> CheckpointManager:
    """Get or create global checkpoint manager."""
    global _checkpoint_manager
    if _checkpoint_manager is None:
        _checkpoint_manager = CheckpointManager(checkpoint_dir)
    return _checkpoint_manager


def stage_checkpoint(stage_name: str):
    """
    Decorator for pipeline stages with automatic checkpointing.
    
    Usage:
        @stage_checkpoint("content_generation")
        def generate_content(config):
            ...
            return content
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            manager = get_checkpoint_manager()
            context = StageContext(manager, stage_name)
            
            with context:
                result = func(*args, **kwargs)
                context.data = result
                return result
        
        return wrapper
    return decorator
