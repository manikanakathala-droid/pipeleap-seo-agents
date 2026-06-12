# Platform Positioning Rebrand

**Goal:** Reframe Pipeleap from "managed service" to "Sales Operations Platform" (software product). Remove all service-language, partner-language, and retainer-language. Rewrite the Services page as platform capabilities.

## Files to Change

### 1. `src/pages/Services.tsx` — Rewrite as platform page
- Rename page: "Services" → "Platform" (or "Capabilities")
- Replace `"@type": "Service"` schema → `"@type": "SoftwareApplication"`, `"applicationCategory": "BusinessApplication"` (same as Index.tsx)
- Replace H1: "Sales Workflow Automation Services" → "Sales Operations Platform"
- Replace subtitle: remove "designs and implements plug-and-play sales workflows" → platform description
- Replace FAQ Q: "Is Pipeleap a managed service?" → "How does Pipeleap pricing work?"
- Replace FAQ A: "No. Pipeleap is a managed service..." → platform-language
- Remove all "we deploy/implement" from body text
- Keep the 4 service cards but frame them as platform modules (e.g., "Outbound Workflow Design" → "Outbound Workflow Engine")
- Update meta description

### 2. `src/pages/About.tsx` — Remove all service/partner language
- Remove `"Sales Operations Partner"` from WebPage schema name → `"About Pipeleap - Sales Operations Platform"`
- Remove `"jobTitle": "Sales Operations Partner"` from Person schema → `"Co-Founder"` or remove jobTitle
- Remove `"Sales operations partner"` from Organization description → platform description
- Replace "Eleven connected modules... built and operated for you" → platform capabilities
- Replace "You do not... pay for software that sits unused" (implies service) → platform value prop
- Replace "We do not sell another tool" (defensive) → confident platform statement
- Replace "One system. One partner. One result." → "One platform. One system. One result."
- Replace "Three. We deploy and run it." → "Three. It runs continuously."
- Replace "We build and maintain the system" → "The platform manages..."
- Replace "Meet Your Sales Ops Partner" heading → "Meet the Team"
- Remove "leverage of a senior revenue team. Without the headcount."
- Remove "we are not it" (line 165) if it denies being software

### 3. `src/pages/Index.tsx` — Fix stats and deployment language
- Replace stat `"100%" "Managed operations" "We deploy, run, and optimize"` → `"100%" "Platform-managed" "The platform handles deployment, run, and optimization."`
- Replace "A phased rollout. We deploy, run, and optimize each phase." → "A phased rollout. Each phase deploys and optimizes automatically."
- Review all "we" language for service implications

### 4. `src/pages/Pricing.tsx` — Platform pricing language
- Replace "flat monthly retainer" → "monthly subscription" (or "flat monthly subscription")
- Replace "engagement model" → "pricing model" or "subscription model"
- Replace "system deployment, monitoring, optimization, and ongoing support" → "platform features"
- Update PricingCard components to not say "retainer"

### 5. `src/components/pricing/PricingTiers.tsx` — Remove service tiers
- Remove "Optional retainer" section header
- Remove "Dedicated strategist" perk → "Dedicated support" or similar
- Remove "Weekly strategy sessions" perk
- Remove "Email infrastructure setup (from $1,500)" → platform-native equivalent or remove
- Change tier descriptions from service-y to software-y

### 6. `src/components/layout/Footer.tsx` — Remove Services section
- Remove the "Services" section (4 items: Outbound Workflow Design, Lead Intelligence Automation, Multi-Channel Outreach Automation, Pipeline Automation)
- Replace with "Platform" section listing capabilities
- Review tagline: "We build the operational layer..." → "The operational layer that eliminates non-selling work."

### 7. `src/components/layout/Navbar.tsx` — Rename Services
- Change `{ label: "Services", path: "/services" }` → `{ label: "Platform", path: "/platform" }`

### 8. `src/pages/Terms.tsx` — Legal language
- Change "sales workflow automation consulting, Sales Ops audit services, and related operational tools. Our services are delivered on a project or subscription basis as agreed in a separate statement of work or service agreement."
  → "a Sales Operations Platform subscription. The Platform is provided on a subscription basis as agreed in a separate subscription agreement."
- Change "sales workflow automation consulting services" → "Sales Operations Platform"
- Change "engagement" → "subscription" throughout
- **Note:** This may need legal review. The Terms page is a legal document.

### 9. `src/pages/OutboundAutomation.tsx` — Remove services language
- Replace "Outbound Sales Automation Services" → "Outbound Sales Automation"
- Replace "sales engagement workflow automation services" → "sales engagement workflow automation"

### 10. `src/components/ComparisonSection.tsx` — Fix cost description
- Change `pipeleap: { text: "Project-based, predictable", type: "positive" }` → `pipeleap: { text: "Subscription-based, predictable", type: "positive" }`

### 11. `src/pages/GTMAudit.tsx`
- Keep as-is. The free audit is legitimately a service. No change needed.

### 12. Routes (App.tsx)
- Route path `/services` → `/platform` (need redirect for backward compat)

## Order of Execution

1. Page components (Tools.tsx, ToolCategory.tsx, ToolDetail.tsx) — already done
2. types/tool.ts — already done
3. Data files (categories.ts, 37 tool files) — already done
4. **Services.tsx** → Platform page rewrite
5. **About.tsx** — remove partner/service language
6. **Index.tsx** — fix stats/deploy language
7. **Pricing.tsx + PricingTiers.tsx** — fix pricing language
8. **Navbar.tsx + Footer.tsx** — rename Services → Platform
9. **Terms.tsx** — legal language shift
10. **OutboundAutomation.tsx** — minor fixes
11. **ComparisonSection.tsx** — minor fix
12. **App.tsx** — route update
13. Build, commit, push

## Risk Items
- **Terms.tsx** is a legal document. Changing "consulting services" → "software subscription" is a substantive legal change. Recommend keeping this until legal review or at least flagging it.
- **Route change** `/services` → `/platform` needs a redirect in Vite config or Vercel to avoid 404s on any existing links.
- **App.tsx** import paths for lazy-loaded Services page need updating if filename changes.
