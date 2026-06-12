"""Write proper meta descriptions for the 24 generated categories."""
from pathlib import Path

cat_path = Path("temp_frontend_repo/src/data/tools/categories.ts")
text = cat_path.read_text(encoding="utf-8")

META = {
    "chatbots-live-chat": "AI chatbots and live chat tools for website lead capture, conversational qualification, and real-time prospect engagement.",
    "content-management-tools": "Content management and sales enablement platforms for organising, distributing, and tracking sales content performance.",
    "contract-management-tools": "Contract lifecycle management tools that automate agreement workflows, approvals, and compliance tracking for sales teams.",
    "conversation-intelligence-tools": "Conversation intelligence and call analysis platforms that transcribe, analyse, and surface deal risks from sales conversations.",
    "cpq-tools": "Configure, price, quote platforms that automate proposal generation, pricing logic, and approval workflows for sales teams.",
    "data-providers": "B2B company and contact data providers supplying firmographic, technographic, and intent data for targeted prospecting.",
    "deal-desk-tools": "Deal desk and pricing optimisation tools for structuring discounts, managing approvals, and accelerating deal closure.",
    "demo-platforms": "Interactive product demo and walkthrough platforms that let prospects experience your product without a live sales call.",
    "e-signature-tools": "E-signature and contract approval platforms for legally binding digital signatures and faster deal closure.",
    "email-deliverability-tools": "Email deliverability and sending infrastructure tools that protect domain reputation and maximise inbox placement.",
    "email-validation-tools": "Email verification and validation tools that clean prospect lists by detecting invalid, risky, or disposable addresses.",
    "forecasting-tools": "Sales forecasting and revenue intelligence platforms that predict pipeline outcomes and improve forecast accuracy.",
    "intent-data-tools": "Buyer intent data and predictive scoring platforms that identify accounts actively researching your product category.",
    "ipaas-tools": "Integration platform as a service tools that connect SaaS applications through pre-built connectors and automated data sync.",
    "list-building-tools": "Lead list building and account research tools for building targeted prospect lists from multiple data sources.",
    "meeting-scheduling-tools": "Meeting scheduling and booking platforms that eliminate back-and-forth emails with direct calendar booking.",
    "payment-tools": "Payment processing and billing platforms for subscription management, invoicing, and revenue collection.",
    "pipeline-analytics-tools": "Pipeline analytics and inspection tools that give revenue leaders real-time visibility into deal progression and bottlenecks.",
    "proposal-tools": "Proposal generation and document management platforms for creating, sending, and tracking sales proposals.",
    "sales-coaching-tools": "Sales coaching and training platforms that improve rep performance through call review, scorecards, and structured learning.",
    "sales-copilot-tools": "AI sales copilots and assistive tools providing real-time recommendations, next-best-action prompts, and automated CRM data entry.",
    "sales-enablement-tools": "Sales enablement and content management platforms that equip reps with playbooks, training, and content at every deal stage.",
    "video-prospecting-tools": "Video messaging for sales prospecting tools that let reps send personalised recorded videos to stand out in crowded inboxes.",
    "cdp-tools": "Customer data platforms that unify behavioural, transactional, and demographic data into single customer profiles for personalised outreach.",
}

import re

for slug, meta in META.items():
    # Find the entry for this slug and update its metaDescription
    pattern = r'(slug:\s*"' + re.escape(slug) + r'"[\s\S]*?metaDescription:\s*")[^"]*(")'
    replacement = r'\1' + meta + r'\2'
    new_text = re.sub(pattern, replacement, text)
    if new_text != text:
        text = new_text
        print(f"  Updated meta for {slug}")
    else:
        print(f"  NOT FOUND: {slug}")

cat_path.write_text(text, encoding="utf-8")
print("\nDone!")
