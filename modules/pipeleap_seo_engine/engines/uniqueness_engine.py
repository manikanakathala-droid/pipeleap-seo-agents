"""
Content uniqueness engine for the Pipeleap SaaS Growth Engine.

Provides six layers of duplicate prevention:

  Layer 1 — Page-level Jaccard shingle similarity (was broken: fixed)
  Layer 2 — Paragraph-level hash deduplication (new)
  Layer 3 — Semantic angle tracking per topical pillar (new)
  Layer 4 — Intent × page-type isolation guard (new)
  Layer 5 — CTA pattern deduplication (new)
  Layer 6 — Topic ownership / canonical claim registry (new)

Critical bug fixed: the orchestrator was storing SHA-256 *hashes* in the
fingerprints list and then calling _shingle() on those hex strings. A 64-char
hex hash produces exactly one "word" after tokenisation, so Jaccard similarity
against content text shingles was always 0 — every page scored 1.0 (unique).

Fix: the fingerprints list now stores *raw text* so _shingle() operates on
actual content. The SHA-256 hash is retained as an exact-match shortcut only.
"""
from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any


# ── Stop words for semantic angle normalisation ───────────────────────────────
_ANGLE_STOP = {
    "the", "a", "an", "of", "in", "on", "and", "or", "for", "with", "how",
    "to", "is", "your", "our", "its", "by", "from", "that", "at", "this",
    "pipeleap", "saas",
}


class GrowthUniquenessEngine:
    """
    Multi-layer content uniqueness engine.

    Usage in orchestrator:
        engine = GrowthUniquenessEngine()
        # Pass raw text corpus (NOT hashes) to score() and register()
        corpus: list[str] = []
        for page in all_pages:
            score = engine.score(page.body_markdown, corpus)
            page.uniqueness_score = score
            if score >= engine.PUBLISH_THRESHOLD:
                corpus.append(page.body_markdown)   # register raw text
    """

    PUBLISH_THRESHOLD = 0.65   # stricter: only 35% similarity allowed
    WARN_THRESHOLD    = 0.75   # flag pages between 0.65–0.75 for review

    # Programmatic SEO page types that are intentionally structurally similar.
    PROGRAMMATIC_TYPES = {"market_page", "use_case_page", "integration_page", "workflow_page", "workflow_recipe"}
    PROGRAMMATIC_THRESHOLD = 0.45  # was 0.25 (too low)
    SHINGLE_N         = 4      # 4-gram shingles for stricter comparison
    PARA_MIN_WORDS    = 15     # lower word count for paragraph-level check (more sensitive)

    def score(self, candidate: str, existing_texts: list[str]) -> float:
        """
        Layer 1: page-level Jaccard similarity against corpus of raw texts.
        Returns 0.0–1.0. 1.0 = fully unique, 0.0 = identical.

        NOTE: existing_texts must be raw content strings, NOT SHA-256 hashes.
        The orchestrator bug was passing hashes here — now fixed at call site.
        """
        if not existing_texts:
            return 1.0
        candidate_shingles = self._shingle(candidate)
        if not candidate_shingles:
            return 1.0
        max_sim = max(
            self._jaccard(candidate_shingles, self._shingle(text))
            for text in existing_texts
        )
        return round(max(0.0, 1.0 - max_sim), 3)

    def fingerprint(self, text: str) -> str:
        """SHA-256 hash of normalised text. Used for exact-match dedup only."""
        normalised = re.sub(r"[^a-z0-9 ]", "", text.lower())
        normalised = re.sub(r"\s+", " ", normalised).strip()
        return hashlib.sha256(normalised.encode()).hexdigest()

    def is_duplicate(self, candidate: str, existing_texts: list[str], threshold: float | None = None) -> bool:
        t = threshold if threshold is not None else self.PUBLISH_THRESHOLD
        return self.score(candidate, existing_texts) < t

    # ── Layer 2: paragraph-level deduplication ────────────────────────────────

    def paragraph_hashes(self, text: str) -> set[str]:
        """
        Extract MD5 hashes for every paragraph with >= PARA_MIN_WORDS words.
        Used to detect when the same paragraph is copy-pasted across pages.
        """
        paras = re.split(r"\n{2,}", text.strip())
        hashes: set[str] = set()
        for para in paras:
            clean = re.sub(r"[#*`>\-|]", "", para).strip()
            words = clean.split()
            if len(words) >= self.PARA_MIN_WORDS:
                hashes.add(hashlib.md5(clean.lower().encode()).hexdigest())
        return hashes

    def paragraph_overlap(self, candidate: str, existing_texts: list[str]) -> float:
        """
        Returns fraction of candidate paragraphs that already exist verbatim
        in the corpus. 0.0 = all unique, 1.0 = all duplicated.
        """
        candidate_hashes = self.paragraph_hashes(candidate)
        if not candidate_hashes:
            return 0.0
        corpus_hashes: set[str] = set()
        for text in existing_texts:
            corpus_hashes |= self.paragraph_hashes(text)
        shared = candidate_hashes & corpus_hashes
        return round(len(shared) / len(candidate_hashes), 3)

    # ── Layer 3: semantic angle tracking ─────────────────────────────────────

    def extract_angle(self, title: str, primary_keyword: str) -> str:
        """
        Normalise the semantic angle of a page to a canonical key.
        Used to detect when multiple pages cover the same angle under a pillar.
        E.g. "How VP Sales automates outbound" and "VP Sales outbound automation"
        both normalise to "vp sales outbound".
        """
        combined = f"{title} {primary_keyword}".lower()
        words = re.sub(r"[^a-z0-9 ]", "", combined).split()
        core = [w for w in words if w not in _ANGLE_STOP]
        return " ".join(sorted(set(core)))[:120]

    def angle_is_duplicate(
        self,
        title: str,
        primary_keyword: str,
        registered_angles: dict[str, str],   # angle_key → slug
        slug: str,
    ) -> tuple[bool, str]:
        """
        Returns (is_duplicate, conflicting_slug).
        If the normalised angle already exists under a different slug, it's a dup.
        """
        angle = self.extract_angle(title, primary_keyword)
        existing_slug = registered_angles.get(angle, "")
        if existing_slug and existing_slug != slug:
            return True, existing_slug
        return False, ""

    # ── Layer 4: intent × page-type isolation guard ──────────────────────────

    ALLOWED_INTENT_PAGE_TYPE_COMBOS: set[tuple[str, str]] = {
        # informational intent
        ("informational", "blog_post"),
        ("informational", "glossary_page"),
        ("informational", "problem_page"),
        # commercial intent
        ("commercial",    "comparison_page"),
        ("commercial",    "alternative_page"),
        ("commercial",    "multi_competitor_page"),
        ("commercial",    "use_case_page"),
        ("commercial",    "integration_page"),
        ("commercial",    "role_page"),
        # transactional intent
        ("transactional", "landing_page"),
        ("transactional", "bofu_page"),
        ("transactional", "objection_page"),
        ("transactional", "roi_page"),
        ("transactional", "demo_page"),
        # workflow / how-to
        ("informational", "workflow_page"),
        ("informational", "workflow_recipe"),
        ("commercial",    "workflow_page"),
        ("commercial",    "workflow_recipe"),
    }

    def intent_page_type_valid(self, intent: str, page_type: str) -> bool:
        """Returns True if the intent × page_type combination is architecturally valid."""
        return (intent, page_type) in self.ALLOWED_INTENT_PAGE_TYPE_COMBOS

    def keyword_intent_conflict(
        self,
        keyword: str,
        intent: str,
        page_type: str,
        intent_registry: dict[str, tuple[str, str]],   # keyword → (intent, page_type)
    ) -> tuple[bool, str]:
        """
        Detect when a keyword is already owned by a page with a different intent
        or page type. Returns (conflict_found, description).
        """
        existing = intent_registry.get(keyword.lower())
        if not existing:
            return False, ""
        existing_intent, existing_page_type = existing
        if existing_intent == intent and existing_page_type == page_type:
            return False, ""
        return True, (
            f"'{keyword}' already claimed by page_type='{existing_page_type}' "
            f"intent='{existing_intent}'. New: page_type='{page_type}' intent='{intent}'."
        )

    # ── Layer 5: CTA pattern deduplication ───────────────────────────────────

    def normalise_cta(self, cta_text: str) -> str:
        """Normalise CTA copy to detect identical patterns across pages."""
        clean = re.sub(r"[^a-z0-9 ]", "", cta_text.lower())
        return re.sub(r"\s+", " ", clean).strip()[:80]

    def cta_is_overused(
        self,
        cta_text: str,
        cta_registry: dict[str, int],   # normalised_cta → count
        max_uses: int = 5,
    ) -> bool:
        """Returns True if this CTA pattern has been used >= max_uses times already."""
        key = self.normalise_cta(cta_text)
        return cta_registry.get(key, 0) >= max_uses

    def register_cta(self, cta_text: str, cta_registry: dict[str, int]) -> None:
        """Increment the CTA usage count."""
        key = self.normalise_cta(cta_text)
        cta_registry[key] = cta_registry.get(key, 0) + 1

    # ── Layer 6: topic ownership ──────────────────────────────────────────────

    def topic_key(self, primary_keyword: str, topical_pillar: str) -> str:
        """Canonical topic key combining primary keyword + pillar."""
        kw = re.sub(r"[^a-z0-9 ]", "", primary_keyword.lower()).strip()
        pillar = re.sub(r"[^a-z0-9 ]", "", topical_pillar.lower()).strip()
        return f"{pillar}::{kw}"

    def claim_topic(
        self,
        primary_keyword: str,
        topical_pillar: str,
        slug: str,
        page_type: str,
        ownership_registry: dict[str, dict],   # topic_key → {slug, page_type}
    ) -> tuple[bool, dict]:
        """
        Attempt to claim canonical ownership of a topic for this page.
        Returns (claimed, existing_owner_dict).
        If the topic is already claimed by a different slug, returns (False, owner).
        If claimed by the same slug, returns (True, owner).
        If unclaimed, registers and returns (True, {}).
        """
        key = self.topic_key(primary_keyword, topical_pillar)
        existing = ownership_registry.get(key)
        if not existing:
            ownership_registry[key] = {"slug": slug, "page_type": page_type}
            return True, {}
        if existing["slug"] == slug:
            return True, existing
        return False, existing

    # ── Full page assessment ──────────────────────────────────────────────────

    def assess(
        self,
        page: Any,
        corpus_texts: list[str],
        angle_registry: dict[str, str],
        intent_registry: dict[str, tuple[str, str]],
        cta_registry: dict[str, int],
        topic_ownership: dict[str, dict],
    ) -> dict[str, Any]:
        """
        Run all six uniqueness layers against a candidate page.
        Returns a report dict with scores, flags, and a publish_decision.
        """
        slug          = getattr(page, "slug", "")
        title         = getattr(page, "title", "")
        body          = getattr(page, "body_markdown", "")
        kw            = getattr(page, "primary_keyword", "")
        page_type     = getattr(page, "page_type", "")
        intent        = getattr(page, "intent", "commercial")
        cta           = getattr(page, "call_to_action", "")
        pillar        = getattr(page, "topical_pillar", "")

        report: dict[str, Any] = {"slug": slug, "flags": [], "publish": True}

        # Use lower threshold for programmatic page types (intentionally templated)
        effective_threshold = (
            self.PROGRAMMATIC_THRESHOLD
            if page_type in self.PROGRAMMATIC_TYPES
            else self.PUBLISH_THRESHOLD
        )

        # L1: page-level similarity
        l1 = self.score(body, corpus_texts)
        report["page_similarity_score"] = l1
        if l1 < effective_threshold:
            report["flags"].append(f"L1:near_duplicate page_score={l1:.3f}")
            report["publish"] = False
        elif l1 < self.WARN_THRESHOLD and page_type not in self.PROGRAMMATIC_TYPES:
            report["flags"].append(f"L1:low_uniqueness page_score={l1:.3f} (review)")

        # L2: paragraph overlap
        l2 = self.paragraph_overlap(body, corpus_texts)
        report["paragraph_overlap"] = l2
        if l2 > 0.2:
            report["flags"].append(f"L2:paragraph_overlap={l2:.0%} of paragraphs reused")
            if l2 > 0.4:
                report["publish"] = False

        # L3: semantic angle
        is_angle_dup, conflict_slug = self.angle_is_duplicate(title, kw, angle_registry, slug)
        report["angle_duplicate"] = is_angle_dup
        if is_angle_dup:
            report["flags"].append(f"L3:angle_duplicate conflicts with '{conflict_slug}'")
            report["publish"] = False

        # L4: intent × page-type validity
        if not self.intent_page_type_valid(intent, page_type):
            report["flags"].append(f"L4:invalid_combo intent='{intent}' page_type='{page_type}'")
        kw_conflict, kw_conflict_msg = self.keyword_intent_conflict(kw, intent, page_type, intent_registry)
        report["keyword_conflict"] = kw_conflict
        if kw_conflict:
            report["flags"].append(f"L4:keyword_intent_conflict {kw_conflict_msg}")

        # L5: CTA overuse
        cta_overused = self.cta_is_overused(cta, cta_registry)
        report["cta_overused"] = cta_overused
        if cta_overused:
            report["flags"].append(f"L5:cta_overused '{cta[:50]}...' used ≥5 times")

        # L6: topic ownership
        if kw and pillar:
            claimed, existing_owner = self.claim_topic(kw, pillar, slug, page_type, topic_ownership)
            report["topic_owner"] = slug if claimed else existing_owner.get("slug", "")
            if not claimed and existing_owner.get("slug") != slug:
                report["flags"].append(
                    f"L6:topic_conflict '{kw}' already owned by '{existing_owner.get('slug')}'"
                )

        report["flag_count"] = len(report["flags"])
        return report

    # ── Layer 7: Scaled-content cluster volume guard ──────────────────────────

    # Google's spam policy flags sites that generate many pages targeting the
    # same topic without adding value. This guard caps new pages per topical
    # cluster per run so no single cluster is flooded.
    CLUSTER_PAGE_CAP = 8   # max new pages per cluster per orchestrator run

    def cluster_volume_ok(
        self,
        cluster: str,
        volume_registry: dict[str, int],
        cap: int | None = None,
    ) -> tuple[bool, str]:
        """
        Returns (ok, reason). Increments the in-memory counter if ok.
        Pass the same volume_registry dict throughout a single run so counts
        accumulate across all generator calls.
        """
        limit = cap if cap is not None else self.CLUSTER_PAGE_CAP
        count = volume_registry.get(cluster, 0)
        if count >= limit:
            return False, (
                f"Cluster '{cluster}' already has {count} pages this run "
                f"(cap={limit}). Skipping to avoid scaled-content abuse signal."
            )
        volume_registry[cluster] = count + 1
        return True, ""

    # ── Staleness ─────────────────────────────────────────────────────────────

    def needs_refresh(self, created_at_iso: str, staleness_days: int = 90) -> bool:
        try:
            created = datetime.fromisoformat(created_at_iso.replace("Z", "+00:00"))
            age = (datetime.now(timezone.utc) - created).days
            return age > staleness_days
        except (ValueError, TypeError):
            return False

    # ── Internals ─────────────────────────────────────────────────────────────

    def _shingle(self, text: str, n: int | None = None) -> set[str]:
        n = n or self.SHINGLE_N
        words = re.sub(r"[^a-z0-9 ]", "", text.lower()).split()
        if len(words) < n:
            return set(words)
        return {" ".join(words[i: i + n]) for i in range(len(words) - n + 1)}

    def _jaccard(self, a: set[str], b: set[str]) -> float:
        if not a and not b:
            return 0.0
        intersection = len(a & b)
        union = len(a | b)
        return intersection / union if union else 0.0
