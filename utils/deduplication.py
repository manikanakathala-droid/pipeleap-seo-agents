"""
Deduplication system to prevent duplicate operations.
Uses idempotency keys and checksums to track submitted items.
"""

import logging
import hashlib
import json
import sqlite3
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime, timedelta

log = logging.getLogger(__name__)


class DeduplicationStore:
    """
    SQLite-backed store for tracking submitted/published items.
    Prevents duplicate submissions if process is interrupted and re-run.
    """
    
    def __init__(self, db_path: str = "outputs/dedup.sqlite"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
    
    def _init_schema(self):
        """Create deduplication tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Idempotency key store
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS idempotency_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT UNIQUE NOT NULL,
                    operation TEXT NOT NULL,
                    result TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP
                )
            """)
            
            # Published content tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS published_content (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content_hash TEXT UNIQUE NOT NULL,
                    content_type TEXT NOT NULL,
                    url TEXT,
                    publish_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            # Submitted URLs (for indexing, backlinks, etc.)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS submitted_urls (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    url TEXT NOT NULL,
                    service TEXT NOT NULL,
                    submission_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'pending',
                    UNIQUE(url, service)
                )
            """)
            
            # Create indices
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_key ON idempotency_keys(key)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_hash ON published_content(content_hash)"
            )
            cursor.execute(
                "CREATE INDEX IF NOT EXISTS idx_submitted ON submitted_urls(url, service)"
            )
            
            conn.commit()
    
    def generate_idempotency_key(self, operation: str, data: Dict[str, Any]) -> str:
        """
        Generate deterministic idempotency key for operation.
        
        Args:
            operation: Operation type (e.g., "publish_blog", "submit_indexing")
            data: Operation data (content, URLs, etc.)
            
        Returns:
            SHA256 hash as idempotency key
        """
        payload = json.dumps({"op": operation, "data": data}, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()
    
    def check_idempotency(
        self,
        key: str,
        operation: str,
    ) -> Tuple[bool, Optional[str]]:
        """
        Check if operation with this key was already executed.
        
        Args:
            key: Idempotency key
            operation: Operation type
            
        Returns:
            (was_executed, previous_result)
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT result FROM idempotency_keys WHERE key = ? AND operation = ?",
                    (key, operation),
                )
                row = cursor.fetchone()
                
                if row:
                    return True, row[0]
                return False, None
        except sqlite3.Error as e:
            log.error(f"Dedup store error: {e}")
            return False, None
    
    def record_operation(
        self,
        key: str,
        operation: str,
        result: str = None,
        ttl_hours: int = 24,
    ) -> bool:
        """
        Record that an operation was executed.
        
        Args:
            key: Idempotency key
            operation: Operation type
            result: Result of operation (optional)
            ttl_hours: How long to keep record
            
        Returns:
            True if recorded, False if already existed
        """
        expires_at = datetime.utcnow() + timedelta(hours=ttl_hours)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO idempotency_keys 
                    (key, operation, result, expires_at) 
                    VALUES (?, ?, ?, ?)
                    """,
                    (key, operation, result, expires_at),
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            log.error(f"Failed to record operation: {e}")
            return False
    
    def check_content_published(self, content_hash: str) -> bool:
        """
        Check if content with this hash was already published.
        
        Args:
            content_hash: SHA256 of content
            
        Returns:
            True if already published
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM published_content WHERE content_hash = ?",
                    (content_hash,),
                )
                return cursor.fetchone() is not None
        except sqlite3.Error as e:
            log.error(f"Dedup store error: {e}")
            return False
    
    def record_published_content(
        self,
        content_hash: str,
        content_type: str,
        url: str = None,
        metadata: Dict[str, Any] = None,
    ) -> bool:
        """
        Record published content to prevent re-publication.
        
        Args:
            content_hash: SHA256 of content
            content_type: Type (blog, comparison, landing_page, etc.)
            url: Published URL (optional)
            metadata: Additional metadata (optional)
            
        Returns:
            True if recorded
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO published_content
                    (content_hash, content_type, url, metadata)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        content_hash,
                        content_type,
                        url,
                        json.dumps(metadata) if metadata else None,
                    ),
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            log.error(f"Failed to record published content: {e}")
            return False
    
    def check_url_submitted(self, url: str, service: str) -> bool:
        """
        Check if URL was already submitted to a service.
        
        Args:
            url: URL submitted
            service: Service (indexing_google, backlinks, etc.)
            
        Returns:
            True if already submitted
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT 1 FROM submitted_urls WHERE url = ? AND service = ?",
                    (url, service),
                )
                return cursor.fetchone() is not None
        except sqlite3.Error as e:
            log.error(f"Dedup store error: {e}")
            return False
    
    def record_url_submission(
        self,
        url: str,
        service: str,
        status: str = "pending",
    ) -> bool:
        """
        Record URL submission to prevent re-submission.
        
        Args:
            url: URL submitted
            service: Service name
            status: Submission status
            
        Returns:
            True if recorded
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO submitted_urls
                    (url, service, status)
                    VALUES (?, ?, ?)
                    """,
                    (url, service, status),
                )
                conn.commit()
                return cursor.rowcount > 0
        except sqlite3.Error as e:
            log.error(f"Failed to record submission: {e}")
            return False
    
    def cleanup_expired(self):
        """Remove expired deduplication records."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "DELETE FROM idempotency_keys WHERE expires_at < datetime('now')"
                )
                conn.commit()
                if cursor.rowcount > 0:
                    log.debug(f"Cleaned up {cursor.rowcount} expired dedup records")
        except sqlite3.Error as e:
            log.error(f"Cleanup error: {e}")


# Global deduplication store instance
_dedup_store = None


def get_dedup_store(db_path: str = "outputs/dedup.sqlite") -> DeduplicationStore:
    """Get or create global deduplication store."""
    global _dedup_store
    if _dedup_store is None:
        _dedup_store = DeduplicationStore(db_path)
    return _dedup_store


def content_hash(content: str) -> str:
    """Generate SHA256 hash of content."""
    return hashlib.sha256(content.encode()).hexdigest()
