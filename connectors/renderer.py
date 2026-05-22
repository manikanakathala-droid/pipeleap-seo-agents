from __future__ import annotations

from dataclasses import dataclass

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:  # pragma: no cover
    PLAYWRIGHT_AVAILABLE = False

_SOFT_404_PHRASES = frozenset({
    "page not found", "404 not found", "404 error", "not found",
    "page doesn't exist", "page does not exist", "doesn't exist",
    "cannot be found", "no longer available", "been removed",
    "this page is gone", "nothing here", "oops", "went wrong",
})

# JS injected into Chromium to detect fullscreen overlays
_OVERLAY_JS = """
() => {
    const vw = window.innerWidth || 1280;
    const vh = window.innerHeight || 800;
    const minW = vw * 0.65;
    const minH = vh * 0.65;
    for (const el of document.querySelectorAll('*')) {
        const tag = el.tagName.toUpperCase();
        if (tag === 'HTML' || tag === 'BODY') continue;
        const s = window.getComputedStyle(el);
        if (s.display === 'none' || s.visibility === 'hidden') continue;
        if (s.position !== 'fixed' && s.position !== 'absolute') continue;
        if (parseFloat(s.opacity || '1') < 0.3) continue;
        const r = el.getBoundingClientRect();
        if (r.width >= minW && r.height >= minH) return true;
    }
    return false;
}
"""


@dataclass
class RenderResult:
    url: str
    rendered_word_count: int = 0
    is_soft_404: bool = False
    has_fullscreen_overlay: bool = False
    error: str = ""


class PlaywrightRenderer:
    """
    Optional Playwright-based renderer.
    Detects soft 404s (200 status + error content) and fullscreen
    interstitials/overlays that block page content from Googlebot.

    Install: pip install playwright && playwright install chromium
    Enable:  set execution.use_renderer: true in config.yaml
    """

    def __init__(self, timeout_ms: int = 12000) -> None:
        self.timeout_ms = timeout_ms

    @property
    def available(self) -> bool:
        return PLAYWRIGHT_AVAILABLE

    def render_pages(self, urls: list[str]) -> list[RenderResult]:
        if not PLAYWRIGHT_AVAILABLE:
            return [RenderResult(url=u, error="playwright not installed — run: pip install playwright && playwright install chromium") for u in urls]

        results: list[RenderResult] = []
        try:
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                for url in urls:
                    result = RenderResult(url=url)
                    try:
                        page = browser.new_page(viewport={"width": 1280, "height": 800})
                        page.goto(url, timeout=self.timeout_ms, wait_until="domcontentloaded")

                        body_text = page.inner_text("body") or ""
                        words = body_text.split()
                        result.rendered_word_count = len(words)

                        body_lower = body_text.lower()
                        result.is_soft_404 = (
                            len(words) < 150
                            and any(phrase in body_lower for phrase in _SOFT_404_PHRASES)
                        )
                        result.has_fullscreen_overlay = bool(page.evaluate(_OVERLAY_JS))
                        page.close()
                    except Exception as exc:
                        result.error = str(exc)[:200]
                    results.append(result)
                browser.close()
        except Exception as exc:
            rendered_urls = {r.url for r in results}
            for url in urls:
                if url not in rendered_urls:
                    results.append(RenderResult(url=url, error=str(exc)[:200]))
        return results
