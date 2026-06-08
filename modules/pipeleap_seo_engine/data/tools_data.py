"""
Curated tools page seed data.

Rules enforced here:
- One entry per tool category — no duplicate categories
- No calculators, ROI estimators, capacity planners, or generic benchmarks
- Pipeleap is never described as an alternative to the tool on the page
- Each entry frames the tool the user searched for first; Pipeleap is the orchestration layer around it
- No differentiation-style copy, blog explanations, or editorial commentary in field values
"""
from __future__ import annotations

TOOLS_DATA: list[dict] = [
    {
        "slug": "clay-enrichment-workflow",
        "title": "Clay for B2B Enrichment: How Revenue Teams Use It in Production",
        "seo_title": "Clay Enrichment Workflow for B2B Sales Teams | Pipeleap",
        "h1": "Clay for B2B Enrichment: Production Architecture for Revenue Teams",
        "primary_keyword": "clay enrichment workflow",
        "keywords": ["clay b2b enrichment", "clay data enrichment", "clay workflow setup", "clay waterfall enrichment"],
        "category": "Data Enrichment",
        "tool_name": "Clay",
        "pain": "Enrichment results are inconsistent — match rates vary by provider, data goes stale, and there is no fallback when a primary provider misses a contact.",
        "tool_what": (
            "Clay is a data enrichment and workflow automation platform that pulls from 50+ data providers "
            "through a spreadsheet-like interface. Revenue teams use it to build enrichment waterfalls, "
            "research prospects at scale, and push enriched data into CRM or sequencing tools."
        ),
        "tool_where_it_breaks": (
            "Clay handles enrichment well but does not own the full execution layer. "
            "CRM write-back, suppression checks, sequence assignment, and reply routing all require "
            "separate tooling and manual stitching. At scale, this creates data inconsistency between "
            "enrichment output and CRM state."
        ),
        "pipeleap_layer": (
            "Pipeleap's workflow engine wraps around Clay's enrichment output — ingesting enriched records, "
            "applying ICP qualification gates, writing structured data to CRM, and triggering sequences "
            "with suppression checks. Clay handles the data layer; Pipeleap governs the execution layer."
        ),
        "faqs": [
            ("Does Pipeleap replace Clay?", "No. Clay handles the data enrichment layer. Pipeleap governs what happens after enrichment — CRM write-back, qualification, sequencing, and reply routing."),
            ("Can Pipeleap ingest Clay output directly?", "Yes. Pipeleap connects to Clay via webhook or API, picks up enriched records, and routes them through the downstream execution workflow."),
            ("What breaks when you use Clay without an orchestration layer?", "CRM records go stale because there is no structured write-back. Sequences fire on partially enriched contacts. Reply handling is manual. Each step is owned by a different tool with no shared state."),
        ],
        "topical_pillar": "enrichment-waterfall",
    },
    {
        "slug": "apollo-outbound-workflow",
        "title": "Apollo.io in an Outbound Workflow: Where It Fits and Where It Needs Governance",
        "seo_title": "Apollo.io Outbound Workflow Architecture | Pipeleap",
        "h1": "Apollo.io in an Outbound Workflow: Governance Architecture for Revenue Teams",
        "primary_keyword": "apollo outbound workflow",
        "keywords": ["apollo.io workflow", "apollo outbound automation", "apollo crm sync", "apollo sequence governance"],
        "category": "Sales Engagement / Sequencer",
        "tool_name": "Apollo.io",
        "pain": "Apollo sequences fire on unqualified contacts, CRM data is overwritten without deduplication, and reply routing is manual — the system scales volume, not pipeline quality.",
        "tool_what": (
            "Apollo.io is a sales engagement platform combining a B2B contact database, email sequencer, "
            "and basic CRM enrichment. Revenue teams use it to source prospects, run outbound sequences, "
            "and track engagement metrics in a single interface."
        ),
        "tool_where_it_breaks": (
            "Apollo's database and sequencer are tightly coupled, which limits how much governance can be "
            "applied before outreach fires. ICP qualification, enrichment waterfall logic, CRM deduplication, "
            "and reply routing all require configuration that Apollo does not natively enforce at the "
            "workflow level."
        ),
        "pipeleap_layer": (
            "Pipeleap sits upstream of Apollo's sequencer — running enrichment validation and ICP qualification "
            "before any contact enters an Apollo sequence. It also handles CRM write-back and reply routing "
            "as governed workflow steps, so Apollo handles execution while Pipeleap handles the intake "
            "and output governance."
        ),
        "faqs": [
            ("Does Pipeleap replace Apollo?", "No. Apollo handles the contact database and sequence execution. Pipeleap governs the intake qualification and CRM output layer that Apollo does not enforce."),
            ("Can Pipeleap trigger Apollo sequences automatically?", "Yes. Pipeleap qualifies a contact against ICP criteria and triggers the Apollo sequence via API once all gates pass."),
            ("Why do Apollo sequences produce inconsistent results?", "Contacts often enter sequences before enrichment is complete, without ICP qualification, and without CRM deduplication. Governing the intake layer before sequences fire fixes this."),
        ],
        "topical_pillar": "outbound-governance",
    },
    {
        "slug": "n8n-outbound-automation",
        "title": "n8n for Outbound Automation: Building a Governed Revenue Workflow",
        "seo_title": "n8n Outbound Automation Workflow for Revenue Teams | Pipeleap",
        "h1": "n8n for Outbound Automation: Governed Workflow Architecture",
        "primary_keyword": "n8n outbound automation",
        "keywords": ["n8n outbound workflow", "n8n sales automation", "n8n crm integration", "n8n sequence automation"],
        "category": "Workflow Automation Engine",
        "tool_name": "n8n",
        "pain": "n8n workflows are powerful but ungoverned — there are no built-in ICP gates, enrichment waterfall logic, or outbound-specific suppression rules, so the workflows require constant maintenance as the stack changes.",
        "tool_what": (
            "n8n is an open-source workflow automation platform that connects APIs, databases, and services "
            "through a visual node editor. Revenue teams use it to automate multi-step outbound workflows — "
            "enrichment, CRM sync, sequence triggers — without code."
        ),
        "tool_where_it_breaks": (
            "n8n provides the execution layer but not the domain logic. Building ICP qualification nodes, "
            "enrichment waterfall fallback logic, CRM deduplication, and reply routing in n8n requires "
            "significant configuration that must be rebuilt when the stack changes. There is no "
            "outbound-specific governance layer built in."
        ),
        "pipeleap_layer": (
            "Pipeleap is built on n8n's workflow engine and adds the outbound-specific governance layer "
            "on top: enrichment waterfall logic, ICP qualification gates, CRM deduplication, sequence "
            "suppression, and reply routing — all pre-configured for SaaS revenue workflows."
        ),
        "faqs": [
            ("Is Pipeleap built on n8n?", "Yes. Pipeleap uses n8n as its workflow execution engine and adds the outbound governance layer — enrichment waterfalls, ICP gates, CRM dedup, and reply routing — on top."),
            ("Can I migrate existing n8n outbound workflows to Pipeleap?", "Yes. Existing n8n workflows can be imported and extended with Pipeleap's governance nodes without rebuilding from scratch."),
            ("When should a revenue team use raw n8n compared to Pipeleap?", "Raw n8n works for general automation. Pipeleap is the right choice when the workflow is specifically outbound sales — enrichment, qualification, CRM sync, sequencing, and reply handling — where domain-specific governance matters."),
        ],
        "topical_pillar": "workflow-orchestration",
    },
    {
        "slug": "salesforce-crm-enrichment",
        "title": "Salesforce CRM Enrichment at Scale: RevOps Architecture Guide",
        "seo_title": "Salesforce CRM Enrichment Workflow for RevOps Teams | Pipeleap",
        "h1": "Salesforce CRM Enrichment at Scale: RevOps Architecture Guide",
        "primary_keyword": "salesforce crm enrichment",
        "keywords": ["salesforce enrichment workflow", "salesforce data quality", "salesforce crm hygiene", "salesforce outbound integration"],
        "category": "CRM Data Operations",
        "tool_name": "Salesforce",
        "pain": "Salesforce records are incomplete or stale — enrichment runs periodically rather than on every contact action, deduplication logic is inconsistent, and RevOps spends time cleaning data instead of building pipeline.",
        "tool_what": (
            "Salesforce is the enterprise CRM standard for tracking contacts, accounts, opportunities, "
            "and pipeline. RevOps teams use it as the system of record for all revenue activity, "
            "reporting, and forecasting."
        ),
        "tool_where_it_breaks": (
            "Salesforce is the system of record but not the data quality enforcement layer. "
            "Enrichment runs in batch rather than at the point of contact creation, deduplication "
            "rules require custom configuration, and there is no native workflow that blocks outreach "
            "until data quality meets a defined threshold."
        ),
        "pipeleap_layer": (
            "Pipeleap writes to Salesforce as a governed workflow step — enriching each contact before "
            "write-back, applying deduplication logic, and setting ownership and lifecycle stage "
            "consistently. Every Salesforce record created via Pipeleap meets defined data quality "
            "thresholds before it enters the CRM."
        ),
        "faqs": [
            ("Does Pipeleap replace Salesforce?", "No. Salesforce remains the system of record. Pipeleap governs what data enters Salesforce — enrichment, deduplication, and field mapping — so the records are clean when they arrive."),
            ("How does Pipeleap handle Salesforce deduplication?", "Pipeleap checks for existing contacts and accounts by email, domain, and name before every write-back, merging or skipping as configured."),
            ("Can Pipeleap write to custom Salesforce fields?", "Yes. Field mappings are configured per workflow and support any standard or custom field in the target Salesforce org."),
        ],
        "topical_pillar": "crm-hygiene",
    },
    {
        "slug": "gong-pipeline-data",
        "title": "Gong Pipeline Data: How Revenue Leaders Use Call Intelligence Without Building Dependency",
        "seo_title": "Gong Pipeline Data Workflow for Revenue Leaders | Pipeleap",
        "h1": "Gong Pipeline Data: Governance Architecture for Revenue Leaders",
        "primary_keyword": "gong pipeline data",
        "keywords": ["gong call intelligence workflow", "gong crm integration", "gong pipeline forecasting", "gong revenue insights"],
        "category": "Conversation Intelligence",
        "tool_name": "Gong",
        "pain": "Gong call data sits in a separate system from pipeline data — insights about deal risk, objection patterns, and next steps are not automatically synced to CRM or used to trigger workflow actions.",
        "tool_what": (
            "Gong is a conversation intelligence platform that records, transcribes, and analyses sales calls "
            "to surface deal risk, coaching opportunities, and pipeline forecasting signals. CROs and VP Sales "
            "Strategy teams use it to improve forecast accuracy and rep performance."
        ),
        "tool_where_it_breaks": (
            "Gong generates deal intelligence but does not act on it. Risk flags, next-step gaps, and "
            "engagement signals stay inside Gong unless manually reviewed and acted on by a rep or manager. "
            "There is no native path from Gong insight to automated workflow trigger."
        ),
        "pipeleap_layer": (
            "Pipeleap ingests Gong signals via API — deal risk scores, next-step gaps, engagement drop-offs — "
            "and uses them as triggers for automated workflow actions: re-engagement sequences, rep alerts, "
            "CRM stage updates, or manager escalations. Gong identifies the signal; Pipeleap acts on it."
        ),
        "faqs": [
            ("Does Pipeleap replace Gong?", "No. Gong provides the call intelligence and deal risk signals. Pipeleap acts on those signals automatically — triggering sequences, updating CRM, or escalating to managers."),
            ("What Gong signals can Pipeleap act on?", "Any signal Gong exposes via API: deal risk score, next step missing, champion engagement drop, or specific keywords flagged in call transcripts."),
            ("How does this improve forecast accuracy?", "By automatically acting on deal risk signals instead of waiting for manual rep review, deals get re-engaged or escalated before they slip the forecast window."),
        ],
        "topical_pillar": "signal-based-outbound",
    },
    {
        "slug": "outreach-reply-handling",
        "title": "Outreach.io Reply Handling: Automating What Happens After a Sequence Reply",
        "seo_title": "Outreach.io Reply Handling Workflow Automation | Pipeleap",
        "h1": "Outreach.io Reply Handling: Automated Routing Architecture",
        "primary_keyword": "outreach reply handling",
        "keywords": ["outreach.io reply routing", "outreach sequence reply automation", "outreach crm reply sync", "outreach meeting booking"],
        "category": "Sequencer Reply Routing",
        "tool_name": "Outreach.io",
        "pain": "Positive replies sit unactioned while SDRs manually triage inboxes — out-of-office replies are not snoozed, unsubscribes are not suppressed in CRM, and meeting booking is a manual step that breaks the sequence ROI calculation.",
        "tool_what": (
            "Outreach.io is a sales engagement platform for managing multi-touch outbound sequences across "
            "email, calls, and LinkedIn. VP Sales Ops teams use it to standardise rep outreach, enforce "
            "sequence templates, and track engagement at the account level."
        ),
        "tool_where_it_breaks": (
            "Outreach handles sequence execution well but reply handling is largely manual. "
            "Positive replies require a rep to book the meeting, out-of-office replies require manual "
            "snooze, and CRM suppression after an unsubscribe requires a separate workflow step. "
            "Each missed reply action compounds into wasted pipeline."
        ),
        "pipeleap_layer": (
            "Pipeleap governs the reply layer on top of Outreach sequences — auto-routing positive replies "
            "to meeting booking, snoozed out-of-office replies for re-entry, and pushing unsubscribes "
            "to CRM suppression lists automatically. Reply handling becomes a workflow step, not a "
            "manual inbox task."
        ),
        "faqs": [
            ("Does Pipeleap replace Outreach?", "No. Outreach runs the sequences. Pipeleap governs what happens when a reply arrives — routing it to the right action automatically."),
            ("How does Pipeleap classify reply intent?", "Pipeleap uses keyword and sentiment signals to classify replies as positive, out-of-office, unsubscribe, or objection, then routes each to the appropriate workflow branch."),
            ("What happens to meeting booking in this architecture?", "Positive replies trigger an automated meeting link or calendar booking step within the Pipeleap workflow — no manual SDR action required."),
        ],
        "topical_pillar": "outbound-governance",
    },
    {
        "slug": "hubspot-outbound-stack",
        "title": "HubSpot as an Outbound CRM: What Works and What Requires Governance",
        "seo_title": "HubSpot Outbound CRM Workflow Architecture | Pipeleap",
        "h1": "HubSpot as an Outbound CRM: Governance Architecture for Revenue Teams",
        "primary_keyword": "hubspot outbound crm",
        "keywords": ["hubspot outbound workflow", "hubspot crm enrichment", "hubspot sequence governance", "hubspot sales ops"],
        "category": "CRM + Outbound",
        "tool_name": "HubSpot",
        "pain": "HubSpot's all-in-one model creates fragmentation at scale — sequences lack enrichment gates, CRM records are created without deduplication, and there is no governed path from signal to booked meeting.",
        "tool_what": (
            "HubSpot is a CRM and marketing platform used by SaaS revenue teams for contact management, "
            "deal tracking, email sequences, and reporting. It is widely adopted as the system of record "
            "for SMB and mid-market sales teams."
        ),
        "tool_where_it_breaks": (
            "HubSpot's native sequences do not enforce enrichment quality before firing. "
            "Contact creation lacks deduplication rules that scale beyond a few thousand records. "
            "And there is no workflow-level governance that blocks outreach until ICP qualification "
            "passes — sequences are triggered by list membership, not data quality."
        ),
        "pipeleap_layer": (
            "Pipeleap adds the governance layer that HubSpot's native workflows lack — enriching contacts "
            "before CRM write-back, applying ICP qualification before sequence entry, and deduplicating "
            "records at the point of creation. HubSpot remains the system of record; Pipeleap governs "
            "the data that enters it."
        ),
        "faqs": [
            ("Does Pipeleap replace HubSpot?", "No. HubSpot is the system of record. Pipeleap governs the enrichment, qualification, and deduplication layer before contacts enter HubSpot."),
            ("Can Pipeleap trigger HubSpot sequences?", "Yes. Once a contact passes Pipeleap's ICP qualification gate, it can trigger a HubSpot sequence enrollment automatically via API."),
            ("What CRM hygiene problems does this solve?", "Duplicate contacts, incomplete records, and contacts that enter sequences without meeting ICP criteria — all prevented by the Pipeleap governance layer before HubSpot write-back."),
        ],
        "topical_pillar": "crm-hygiene",
    },
    {
        "slug": "zoominfo-enrichment-workflow",
        "title": "ZoomInfo Enrichment Workflow: How Revenue Teams Use It in a Governed Stack",
        "seo_title": "ZoomInfo Enrichment Workflow for Revenue Teams | Pipeleap",
        "h1": "ZoomInfo Enrichment Workflow: Governed Architecture for Revenue Teams",
        "primary_keyword": "zoominfo enrichment workflow",
        "keywords": ["zoominfo crm enrichment", "zoominfo data quality", "zoominfo workflow integration", "zoominfo vs clay enrichment"],
        "category": "Enterprise Enrichment Provider",
        "tool_name": "ZoomInfo",
        "pain": "ZoomInfo data is high-quality but expensive per match — without a waterfall strategy and quality threshold logic, teams over-spend on enrichment while still getting incomplete records into CRM.",
        "tool_what": (
            "ZoomInfo is an enterprise B2B data platform providing contact intelligence, intent data, "
            "and CRM enrichment for large revenue teams. It is the most widely used enrichment provider "
            "at the enterprise level, known for high match rates on North American accounts."
        ),
        "tool_where_it_breaks": (
            "ZoomInfo is a data source, not an execution layer. Getting ZoomInfo data into CRM in a "
            "structured, deduplicated way requires integration work. Building a waterfall that falls "
            "back to a secondary provider when ZoomInfo misses requires additional configuration "
            "that ZoomInfo does not natively support."
        ),
        "pipeleap_layer": (
            "Pipeleap uses ZoomInfo as the primary enrichment provider in its waterfall logic — "
            "querying ZoomInfo first, falling back to secondary providers (Clay, Apollo, Clearbit) when "
            "ZoomInfo returns incomplete data, and writing the final enriched record to CRM with "
            "deduplication and field validation enforced."
        ),
        "faqs": [
            ("Does Pipeleap replace ZoomInfo?", "No. ZoomInfo is the data source. Pipeleap orchestrates when and how ZoomInfo is queried, what happens when it misses, and how the result is written to CRM."),
            ("When should ZoomInfo be used over Clay in a waterfall?", "ZoomInfo has higher match rates on large North American accounts. Clay is more flexible for international contacts and custom research. Pipeleap's waterfall routes each contact to the right provider based on account region and data completeness targets."),
            ("How does Pipeleap manage ZoomInfo costs?", "Pipeleap only queries ZoomInfo when the contact meets a minimum ICP signal threshold, reducing enrichment spend on contacts that will never enter a sequence."),
        ],
        "topical_pillar": "enrichment-waterfall",
    },
]
