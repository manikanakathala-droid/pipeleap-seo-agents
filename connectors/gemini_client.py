from __future__ import annotations

import os
from typing import Any

try:
    from google import genai as _genai
    from google.genai import types as _genai_types
    _HAS_GEMINI = True
except ImportError:
    _HAS_GEMINI = False


class GeminiClient:
    """
    Gemini API wrapper for content generation.

    Always returns data — falls back gracefully if unconfigured or errored.
    Mirrors pattern from FreeKeywordConnector for consistency.
    """

    is_configured: bool = False

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        if self.api_key and _HAS_GEMINI:
            self._client = _genai.Client(api_key=self.api_key)
            self.is_configured = True
        else:
            self._client = None

    def generate(
        self,
        prompt: str,
        model: str = "gemini-2.0-flash",
        **kwargs: Any,
    ) -> str:
        """Generate content from prompt. Returns empty string on failure."""
        if not self.is_configured or self._client is None:
            return ""
        try:
            resp = self._client.models.generate_content(
                model=model,
                contents=prompt,
                **kwargs,
            )
            return resp.text or ""
        except Exception:
            return ""
