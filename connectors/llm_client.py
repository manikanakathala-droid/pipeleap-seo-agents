"""
LLM client using GitHub Models (free, uses GITHUB_TOKEN).

Endpoint: https://models.inference.ai.azure.com
Auth:    Bearer <GITHUB_TOKEN> (or LAUNCHPAD_DEPLOY_TOKEN)
Models:  gpt-4o-mini (default), gpt-4o, Phi-4, DeepSeek-V3, Llama-3.3-70B, etc.

Rate limits (free tier, no Copilot):
  gpt-4o-mini: ~200 req/day, 8K in / 4K out tokens
  Phi-4:       ~200 req/day
  gpt-4o:      ~50 req/day

Always returns data — falls back gracefully if unconfigured or errored.
"""
from __future__ import annotations

import os
from typing import Any

try:
    from openai import OpenAI as _OpenAI
    _HAS_OPENAI = True
except ImportError:
    _HAS_OPENAI = False


class LLMClient:
    """Wrapper around GitHub Models API for content generation."""

    is_configured: bool = False

    def __init__(self, api_key: str | None = None) -> None:
        token = api_key or os.getenv("GITHUB_TOKEN") or os.getenv("LAUNCHPAD_DEPLOY_TOKEN") or ""
        if token and _HAS_OPENAI:
            self._client = _OpenAI(api_key=token, base_url="https://models.inference.ai.azure.com")
            self.is_configured = True
        else:
            self._client = None

    def generate(
        self,
        prompt: str,
        model: str = "gpt-4o-mini",
        **kwargs: Any,
    ) -> str:
        """Generate content from prompt. Returns empty string on failure."""
        if not self.is_configured or self._client is None:
            return ""
        try:
            resp = self._client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                **kwargs,
            )
            return resp.choices[0].message.content or ""
        except Exception:
            return ""
