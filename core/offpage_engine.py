from __future__ import annotations

"""
Off-Page SERP Expansion Engine — Pillars 3, 4, 7 of the SERP visibility strategy.

Responsibilities:
  - Generate a prioritised directory submission queue
  - Generate guest post pitch packages (subject, body, publication data)
  - Generate LinkedIn content briefs for the weekly cadence
  - Generate authority building action queue (HARO, partner co-marketing, community)
  - Track which directories/publications have already been actioned
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from modules.pipeleap_seo_engine.data.serp_strategy import (
    AUTHORITY_TIERS,
    BACKLINK_ANCHOR_VARIANTS,
    BRAND_MONITORING_QUERIES,
    DIRECTORY_TARGETS,
    GUEST_POST_TARGETS,
    LINKEDIN_CADENCE,
    SERP_KEYWORD_CLUSTERS,
)


@dataclass
class DirectorySubmission:
    name: str
    url: str
    category: str
    priority: int
    da: int
    status: str = "pending"
    action_notes: str = ""


@dataclass
class GuestPostPitch:
    publication: str
    url: str
    da: int
    pitch_angle: str
    contact: str
    email_subject: str = ""
    email_body: str = ""
    status: str = "pending"


@dataclass
class LinkedInBrief:
    week_number: int
    day: str
    format: str
    topic: str
    hook: str
    body_guidance: str
    cta: str
    target_keyword: str = ""


@dataclass
class AuthorityAction:
    tier: int
    tactic: str
    action_detail: str
    priority_score: float
    status: str = "pending"


@dataclass
class OffPageReport:
    run_id: str
    generated_at: str
    directory_queue: list[DirectorySubmission] = field(default_factory=list)
    guest_post_pitches: list[GuestPostPitch] = field(default_factory=list)
    linkedin_briefs: list[LinkedInBrief] = field(default_factory=list)
    authority_actions: list[AuthorityAction] = field(default_factory=list)
    brand_monitoring_setup: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "generated_at": self.generated_at,
            "directory_queue": [vars(d) for d in self.directory_queue],
            "guest_post_pitches": [vars(g) for g in self.guest_post_pitches],
            "linkedin_briefs": [vars(lb) for lb in self.linkedin_briefs],
            "authority_actions": [vars(a) for a in self.authority_actions],
            "brand_monitoring_setup": self.brand_monitoring_setup,
        }


class OffPageEngine:
    """
    Produces a weekly off-page action queue covering directories,
    guest posts, LinkedIn content, and authority-building tactics.
    All outputs are content and distribution actions only — no site code changes.
    """

    def __init__(self, config: dict[str, Any], logger) -> None:
        self.config = config
        self.logger = logger
        self.brand = config.get("site", {}).get("brand", "Pipeleap")
        self.site_url = config.get("site", {}).get("site_url", "https://pipeleap.com")

    def run(
        self,
        run_id: str,
        week_number: int | None = None,
        actioned_directories: set[str] | None = None,
        actioned_publications: set[str] | None = None,
    ) -> OffPageReport:
        now = datetime.now(timezone.utc)
        generated_at = now.isoformat()
        week_num = week_number or now.isocalendar()[1]
        actioned_dirs = actioned_directories or set()
        actioned_pubs = actioned_publications or set()

        report = OffPageReport(run_id=run_id, generated_at=generated_at)
        report.directory_queue = self._build_directory_queue(actioned_dirs)
        report.guest_post_pitches = self._build_guest_post_pitches(actioned_pubs)
        report.linkedin_briefs = self._build_linkedin_briefs(week_num)
        report.authority_actions = self._build_authority_actions()
        report.brand_monitoring_setup = BRAND_MONITORING_QUERIES

        self.logger.info(
            "OffPageEngine: %d directories | %d pitches | %d LinkedIn briefs | %d authority actions",
            len(report.directory_queue),
            len(report.guest_post_pitches),
            len(report.linkedin_briefs),
            len(report.authority_actions),
        )
        return report

    def _build_directory_queue(self, actioned: set[str]) -> list[DirectorySubmission]:
        queue: list[DirectorySubmission] = []
        for d in sorted(DIRECTORY_TARGETS, key=lambda x: (x["priority"], -x["da"])):
            status = "done" if d["url"] in actioned else "pending"
            notes = (
                "Submit listing in category: " + d["category"] + ". "
                "Use consistent NAP: Pipeleap, https://pipeleap.com, contact@pipeleap.com. "
                "Description: Pipeleap is a sales operations platform that orchestrates outbound sales workflows."
            )
            queue.append(DirectorySubmission(
                name=d["name"],
                url=d["url"],
                category=d["category"],
                priority=d["priority"],
                da=d["da"],
                status=status,
                action_notes=notes,
            ))
        return queue

    def _build_guest_post_pitches(self, actioned: set[str]) -> list[GuestPostPitch]:
        pitches: list[GuestPostPitch] = []
        top_cluster = SERP_KEYWORD_CLUSTERS[1]  # solution_evaluation — highest business fit

        for target in sorted(GUEST_POST_TARGETS, key=lambda x: -x["da"]):
            status = "done" if target["url"] in actioned else "pending"
            subject = f"Contributor idea for {target['publication']}: {target['pitch_angle']}"
            body = "\n".join([
                f"Hi {target['publication']} team,",
                "",
                f"I wanted to pitch a contributor piece aligned to what your audience cares about most right now.",
                "",
                f"Working title: {target['pitch_angle']}",
                "",
                "What the piece covers:",
                f"- Why {top_cluster['cluster_name'].replace('_', ' ')} is the defining challenge for B2B revenue teams in 2025",
                "- A practical framework your readers can apply immediately",
                "- Real workflow architecture diagrams and implementation steps",
                "- Outcome data from teams that have made the shift",
                "",
                "Why it fits your readers:",
                "- Written for operators, not evaluators — implementation-first, not vendor-first",
                "- Addresses demand around managed outbound and AI-assisted GTM",
                "- No product pitch in the body — the value is in the framework",
                "",
                "Happy to send a full outline within 48 hours.",
                "",
                "Best,",
                f"Rajiv Maanik, Pipeleap ({self.site_url})",
            ])

            pitches.append(GuestPostPitch(
                publication=target["publication"],
                url=target["url"],
                da=target["da"],
                pitch_angle=target["pitch_angle"],
                contact=target["contact"],
                email_subject=subject,
                email_body=body,
                status=status,
            ))
        return pitches

    def _build_linkedin_briefs(self, week_number: int) -> list[LinkedInBrief]:
        briefs: list[LinkedInBrief] = []
        slots = LINKEDIN_CADENCE["slots"]
        clusters = SERP_KEYWORD_CLUSTERS

        for i, slot in enumerate(slots):
            cluster = clusters[i % len(clusters)]
            primary_kw = cluster["keywords"][0]

            if slot["format"] == "insight":
                hook = f"Most B2B sales teams have a stack problem disguised as a pipeline problem."
                body = (
                    f"They buy {primary_kw.split()[0].capitalize()} tools. They hire SDRs. "
                    f"They add Clay. They add Apollo. They wait for pipeline.\n\n"
                    f"What they get is reps spending 65% of their day on admin.\n\n"
                    f"The insight nobody says out loud: the more tools you add, the worse the handoff tax gets.\n\n"
                    f"The fix is not another tool. It is one system that owns the entire chain."
                )
                cta = "Pipeleap runs the entire system for sales teams. Link in bio."
            else:
                hook = f"Here is the exact sequence we use to go from cold list to CRM opportunity in 72 hours."
                body = (
                    f"Step 1: Trigger from intent signal or list upload\n"
                    f"Step 2: Enrich with firmographic + technographic data\n"
                    f"Step 3: Score against ICP model (threshold: 70+)\n"
                    f"Step 4: Route to personalised outreach sequence\n"
                    f"Step 5: Handle reply, book meeting, write back to CRM\n\n"
                    f"The whole thing runs without a rep touching it until the meeting is booked.\n\n"
                    f"Pipeleap is built for {primary_kw}."
                )
                cta = "Deploys in 2 to 4 weeks. DM me if you want to see it."

            briefs.append(LinkedInBrief(
                week_number=week_number,
                day=slot["day"],
                format=slot["format"],
                topic=primary_kw,
                hook=hook,
                body_guidance=body,
                cta=cta,
                target_keyword=primary_kw,
            ))

        return briefs

    def _build_authority_actions(self) -> list[AuthorityAction]:
        actions: list[AuthorityAction] = []
        priority_by_tier = {1: 90.0, 2: 60.0, 3: 30.0}

        for tier_def in AUTHORITY_TIERS:
            tier = tier_def["tier"]
            for tactic in tier_def["tactics"]:
                if "guest post" in tactic.lower():
                    detail = (
                        "Use the guest post pitch template from OffPageEngine. "
                        "Target DA 70+ publications. Vary anchor text per BACKLINK_ANCHOR_VARIANTS."
                    )
                elif "linkedin" in tactic.lower():
                    detail = (
                        "Use LinkedIn brief from OffPageEngine. "
                        "Post Monday insight + Thursday how-to. "
                        "Start The Outbound Letter newsletter — weekly, indexes on Google."
                    )
                elif "product hunt" in tactic.lower():
                    detail = (
                        "Full Product Hunt launch. "
                        "Prep: hunter with 500+ followers, 50 upvotes in first hour. "
                        "Generates ~50 high-DA backlinks automatically."
                    )
                elif "haro" in tactic.lower() or "connectively" in tactic.lower():
                    detail = (
                        "Check HARO / Connectively daily for queries tagged: "
                        "sales automation, AI in sales, GTM strategy, outbound prospecting. "
                        "Respond within 1 hour of alert for best placement odds."
                    )
                elif "podcast" in tactic.lower():
                    detail = (
                        "Pitch: 30 Minutes to Presidents Club, The Sales Evangelist, Make It Happen Mondays. "
                        "Lead with: how Pipeleap reduces SDR admin from 65% to under 20% of their day. "
                        "Request show notes link to pipeleap.com."
                    )
                else:
                    detail = tactic

                actions.append(AuthorityAction(
                    tier=tier,
                    tactic=tactic,
                    action_detail=detail,
                    priority_score=priority_by_tier[tier],
                ))

        return sorted(actions, key=lambda a: -a.priority_score)
