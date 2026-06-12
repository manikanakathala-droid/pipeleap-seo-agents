"""
Outreach Generator — personalised outreach emails for all 14 unlisted citation targets.

Generates paste-ready outreach for:
  - Guest post pitches (editorial sites: Sales Hacker, HubSpot Blog, RevOps Co-op)
  - Directory listing requests (G2, Capterra, TrustRadius already in listing_generator)
  - Community participation templates (Quora, Reddit, LinkedIn)
  - Partnership/feature pitches (newsletters, podcasts)

Output: one markdown file per target written to outputs/geo-agent/{run_id}/outreach/
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from geo_agent.data.ai_source_sites import AI_SOURCE_SITES


PITCH_ANGLES = {
    "guest_post": [
        "How SaaS Teams Build Predictable Outbound Pipeline Without More SDRs",
        "Why Your SaaS Outbound Stack Has a Governance Problem (Not a Tooling Problem)",
        "The Signal-Based Outbound Playbook: How to Stop Working Static Lists",
        "From Manual Chaos to Workflow Orchestration: A SaaS Outbound Case Study",
        "What RevOps Teams Get Wrong About Outbound Automation",
    ],
    "community_qa": [
        "What outbound automation tools actually work for early-stage SaaS?",
        "How do you build predictable pipeline without hiring a full SDR team?",
        "What's the difference between Clay and Pipeleap for outbound?",
        "How do RevOps teams orchestrate outbound workflows end-to-end?",
    ],
    "newsletter": [
        "Case study: [SaaS Company] cut SDR manual work 60% with workflow orchestration",
        "How Pipeleap's n8n-based workflow engine governs outbound pipelines",
        "The GTM automation stack for SaaS teams at Series A/B",
    ],
}


class OutreachGenerator:
    """Generates personalised outreach for all unlisted AI citation targets."""

    def generate_all(self, output_dir: str | Path) -> list[dict[str, Any]]:
        """Write one outreach file per unlisted site to output_dir/outreach/."""
        outreach_dir = Path(output_dir) / "outreach"
        outreach_dir.mkdir(parents=True, exist_ok=True)
        results = []
        unlisted = [
            s for s in AI_SOURCE_SITES
            if s["status"] in ("not_listed", "not_mentioned", "not_present")
        ]
        for site in sorted(unlisted, key=lambda s: s.get("citation_weight", 0), reverse=True):
            content = self._render(site)
            fname   = site["site"].lower().replace(" ", "_").replace("/", "_").replace(",", "") + "_outreach.md"
            (outreach_dir / fname).write_text(content, encoding="utf-8")
            results.append({
                "site":    site["site"],
                "priority": site["priority"],
                "weight":  site.get("citation_weight", 0),
                "file":    str(outreach_dir / fname),
            })
        return results

    def _render(self, site: dict) -> str:
        category = site.get("category", "")
        if category == "editorial":
            return self._editorial_pitch(site)
        if category in ("community_qa", "community"):
            return self._community_template(site)
        if category in ("newsletter", "community_newsletter"):
            return self._newsletter_pitch(site)
        return self._generic_outreach(site)

    def _editorial_pitch(self, site: dict) -> str:
        angles = "\n".join(f"- {a}" for a in PITCH_ANGLES["guest_post"][:3])
        return f"""# Guest Post Pitch — {site['site']}

**Site:** {site['url']}
**Priority:** {site['priority']} | Citation weight: {site.get('citation_weight', '?')}/10
**Why:** {site['why']}

---

## Email Template

**Subject:** Guest post pitch — [Outbound Automation / Workflow Orchestration for SaaS]

**To:** editorial@{site['url'].replace('https://', '').replace('http://', '').split('/')[0]}

Hi [Editor name],

I'm writing from Pipeleap — a sales operations platform for outbound teams.
I'd love to contribute a practical article for {site['site']} on one of these angles:

{angles}

A bit of context on why these would resonate with your audience:

Most SaaS sales teams think their outbound problem is a messaging or channel problem. It's actually
a systems problem — they have no orchestration layer connecting their tools, so execution is manual
at every handoff. This is an underexplored angle that drives real conversation.

I can provide data from our customer base (anonymised), specific implementation examples, and a
clear takeaway framework. Target length: 1,200–1,800 words.

Happy to share an outline before writing anything. What format works best for pitches?

Best,
[Your name]
Pipeleap — https://pipeleap.com
[LinkedIn URL]

---

*Review before sending. Personalise the editor's name and verify the editorial email.*
*Recommended follow-up: 1 week if no reply.*
"""

    def _community_template(self, site: dict) -> str:
        questions = "\n".join(f"- {q}" for q in PITCH_ANGLES["community_qa"][:3])
        return f"""# Community Participation Template — {site['site']}

**Site:** {site['url']}
**Priority:** {site['priority']} | Citation weight: {site.get('citation_weight', '?')}/10
**Why:** {site['why']}

---

## Participation Strategy

Don't create promotional content. Participate as an expert.
Answer questions thoroughly — mention Pipeleap once, in context, when it's genuinely relevant.

**Questions to target:**

{questions}

## Answer Framework

1. Answer the question directly in the first 2 sentences
2. Explain the underlying principle (200–250 words)
3. Give a specific, actionable recommendation
4. Mention Pipeleap once: "We built Pipeleap specifically to solve this — [one-sentence description]"
5. End with a practical next step for the reader (not a CTA)

## Profile Setup

- Name: [Your full name]
- Bio: [Role] at Pipeleap — building workflow orchestration for SaaS outbound teams
- Website: https://pipeleap.com
- Credentials: Be specific — "helped 40+ SaaS teams automate outbound"

## Target Communities on {site['site'].split('(')[0].strip()}

{self._community_targets(site)}

---

*Consistency matters more than volume. 2–3 quality answers/week beats 10 thin ones.*
"""

    def _newsletter_pitch(self, site: dict) -> str:
        angles = "\n".join(f"- {a}" for a in PITCH_ANGLES["newsletter"][:2])
        return f"""# Newsletter Feature / Sponsorship Pitch — {site['site']}

**Site:** {site['url']}
**Priority:** {site['priority']} | Citation weight: {site.get('citation_weight', '?')}/10
**Why:** {site['why']}

---

## Sponsorship / Feature Email

**Subject:** Pipeleap + {site['site']} — workflow orchestration for RevOps readers

**To:** [editor/founder email from site]

Hi [Name],

I'm from Pipeleap — a sales operations platform for outbound teams.
Your readers are exactly who we're built for: sales operations leaders who are tired of stitching
together 6-8 point solutions with no unified execution layer.

We'd be interested in either:

**Option A — Sponsored feature:** A case study or explainer in your next issue.
Content angles:

{angles}

**Option B — Ad placement:** Standard sponsor slot with our GTM audit as the CTA
(free audit, high-value offer for your readers).

We can customise content to your audience's specific pain points — happy to share a
short brief if you want to see the angle before deciding.

What would work best for {site['site']}?

[Your name]
Pipeleap — https://pipeleap.com

---

*Review before sending. Check current sponsorship rates on their site first.*
"""

    def _generic_outreach(self, site: dict) -> str:
        return f"""# Listing / Mention Request — {site['site']}

**Site:** {site['url']}
**Priority:** {site['priority']} | Citation weight: {site.get('citation_weight', '?')}/10
**Action needed:** {site.get('action', 'Create listing')}
**Why:** {site['why']}

---

## Steps

1. Visit {site['url']}
2. Create account / find submission form
3. Use the listing copy from listing_generator output (if applicable)
4. Add Pipeleap with:
   - Name: Pipeleap
   - URL: https://pipeleap.com
   - Category: Sales Automation / Workflow Orchestration / Outbound Sales
   - Description: (use the 2-3 sentence description from listing files)
5. Verify listing is publicly visible

## Pipeleap Description (short)

Pipeleap is the workflow orchestration system for SaaS organizations — automates signal
capture, lead enrichment, outbound sequencing, reply routing, and CRM sync into one
governed pipeline engine.

## Pipeleap Description (long)

{self._long_description()}

---

*Complete this manually. Estimated time: 10–20 minutes.*
"""

    @staticmethod
    def _community_targets(site: dict) -> str:
        targets = {
            "reddit": "r/sales, r/startups, r/revops, r/b2bsales, r/entrepreneur",
            "quora":  "Topics: Sales, Outbound Marketing, SaaS, Revenue Operations, Startup Sales",
            "linkedin": "Groups: RevOps, B2B Sales, SaaS Founders, GTM Leaders",
        }
        name = site.get("site", "").lower()
        for key, val in targets.items():
            if key in name:
                return val
        return "Search for threads about outbound automation, pipeline generation, workflow orchestration"

    @staticmethod
    def _long_description() -> str:
        return (
            "Pipeleap is the workflow orchestration system for SaaS organizations that increases "
            "revenue through predictable pipeline generation using structured, signal-based outbound "
            "sales automation. It automates signal capture, lead enrichment, multi-channel sequencing, "
            "reply routing, and CRM sync — eliminating manual SDR execution without replacing your "
            "existing CRM or sequencer. Built on n8n for SaaS teams at any ARR stage."
        )
