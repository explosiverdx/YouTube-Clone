"""Notification engine: generates actionable alert summaries using GenAI or rule-based fallback."""

from datetime import datetime

import config

_genai_model = None


def _init_genai():
    global _genai_model
    if config.USE_GENAI and _genai_model is None:
        try:
            import google.generativeai as genai
            genai.configure(api_key=config.GEMINI_API_KEY)
            _genai_model = genai.GenerativeModel("gemini-2.0-flash")
        except Exception as e:
            print(f"GenAI init failed, using fallback: {e}")
            _genai_model = None


def _genai_summarize(alerts: list[dict]) -> str:
    _init_genai()
    if _genai_model is None:
        return ""

    alert_text = "\n".join(
        f"- [{a['severity']}] {a['category']}: {a['message']}" for a in alerts[:20]
    )

    prompt = f"""You are a supply chain risk analyst AI. Analyze these supply chain disruption alerts 
and provide a concise executive summary with:
1. Overall risk assessment (1-2 sentences)
2. Top 3 most critical issues requiring immediate action
3. Recommended actions for each critical issue

Alerts:
{alert_text}

Respond in clear, professional language suitable for a supply chain manager dashboard."""

    try:
        response = _genai_model.generate_content(prompt)
        return response.text
    except Exception as e:
        print(f"GenAI call failed: {e}")
        return ""


def _rule_based_summary(alerts: list[dict]) -> str:
    if not alerts:
        return "No disruptions detected. All supply chain operations are running normally."

    severity_counts = {}
    category_counts = {}
    for a in alerts:
        severity_counts[a["severity"]] = severity_counts.get(a["severity"], 0) + 1
        category_counts[a["category"]] = category_counts.get(a["category"], 0) + 1

    critical = severity_counts.get("CRITICAL", 0)
    high = severity_counts.get("HIGH", 0)
    total = len(alerts)

    lines = [f"**Supply Chain Risk Summary** — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
             "",
             f"**{total} disruptions detected** — {critical} Critical, {high} High priority.",
             ""]

    if critical > 0:
        lines.append("**Immediate Action Required:**")
        for a in alerts:
            if a["severity"] == "CRITICAL":
                lines.append(f"  • {a['message']}")
        lines.append("")

    lines.append("**Breakdown by Category:**")
    for cat, count in sorted(category_counts.items()):
        lines.append(f"  • {cat}: {count} alerts")

    lines.append("")
    lines.append("**Recommended Actions:**")

    if category_counts.get("Inventory", 0) > 0:
        lines.append("  1. Activate emergency procurement for critically low stock items")
    if category_counts.get("Shipment", 0) > 0:
        lines.append("  2. Contact logistics partners for delayed shipments; evaluate alternate routes")
    if category_counts.get("Supplier", 0) > 0:
        lines.append("  3. Review supplier scorecards; initiate backup supplier engagement")

    return "\n".join(lines)


def generate_notifications(alerts: list[dict]) -> dict:
    genai_summary = _genai_summarize(alerts) if config.USE_GENAI else ""
    rule_summary = _rule_based_summary(alerts)

    notifications = []
    for a in alerts:
        notifications.append({
            "id": a["id"],
            "timestamp": a["timestamp"],
            "severity": a["severity"],
            "category": a["category"],
            "type": a["type"],
            "product": a["product"],
            "message": a["message"],
            "details": a.get("details", {}),
        })

    return {
        "generated_at": datetime.now().isoformat(),
        "total_alerts": len(alerts),
        "summary": genai_summary if genai_summary else rule_summary,
        "summary_source": "GenAI (Gemini)" if genai_summary else "Rule-Based Engine",
        "notifications": notifications,
        "severity_breakdown": {
            sev: sum(1 for a in alerts if a["severity"] == sev)
            for sev in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]
        },
    }
