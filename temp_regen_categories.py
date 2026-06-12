"""Regenerate categories.ts: keep 13 good entries, rewrite 24 template entries with rich content."""
import json as json_mod
import os
import re
import subprocess
import sys
from pathlib import Path

# Get gh token for LLM
result = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, timeout=10)
token = result.stdout.strip()
if token:
    os.environ["GITHUB_TOKEN"] = token
else:
    print("No GitHub token")
    sys.exit(1)

sys.path.insert(0, ".")
from connectors.llm_client import LLMClient

llm = LLMClient()
if not llm.is_configured:
    print("LLM not configured")
    sys.exit(1)

tools_dir = Path("temp_frontend_repo/src/data/tools")
cat_path = tools_dir / "categories.ts"

# Read existing file
cat_text = cat_path.read_text(encoding="utf-8")

# Extract first 13 entries (lines 1-211)
# Find the 13th entry's closing brace position
entries = list(re.finditer(r'^\s*\{[\s\S]*?^\s*\},', cat_text, re.MULTILINE))
# First 13 entries
count = 0
pos_after_13 = 0
for m in re.finditer(r'^\s*\{[\s\S]*?^\s*\},', cat_text, re.MULTILINE):
    count += 1
    if count == 13:
        pos_after_13 = m.end()
        break

header = cat_text[:pos_after_13]
closing = "\n];\n\nexport const TOOL_CATEGORY_MAP = Object.fromEntries(\n  toolCategories.map((c) => [c.slug, c])\n) as Record<string, ToolCategory>;\n"

# Categories to generate (24)
categories = [
    ("chatbots-live-chat", "Chatbots and Live Chat", "Chatbots and Live Chat", "chatbots and live chat tools for website engagement, lead capture, and conversational qualification"),
    ("content-management-tools", "Content Management Tools", "Content Management Tools", "content management and sales enablement platforms for organising and distributing sales content"),
    ("contract-management-tools", "Contract Management Tools", "Contract Management Tools", "contract lifecycle management and agreement workflow tools for sales teams"),
    ("conversation-intelligence-tools", "Conversation Intelligence Tools", "Conversation Intelligence Tools", "conversation intelligence and call analysis platforms that transcribe, analyse, and surface deal insights from sales calls"),
    ("cpq-tools", "CPQ Tools", "CPQ Platforms", "configure, price, quote platforms that automate proposal generation, pricing logic, and approval workflows"),
    ("data-providers", "Data Providers", "Data Providers", "B2B company and contact data providers that supply firmographic, technographic, and contact-level data for prospecting"),
    ("deal-desk-tools", "Deal Desk Tools", "Deal Desk Tools", "deal desk and pricing optimisation tools that help sales teams structure quotes, approvals, and discount workflows"),
    ("demo-platforms", "Demo Platforms", "Demo Platforms", "product demo and interactive walkthrough platforms that let prospects experience your product without a live sales call"),
    ("e-signature-tools", "E-Signature Tools", "E-Signature Tools", "e-signature and contract approval platforms that close deals faster with legally binding digital signatures"),
    ("email-deliverability-tools", "Email Deliverability Tools", "Email Deliverability Tools", "email deliverability and sending infrastructure tools that protect domain reputation and maximise inbox placement"),
    ("email-validation-tools", "Email Validation Tools", "Email Validation Tools", "email verification and validation tools that clean prospect lists by detecting invalid, risky, or disposable email addresses"),
    ("forecasting-tools", "Forecasting Tools", "Forecasting Tools", "sales forecasting and revenue intelligence platforms that predict pipeline outcomes and improve forecast accuracy"),
    ("intent-data-tools", "Intent Data Tools", "Intent Data Tools", "buyer intent data and predictive scoring platforms that identify accounts actively researching your category"),
    ("ipaas-tools", "iPaaS Tools", "iPaaS Platforms", "integration platform as a service tools that connect SaaS applications through pre-built connectors and workflow automation"),
    ("list-building-tools", "List Building Tools", "List Building Tools", "lead list building and account research tools that build targeted prospect lists from multiple data sources"),
    ("meeting-scheduling-tools", "Meeting Scheduling Tools", "Meeting Scheduling Tools", "meeting scheduling and booking platforms that eliminate back-and-forth emails by letting prospects book directly"),
    ("payment-tools", "Payment Tools", "Payment Tools", "payment processing and billing platforms that handle subscription management, invoicing, and revenue collection"),
    ("pipeline-analytics-tools", "Pipeline Analytics Tools", "Pipeline Analytics Tools", "pipeline analytics and inspection tools that give revenue leaders real-time visibility into deal progression and bottlenecks"),
    ("proposal-tools", "Proposal Tools", "Proposal Tools", "proposal generation and document management platforms that create, send, and track sales proposals"),
    ("sales-coaching-tools", "Sales Coaching Tools", "Sales Coaching Tools", "sales coaching and training platforms that improve rep performance through call review, scorecards, and structured learning"),
    ("sales-copilot-tools", "Sales Copilot Tools", "Sales Copilot Tools", "AI sales copilots and assistive tools that sit inside a rep's workflow providing real-time recommendations, next-best-action prompts, and automated data entry"),
    ("sales-enablement-tools", "Sales Enablement Tools", "Sales Enablement Tools", "sales enablement and content management platforms that equip reps with the right content, training, and playbooks at each stage of the deal"),
    ("video-prospecting-tools", "Video Prospecting Tools", "Video Prospecting Tools", "video messaging for sales prospecting tools that let reps send personalised recorded videos to stand out in crowded inboxes"),
    ("cdp-tools", "CDP Tools", "CDP Platforms", "customer data platforms that unify behavioural, transactional, and demographic data into a single customer profile for sales and marketing"),
]

# Get tool slugs per category from data files
def get_tool_slugs(cat_slug):
    f = tools_dir / f"{cat_slug}.ts"
    if not f.exists():
        return []
    text = f.read_text(encoding="utf-8")
    return re.findall(r'slug:\s*"([^"]+)"', text)

# Related categories map
RELATED = {
    "chatbots-live-chat": ["crm-tools", "meeting-scheduling-tools", "workflow-automation-tools"],
    "content-management-tools": ["sales-enablement-tools", "sales-coaching-tools", "crm-tools"],
    "contract-management-tools": ["e-signature-tools", "cpq-tools", "proposal-tools"],
    "conversation-intelligence-tools": ["call-recording-tools", "revenue-intelligence-tools", "sales-coaching-tools"],
    "cpq-tools": ["proposal-tools", "e-signature-tools", "contract-management-tools"],
    "data-providers": ["prospecting-tools", "lead-enrichment-tools", "list-building-tools"],
    "deal-desk-tools": ["cpq-tools", "proposal-tools", "forecasting-tools"],
    "demo-platforms": ["meeting-scheduling-tools", "video-prospecting-tools", "crm-tools"],
    "e-signature-tools": ["contract-management-tools", "proposal-tools", "cpq-tools"],
    "email-deliverability-tools": ["cold-email-tools", "email-validation-tools", "sales-engagement-tools"],
    "email-validation-tools": ["email-deliverability-tools", "lead-enrichment-tools", "cold-email-tools"],
    "forecasting-tools": ["revenue-intelligence-tools", "pipeline-analytics-tools", "crm-tools"],
    "intent-data-tools": ["data-providers", "prospecting-tools", "revenue-intelligence-tools"],
    "ipaas-tools": ["workflow-automation-tools", "crm-tools", "cdp-tools"],
    "list-building-tools": ["prospecting-tools", "lead-enrichment-tools", "data-providers"],
    "meeting-scheduling-tools": ["crm-tools", "demo-platforms", "video-prospecting-tools"],
    "payment-tools": ["cpq-tools", "e-signature-tools", "crm-tools"],
    "pipeline-analytics-tools": ["forecasting-tools", "revenue-intelligence-tools", "crm-tools"],
    "proposal-tools": ["cpq-tools", "e-signature-tools", "contract-management-tools"],
    "sales-coaching-tools": ["conversation-intelligence-tools", "call-recording-tools", "sales-enablement-tools"],
    "sales-copilot-tools": ["crm-tools", "sales-engagement-tools", "workflow-automation-tools"],
    "sales-enablement-tools": ["content-management-tools", "sales-coaching-tools", "crm-tools"],
    "video-prospecting-tools": ["demo-platforms", "meeting-scheduling-tools", "cold-email-tools"],
    "cdp-tools": ["crm-tools", "ipaas-tools", "workflow-automation-tools"],
}

BUGET_ANGLE = {
    "chatbots-live-chat": "Pipeleap routes chat-qualified leads into the right enrichment, scoring, and sequencing workflows - so a website chat doesn't become a dead lead.",
    "content-management-tools": "Pipeleap connects content engagement signals to outbound sequences - when a prospect opens a proposal or case study, the next workflow step fires automatically.",
    "contract-management-tools": "Pipeleap surfaces contract-stage deals into pipeline reporting and triggers CRM updates when contract status changes - so ops has real-time visibility into the closing process.",
    "conversation-intelligence-tools": "Pipeleap acts on conversation intelligence signals - routing at-risk deals to management, surfacing competitor mentions, and syncing call outcomes to CRM without manual data entry.",
    "cpq-tools": "Pipeleap connects CPQ outputs to the rest of the outbound workflow - triggering post-close sequences, updating pipeline stages, and feeding deal data into forecasting.",
    "data-providers": "Pipeleap routes data from enrichment providers into automated prospecting workflows - filtering, scoring, and sequencing leads based on firmographic fit without manual triage.",
    "deal-desk-tools": "Pipeleap connects deal desk approval signals back to the sales workflow - automatically escalating discount requests, notifying approvers, and updating deal stages in CRM.",
    "demo-platforms": "Pipeleap triggers follow-up workflows when a prospect views a demo - routing them to the right sequence, updating lead scores, and notifying the assigned rep in real time.",
    "e-signature-tools": "Pipeleap detects when a document is signed and triggers post-close workflows - handoffs to onboarding, CRM stage updates, and customer communication sequences.",
    "email-deliverability-tools": "Pipeleap monitors sending infrastructure and alerts ops to deliverability drops before they affect campaign performance - keeping outbound healthy without constant manual monitoring.",
    "email-validation-tools": "Pipeleap validates email addresses at the point of entry - filtering bad data before it enters sequences, reducing bounce rates and protecting domain reputation.",
    "forecasting-tools": "Pipeleap feeds clean, real-time outbound activity data into forecasting tools - so pipeline predictions reflect what reps are actually doing, not what they remembered to log.",
    "intent-data-tools": "Pipeleap routes intent data signals into automated outreach sequences - when a target account shows buying intent, the right lead is scored, assigned, and sequenced before a competitor reaches them.",
    "ipaas-tools": "Pipeleap acts as the sales workflow layer above iPaaS integrations - routing data between tools, managing exceptions, and keeping CRM in sync without complex custom logic.",
    "list-building-tools": "Pipeleap takes prospect lists and routes them through enrichment, scoring, and sequencing - turning a raw list into a qualified, prioritised outbound pipeline.",
    "meeting-scheduling-tools": "Pipeleap connects meeting bookings to downstream actions - updating lead stages, triggering follow-up sequences, and notifying reps with context about the prospect's journey.",
    "payment-tools": "Pipeleap connects payment events to the sales workflow - triggering renewal sequences, updating deal stages on payment receipt, and routing failed payment alerts to the right team.",
    "pipeline-analytics-tools": "Pipeleap surfaces pipeline data alongside outbound activity data - so analytics reflect the full picture: which sequences are producing pipeline, not just which deals are in stage.",
    "proposal-tools": "Pipeleap connects proposal activity to outbound sequences - when a proposal is sent or viewed, the next workflow step triggers automatically based on engagement.",
    "sales-coaching-tools": "Pipeleap ties coaching data to outbound performance metrics - so ops can see which coaching interventions actually move pipeline metrics, not just activity metrics.",
    "sales-copilot-tools": "Pipeleap routes the data layer that sales copilots need - feeding CRM context, enrichment data, and sequence history into the assistant so recommendations are grounded in real pipeline data.",
    "sales-enablement-tools": "Pipeleap connects content engagement signals to the sales workflow - triggering sequence adjustments, surfacing competitive content at the right deal stage, and alerting reps when key content is viewed.",
    "video-prospecting-tools": "Pipeleap routes video engagement signals into the sales workflow - when a prospect watches a video, the system adjusts sequence timing, updates lead scores, and prioritises follow-up.",
    "cdp-tools": "Pipeleap connects CDP segments to outbound workflows - routing high-intent segments into sequenced outreach, syncing behavioural data to CRM, and triggering personalised sequences based on customer actions.",
}

# Generate content for all 24 categories in batches using LLM
print(f"Generating content for {len(categories)} categories via LLM...")

all_entries = []
batch_size = 6
for i in range(0, len(categories), batch_size):
    batch = categories[i:i+batch_size]
    prompt = f"""You are writing TypeScript category definitions for a sales tools directory. Generate rich content for {len(batch)} tool categories.

For each category, provide:
1. A descriptive `intro` (70-120 chars) explaining what the tools DO, not "Browse our curated list of X"
2. A detailed `body` (100-200 chars) explaining the category landscape - market structure, what defines good vs bad, and what ops leaders should evaluate
3. 2 realistic `faqs` with good answers

Return valid JSON only - an array of objects with keys: slug, intro, body, faqs (array of {{q, a}}).

The {len(batch)} slugs and descriptions:
"""
    for slug, name, plural, desc in batch:
        prompt += f'\n- slug: "{slug}", name: "{name}", description: {desc}'

    prompt += '\n\nReturn ONLY a JSON array. Example: [{"slug": "example-tools", "intro": "...", "body": "...", "faqs": [{"q": "...", "a": "..."}]}]'

    print(f"  Batch {i//batch_size + 1}/{(len(categories)-1)//batch_size + 1}: {batch[0][0]}...")
    resp = llm.generate(prompt, model="gpt-4o-mini", max_tokens=6000, temperature=0.7)

    if not resp:
        print(f"  ERROR: No response for batch {i//batch_size + 1}")
        continue

    # Parse JSON from response
    try:
        # Find JSON array in response
        json_match = re.search(r'\[.*\]', resp, re.DOTALL)
        if json_match:
            batch_data = json_mod.loads(json_match.group())
            all_entries.extend(batch_data)
            print(f"    Got {len(batch_data)} entries")
        else:
            print(f"    Could not parse JSON from response")
            print(f"    Response: {resp[:200]}...")
    except json_mod.JSONDecodeError as e:
        print(f"    JSON decode error: {e}")
        print(f"    Response: {resp[:200]}...")

print(f"\nGenerated {len(all_entries)}/{len(categories)} entries")

def esc(s):
    return s.replace('\\', '\\\\').replace('"', '\\"')

def mk_tools(arr):
    """Build tools array string."""
    if not arr:
        return "    tools: [],"
    items = ', '.join('"' + esc(s) + '"' for s in arr)
    return "    tools: [" + items + "],"

def mk_rel(arr):
    """Build relatedCategories array string."""
    if not arr:
        return "    relatedCategories: [],"
    items = ', '.join('"' + esc(r) + '"' for r in arr)
    return "    relatedCategories: [" + items + "],"

def mk_faqs(faqs_list):
    """Build faqs array string."""
    if not faqs_list:
        return "    faqs: [],"
    lines_b = ["    faqs: ["]
    for fobj in faqs_list[:2]:
        q = esc(fobj.get("q", ""))
        a = esc(fobj.get("a", ""))
        lines_b.append('      { q: "' + q + '", a: "' + a + '" },')
    lines_b.append("    ],")
    return "\n".join(lines_b)

full_entries = []
for entry_data in all_entries:
    slug = entry_data.get("slug", "")
    cat_info = next((c for c in categories if c[0] == slug), None)
    if not cat_info:
        continue
    _, name, plural, _ = cat_info
    desc = esc(entry_data.get("intro", ""))
    body = esc(entry_data.get("body", ""))
    faqs = entry_data.get("faqs", [])
    tool_slugs = get_tool_slugs(slug)
    related = RELATED.get(slug, [])
    angle = esc(BUGET_ANGLE.get(slug, ""))
    meta = "The best " + desc.lower().rstrip(".").lstrip() + " for sales teams." if len(desc) < 120 else desc

    lines_b = [
        "  {",
        '    slug: "' + slug + '",',
        '    name: "' + name + '",',
        '    pluralName: "' + plural + '",',
        '    metaDescription: "' + meta + '",',
        '    intro: "' + desc + '",',
        '    body: "' + body + '",',
        mk_tools(tool_slugs),
        mk_rel(related),
        '    pipeLeapAngle: "' + angle + '",',
        mk_faqs(faqs),
        "  },",
    ]
    full_entries.append("\n".join(lines_b))

content = header.strip("\n") + "\n" + "\n".join(full_entries) + "\n" + closing
cat_path.write_text(content, encoding="utf-8")
print(f"\nWritten {len(all_entries)} entries to categories.ts")
print("Done!")
