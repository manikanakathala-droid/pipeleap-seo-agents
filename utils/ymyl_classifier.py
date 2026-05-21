"""
YMYL (Your Money or Your Life) topic classifier.

Google applies heightened E-E-A-T scrutiny to content that could significantly
impact a reader's health, financial stability, safety, or legal standing.

For Pipeleap (B2B SaaS / RevOps), the YMYL-adjacent zones are:
  - Financial: revenue projections, ROI claims, investment advice
  - Legal/Compliance: GDPR, CCPA, SOC2, contracts, employment law
  - Data Security: breach implications, credential handling

When YMYL signals are detected the content engine should:
  1. Require a named author with verifiable credentials
  2. Include sourced data / third-party validation
  3. Add a "this is not legal/financial advice" disclaimer where appropriate
  4. Set a 90-day mandatory review date
"""
from __future__ import annotations

YMYL_TAXONOMY: dict[str, dict] = {
    "financial": {
        "signals": [
            "roi", "revenue projection", "financial forecast", "investment",
            "cost savings", "payback period", "irr", "npv", "budget",
            "annual recurring revenue", "arr growth", "financial planning",
        ],
        "risk_level": "HIGH",
        "required_trust_signals": [
            "Named author with financial expertise or company credentials",
            "Sourced data or case study with verifiable outcomes",
            "Disclaimer: results are illustrative, not guaranteed",
        ],
        "disclosure_note": (
            "Financial figures and ROI estimates are illustrative. "
            "Actual results depend on your market, team, and execution."
        ),
    },
    "legal_compliance": {
        "signals": [
            "gdpr", "ccpa", "hipaa", "soc2", "iso 27001", "compliance",
            "data protection", "privacy law", "contract", "terms of service",
            "employment law", "labor law", "non-disclosure", "nda",
            "intellectual property", "liability",
        ],
        "risk_level": "HIGH",
        "required_trust_signals": [
            "Named author with legal or compliance credentials",
            "Reference to official regulatory guidance or legal counsel",
            "Disclaimer: this is not legal advice — consult qualified counsel",
        ],
        "disclosure_note": (
            "This content is for informational purposes only and does not constitute "
            "legal or compliance advice. Consult qualified legal counsel for your situation."
        ),
    },
    "data_security": {
        "signals": [
            "data breach", "credential", "password", "encryption", "vulnerability",
            "penetration test", "security audit", "ransomware", "phishing",
            "zero trust", "access control", "pii", "personally identifiable",
        ],
        "risk_level": "MEDIUM",
        "required_trust_signals": [
            "Named author with security credentials or reference to security team",
            "Accurate, up-to-date technical claims with sources",
        ],
        "disclosure_note": (
            "Security configurations depend on your infrastructure. "
            "Always validate recommendations with your security team."
        ),
    },
}


def classify_ymyl(text: str) -> dict:
    """
    Scan text (title, keyword, or body excerpt) for YMYL signals.

    Returns:
        {
            "is_ymyl": bool,
            "categories": list[str],       # matched YMYL categories
            "max_risk_level": str,         # "HIGH" | "MEDIUM" | "NONE"
            "required_trust_signals": list[str],
            "disclosure_notes": list[str],
        }
    """
    text_lower = text.lower()
    matched_categories: list[str] = []
    trust_signals: list[str] = []
    disclosures: list[str] = []

    for category, spec in YMYL_TAXONOMY.items():
        if any(signal in text_lower for signal in spec["signals"]):
            matched_categories.append(category)
            trust_signals.extend(spec["required_trust_signals"])
            disclosures.append(spec["disclosure_note"])

    risk_level = "NONE"
    if matched_categories:
        levels = [YMYL_TAXONOMY[c]["risk_level"] for c in matched_categories]
        risk_level = "HIGH" if "HIGH" in levels else "MEDIUM"

    return {
        "is_ymyl": bool(matched_categories),
        "categories": matched_categories,
        "max_risk_level": risk_level,
        "required_trust_signals": list(dict.fromkeys(trust_signals)),
        "disclosure_notes": disclosures,
    }
