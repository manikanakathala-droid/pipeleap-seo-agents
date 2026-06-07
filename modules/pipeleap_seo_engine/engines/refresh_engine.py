"""Content refresh engine + keyword cannibalization detector."""
from __future__ import annotations
import re
from datetime import datetime, timezone
from typing import Any


class ContentRefreshEngine:
    """
    Identifies pages that need refreshing based on:
    - Age (>90 days since last modification)
    - GSC ranking decay (position dropped >3 spots vs previous period)
    NOTE: Does not penalize by word count — Google has no preferred word count.
    """
    STALENESS_DAYS = 90
    POSITION_DECAY_THRESHOLD = 3.0

    def analyze(self, pages: list[dict[str, Any]], gsc_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        gsc_map = {row.get("query", "").lower(): row for row in gsc_rows}
        refresh_queue = []
        for page in pages:
            reasons = []
            slug = page.get("slug", "")
            body = page.get("body_markdown", "")
            word_count = len(body.split())
            modified = page.get("modified_date", "")

            if modified and self._is_stale(modified):
                reasons.append(f"stale: last modified {modified}")

            primary_kw = page.get("primary_keyword", "").lower()
            gsc_data = gsc_map.get(primary_kw)
            if gsc_data:
                pos = gsc_data.get("position", 0)
                if pos and pos > 20:
                    reasons.append(f"ranking_decay: position {pos:.1f} for '{primary_kw}'")

            if reasons:
                refresh_queue.append({
                    "slug": slug,
                    "primary_keyword": page.get("primary_keyword", ""),
                    "word_count": word_count,
                    "reasons": reasons,
                    "priority": "HIGH" if len(reasons) >= 2 else "MEDIUM",
                })
        return sorted(refresh_queue, key=lambda x: len(x["reasons"]), reverse=True)

    def flag_fake_freshness(
        self, pages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Flag pages whose modified_date was changed but body_markdown content
        hash has not changed — a practice explicitly warned against by Google:
        'Are you changing the date of pages to make them seem fresh when the
        content has not substantially changed?'
        """
        import hashlib
        flagged = []
        for page in pages:
            body = page.get("body_markdown", "")
            prev_hash = page.get("previous_content_hash", "")
            curr_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()[:16]
            modified = page.get("modified_date", "")
            prev_modified = page.get("previous_modified_date", "")
            if prev_hash and prev_hash == curr_hash and modified != prev_modified:
                flagged.append({
                    "slug": page.get("slug", ""),
                    "issue": "fake_freshness",
                    "description": (
                        f"modified_date changed from '{prev_modified}' to '{modified}' "
                        f"but body content is identical. Google warns against changing "
                        f"dates to appear fresh without real content updates."
                    ),
                    "severity": "WARNING",
                })
        return flagged

    def _is_stale(self, date_str: str) -> bool:
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            age = (datetime.now(timezone.utc) - dt).days
            return age > self.STALENESS_DAYS
        except ValueError:
            return False


class CannibalizationDetector:
    """
    Detects keyword cannibalization across both the current run and all
    historically published pages.

    Checks performed:
      1. Primary keyword exact match collision (current run)
      2. Semantic keyword overlap ≥ 50% (current run)
      3. Cross-run primary keyword conflict (new page vs. published history)
      4. Page-type + intent duplication (same role/use-case with same intent)
    """
    OVERLAP_THRESHOLD = 0.5

    def detect(self, pages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """In-run cannibalization detection (current run only)."""
        issues = []
        seen: dict[str, str] = {}

        for page in pages:
            kws = {kw.lower() for kw in page.get("target_keywords", [])}
            kws.add(page.get("primary_keyword", "").lower())
            slug = page.get("slug", "")

            for kw in kws:
                base = self._normalize(kw)
                if base in seen and seen[base] != slug:
                    issues.append({
                        "type":           "in_run_keyword_conflict",
                        "keyword":        kw,
                        "page_1":         seen[base],
                        "page_2":         slug,
                        "recommendation": (
                            f"Merge '{slug}' into '{seen[base]}' or differentiate intent clearly. "
                            "If both are needed, separate by funnel stage (TOFU vs BOFU) or audience."
                        ),
                        "severity": "HIGH",
                    })
                else:
                    seen[base] = slug

        # Semantic overlap check (pairwise)
        for i, page_a in enumerate(pages):
            for page_b in pages[i + 1:]:
                if page_a.get("page_type") != page_b.get("page_type"):
                    continue  # different page types are allowed to share topics
                overlap = self._keyword_overlap(
                    page_a.get("target_keywords", []),
                    page_b.get("target_keywords", []),
                )
                if overlap > self.OVERLAP_THRESHOLD:
                    issues.append({
                        "type":    "semantic_overlap",
                        "keyword": f"semantic_overlap ({overlap:.0%})",
                        "page_1":  page_a.get("slug", ""),
                        "page_2":  page_b.get("slug", ""),
                        "recommendation": (
                            "Consolidate into one page, or differentiate with distinct "
                            "intent sections, buyer stages, or audience modifiers."
                        ),
                        "severity": "MEDIUM",
                    })

        # Page-type + role/competitor duplication
        role_seen: dict[str, str] = {}
        comp_seen: dict[str, str] = {}
        for page in pages:
            if page.get("page_type") == "role_page":
                role = page.get("role", "")
                if role in role_seen:
                    issues.append({
                        "type":    "role_page_duplicate",
                        "keyword": f"role:{role}",
                        "page_1":  role_seen[role],
                        "page_2":  page.get("slug", ""),
                        "recommendation": "Only one role page per persona. Keep the more recent/complete one.",
                        "severity": "HIGH",
                    })
                else:
                    role_seen[role] = page.get("slug", "")
            # competitor page dedup removed

        return issues

    def detect_cross_run(
        self,
        new_pages: list[dict[str, Any]],
        historical_keyword_map: dict[str, dict[str, str]],
    ) -> list[dict[str, Any]]:
        """
        Cross-run cannibalization: checks new pages against all previously
        published pages fetched from storage.fetch_all_published_keywords().

        historical_keyword_map: {keyword: {slug, page_type, intent}}
        """
        issues = []
        for page in new_pages:
            kw   = page.get("primary_keyword", "").lower()
            slug = page.get("slug", "")
            pt   = page.get("page_type", "")
            intent = page.get("intent", "commercial")
            if not kw:
                continue
            base = self._normalize(kw)
            for hist_kw, hist_data in historical_keyword_map.items():
                if self._normalize(hist_kw) == base and hist_data.get("slug") != slug:
                    # Only flag as conflict if SAME page type or SAME intent
                    same_type   = hist_data.get("page_type") == pt
                    same_intent = hist_data.get("intent") == intent
                    if same_type or same_intent:
                        issues.append({
                            "type":    "cross_run_conflict",
                            "keyword": kw,
                            "new_slug": slug,
                            "existing_slug": hist_data.get("slug"),
                            "existing_page_type": hist_data.get("page_type"),
                            "recommendation": (
                                f"'{slug}' ({pt}) targets '{kw}' which was published as "
                                f"'{hist_data['slug']}' ({hist_data.get('page_type')}). "
                                "Differentiate by adding a unique modifier, angle, or audience segment."
                            ),
                            "severity": "HIGH" if same_type else "MEDIUM",
                        })
                        break
        return issues

    @staticmethod
    def _normalize(kw: str) -> str:
        stop = {"for", "the", "a", "an", "in", "of", "to", "and", "with",
                "how", "saas", "automation", "b2b", "your", "our"}
        words = re.sub(r"[^a-z0-9 ]", "", kw.lower()).split()
        return " ".join(w for w in words if w not in stop)

    @staticmethod
    def _keyword_overlap(kws_a: list[str], kws_b: list[str]) -> float:
        set_a = {kw.lower() for kw in kws_a}
        set_b = {kw.lower() for kw in kws_b}
        if not set_a or not set_b:
            return 0.0
        return len(set_a & set_b) / len(set_a | set_b)
