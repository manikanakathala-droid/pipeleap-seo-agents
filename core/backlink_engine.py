from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from utils.models import BacklinkOpportunity, KeywordCluster
from utils.storage import SEOStorage

_AUTHORITY_THRESHOLD = 75
_RECONTACT_DAYS = 30          # skip prospects contacted within this window


class BacklinkEngine:
    """
    Builds a practical outreach queue for Pipeleap's authority-building efforts.

    Improvements over v1:
    - Deduplicates against backlink_contacts table — never regenerates the same
      prospect within _RECONTACT_DAYS, so every run produces a fresh queue.
    - Logs each opportunity to backlink_contacts with status='pending' so
      human operators can update to 'sent' / 'replied' / 'declined'.
    - Deduplicates prospect_seeds config entries (Capterra appeared twice).
    - Skips low-authority prospects (< _AUTHORITY_THRESHOLD).
    """

    def __init__(self, config: dict[str, Any], logger) -> None:
        self.config = config
        self.logger = logger
        self.site = config.get("site", {})
        self.prospects = self._dedup_prospects(
            config.get("backlinks", {}).get("prospect_seeds", [])
        )

    def build(
        self,
        clusters: list[KeywordCluster],
        storage: SEOStorage | None = None,
        run_id: str = "",
    ) -> list[BacklinkOpportunity]:
        if not self.prospects:
            return []

        # Load recently-contacted URLs to avoid re-queuing them
        recently_contacted: set[str] = set()
        if storage:
            try:
                recently_contacted = storage.fetch_contacted_prospect_urls(
                    within_days=_RECONTACT_DAYS
                )
            except Exception as exc:
                self.logger.warning("Could not load backlink contact history: %s", exc)

        top_cluster = clusters[0] if clusters else None
        opportunities: list[BacklinkOpportunity] = []
        now_iso = datetime.now(timezone.utc).isoformat()

        for prospect in self.prospects:
            if not isinstance(prospect, dict):
                continue

            prospect_url = prospect.get("url", "")
            prospect_name = prospect.get("name", "Prospect")

            # Skip low-authority
            authority = prospect.get("authority_hint", 0)
            if authority < _AUTHORITY_THRESHOLD:
                self.logger.debug(
                    "Skipping low-authority prospect: %s (authority=%s)", prospect_name, authority
                )
                continue

            # Skip recently contacted
            if prospect_url in recently_contacted:
                self.logger.info(
                    "Skipping recently-contacted prospect: %s (within %d days)",
                    prospect_name, _RECONTACT_DAYS,
                )
                continue

            target_cluster = self._best_cluster_for_prospect(prospect, clusters) or top_cluster
            if not target_cluster:
                continue

            category = prospect.get("category", "guest_post")
            angle = (
                f"Pitch a workflow-led piece around {target_cluster.primary_keyword} and show how "
                f"Pipeleap connects outbound, enrichment, and CRM automation in one governed system."
            )
            subject = (
                f"Contributor idea for {prospect_name}: "
                f"a practical guide to {target_cluster.primary_keyword}"
            )
            email_body = "\n".join([
                f"Hi {prospect_name} team,",
                "",
                f"I'm reaching out with a contributor idea for your {category.replace('_', ' ')} audience.",
                (
                    f"We can share a practical teardown of {target_cluster.primary_keyword} focused on "
                    f"real RevOps execution: enrichment, CRM write-back, outbound triggers, and demo routing."
                ),
                "",
                "Why it fits your readers:",
                "- Written for teams operationalising automation, not just evaluating it.",
                "- Includes workflow architecture diagrams and implementation steps.",
                "- Addresses current demand around AI SDR and revenue automation systems.",
                "",
                "Happy to send a detailed outline and screenshots of the workflow.",
                "",
                "Best,",
                "Pipeleap team",
            ])

            opp = BacklinkOpportunity(
                prospect_name=prospect_name,
                prospect_url=prospect_url,
                category=category,
                relevance_reason=prospect.get(
                    "relevance_reason",
                    f"Audience overlap with {target_cluster.cluster_name} and revenue automation buyers.",
                ),
                outreach_angle=angle,
                outreach_email_subject=subject,
                outreach_email_body=email_body,
                estimated_authority=float(authority),
            )
            opportunities.append(opp)

            # Register in contact tracker so we don't re-queue next run
            if storage and run_id:
                try:
                    storage.upsert_backlink_contact(
                        prospect_url=prospect_url,
                        prospect_name=prospect_name,
                        category=category,
                        status="pending",
                        run_id=run_id,
                        created_at=now_iso,
                    )
                except Exception as exc:
                    self.logger.warning("Failed to log backlink contact %s: %s", prospect_url, exc)

        if recently_contacted:
            self.logger.info(
                "Backlink engine: %d new opportunities queued, %d skipped (recently contacted)",
                len(opportunities), len(recently_contacted),
            )

        return opportunities

    @staticmethod
    def _dedup_prospects(prospects: list[Any]) -> list[dict[str, Any]]:
        """Remove duplicate entries by URL (config sometimes has duplicates)."""
        seen: set[str] = set()
        deduped: list[dict[str, Any]] = []
        for p in prospects:
            if not isinstance(p, dict):
                continue
            url = p.get("url", "")
            if url and url not in seen:
                seen.add(url)
                deduped.append(p)
        return deduped

    @staticmethod
    def _best_cluster_for_prospect(
        prospect: dict[str, Any],
        clusters: list[KeywordCluster],
    ) -> KeywordCluster | None:
        prospect_text = " ".join(
            [
                str(prospect.get("name", "")),
                str(prospect.get("category", "")),
                str(prospect.get("relevance_reason", "")),
            ]
        ).lower()
        best_cluster = None
        best_score = -1
        for cluster in clusters:
            score = 0
            if cluster.cluster_name.lower() in prospect_text:
                score += 2
            if cluster.primary_keyword.lower() in prospect_text:
                score += 3
            score += int(cluster.aggregate_conversion_potential * 10)
            if score > best_score:
                best_cluster = cluster
                best_score = score
        return best_cluster
