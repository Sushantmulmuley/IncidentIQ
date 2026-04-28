import os
import io
import json
import httpx
from datetime import datetime

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = "llama-3.3-70b-versatile"


async def generate_postmortem_text(incident: dict, rca: dict) -> dict:
    """
    Uses AI to generate a complete postmortem narrative from incident data.
    Returns structured postmortem as a dict.
    """
    if not GROQ_API_KEY:
        return {"error": "GROQ_API_KEY not set"}

    system_prompt = """You are a senior SRE writing a professional incident postmortem report.

Return ONLY a JSON object like this:
{
  "executive_summary": "2-3 sentences for non-technical leadership",
  "what_happened": "Clear narrative of what occurred during the incident",
  "root_cause_analysis": "Deep technical explanation of the root cause",
  "contributing_factors": ["factor 1", "factor 2", "factor 3"],
  "impact_summary": "Business and technical impact in plain language",
  "timeline": [
    {"time": "HH:MM", "event": "what happened"}
  ],
  "resolution": "How the incident was resolved",
  "action_items": [
    {"priority": "P1/P2/P3", "action": "specific action", "owner": "team/role", "due": "timeframe"}
  ],
  "prevention": "How to prevent this from happening again",
  "lessons_learned": ["lesson 1", "lesson 2", "lesson 3"]
}

Rules:
- executive_summary must have zero technical jargon
- action_items must be specific and assignable
- Return ONLY the JSON. No extra text."""

    user_message = f"""Generate a postmortem for this incident:

Service: {incident.get('service_name', 'unknown')}
Severity: {incident.get('severity', 'unknown')}
Time: {incident.get('created_at', 'unknown')}
Raw logs: {incident.get('raw_logs', '')[:500]}

AI analysis:
Root cause: {rca.get('root_cause', '')}
Action items: {json.dumps(rca.get('action_items', []))}
Timeline: {json.dumps(rca.get('timeline', []))}
Founder explanation: {rca.get('founder_explanation', '')}
Estimated impact: {rca.get('estimated_impact', '')}

Generate the complete postmortem JSON."""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type":  "application/json",
                },
                json={
                    "model":       GROQ_MODEL,
                    "temperature": 0.2,
                    "max_tokens":  2000,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user",   "content": user_message},
                    ],
                }
            )

        result  = response.json()
        content = result["choices"][0]["message"]["content"]
        content = content.strip().replace("```json", "").replace("```", "").strip()
        return json.loads(content)

    except Exception as e:
        return {"error": str(e)}


def generate_pdf(incident: dict, postmortem: dict) -> bytes:
    """
    Generates a professional PDF postmortem report.
    Returns PDF as bytes.
    """
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    from reportlab.lib.enums import TA_LEFT, TA_CENTER

    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(
        buffer,
        pagesize    = A4,
        rightMargin = 2*cm,
        leftMargin  = 2*cm,
        topMargin   = 2*cm,
        bottomMargin= 2*cm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "Title",
        parent    = styles["Heading1"],
        fontSize  = 20,
        textColor = colors.HexColor("#1a1a1a"),
        spaceAfter= 6,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent    = styles["Normal"],
        fontSize  = 11,
        textColor = colors.HexColor("#666666"),
        spaceAfter= 20,
    )
    heading_style = ParagraphStyle(
        "Heading",
        parent    = styles["Heading2"],
        fontSize  = 13,
        textColor = colors.HexColor("#0C447C"),
        spaceBefore=16,
        spaceAfter= 6,
    )
    body_style = ParagraphStyle(
        "Body",
        parent    = styles["Normal"],
        fontSize  = 10,
        textColor = colors.HexColor("#333333"),
        spaceAfter= 8,
        leading   = 16,
    )
    bullet_style = ParagraphStyle(
        "Bullet",
        parent     = styles["Normal"],
        fontSize   = 10,
        textColor  = colors.HexColor("#333333"),
        spaceAfter = 4,
        leftIndent = 16,
        leading    = 14,
    )

    severity_colors = {
        "critical": "#E24B4A",
        "high":     "#EF9F27",
        "medium":   "#378ADD",
        "low":      "#1D9E75",
    }

    service   = incident.get("service_name", "unknown")
    severity  = incident.get("severity", "unknown")
    inc_id    = incident.get("id", "?")
    created   = incident.get("created_at", datetime.utcnow())
    sev_color = colors.HexColor(severity_colors.get(severity, "#888780"))

    story = []

    # Header
    story.append(Paragraph("INCIDENT POSTMORTEM REPORT", title_style))
    story.append(Paragraph(f"Generated by IncidentIQ • {datetime.utcnow().strftime('%d %b %Y %H:%M')} UTC", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#0C447C")))
    story.append(Spacer(1, 12))

    # Incident summary table
    summary_data = [
        ["Incident ID", f"#{inc_id}"],
        ["Service", service],
        ["Severity", severity.upper()],
        ["Date", str(created)[:16] if created else "Unknown"],
        ["Status", "Resolved"],
    ]
    summary_table = Table(summary_data, colWidths=[4*cm, 13*cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#F5F5F5")),
        ("TEXTCOLOR",  (0,0), (0,-1), colors.HexColor("#666666")),
        ("FONTSIZE",   (0,0), (-1,-1), 10),
        ("FONTNAME",   (0,0), (0,-1), "Helvetica-Bold"),
        ("PADDING",    (0,0), (-1,-1), 8),
        ("GRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#DDDDDD")),
        ("TEXTCOLOR",  (1,2), (1,2), sev_color),
        ("FONTNAME",   (1,2), (1,2), "Helvetica-Bold"),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 16))

    # Executive Summary
    story.append(Paragraph("Executive Summary", heading_style))
    story.append(Paragraph(postmortem.get("executive_summary", "N/A"), body_style))

    # What Happened
    story.append(Paragraph("What Happened", heading_style))
    story.append(Paragraph(postmortem.get("what_happened", "N/A"), body_style))

    # Root Cause
    story.append(Paragraph("Root Cause Analysis", heading_style))
    story.append(Paragraph(postmortem.get("root_cause_analysis", "N/A"), body_style))

    # Contributing factors
    factors = postmortem.get("contributing_factors", [])
    if factors:
        story.append(Paragraph("Contributing Factors", heading_style))
        for f in factors:
            story.append(Paragraph(f"• {f}", bullet_style))

    # Impact
    story.append(Paragraph("Impact", heading_style))
    story.append(Paragraph(postmortem.get("impact_summary", "N/A"), body_style))

    # Timeline
    timeline = postmortem.get("timeline", [])
    if timeline:
        story.append(Paragraph("Timeline", heading_style))
        tl_data = [["Time", "Event"]] + [[t.get("time",""), t.get("event","")] for t in timeline]
        tl_table = Table(tl_data, colWidths=[3*cm, 14*cm])
        tl_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0C447C")),
            ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
            ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",   (0,0), (-1,-1), 9),
            ("PADDING",    (0,0), (-1,-1), 6),
            ("GRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#DDDDDD")),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F9F9F9")]),
        ]))
        story.append(tl_table)

    # Resolution
    story.append(Paragraph("Resolution", heading_style))
    story.append(Paragraph(postmortem.get("resolution", "N/A"), body_style))

    # Action items
    actions = postmortem.get("action_items", [])
    if actions:
        story.append(Paragraph("Action Items", heading_style))
        ai_data = [["Priority", "Action", "Owner", "Due"]] + [
            [a.get("priority",""), a.get("action",""), a.get("owner",""), a.get("due","")]
            for a in actions
        ]
        ai_table = Table(ai_data, colWidths=[2*cm, 9*cm, 3.5*cm, 2.5*cm])
        ai_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#0C447C")),
            ("TEXTCOLOR",  (0,0), (-1,0), colors.white),
            ("FONTNAME",   (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE",   (0,0), (-1,-1), 9),
            ("PADDING",    (0,0), (-1,-1), 6),
            ("GRID",       (0,0), (-1,-1), 0.5, colors.HexColor("#DDDDDD")),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#F9F9F9")]),
            ("WORDWRAP",   (1,1), (1,-1), True),
        ]))
        story.append(ai_table)

    # Prevention
    story.append(Paragraph("Prevention", heading_style))
    story.append(Paragraph(postmortem.get("prevention", "N/A"), body_style))

    # Lessons learned
    lessons = postmortem.get("lessons_learned", [])
    if lessons:
        story.append(Paragraph("Lessons Learned", heading_style))
        for l in lessons:
            story.append(Paragraph(f"• {l}", bullet_style))

    # Footer
    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#DDDDDD")))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        f"Generated automatically by IncidentIQ • github.com/Sushantmulmuley/IncidentIQ",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=8, textColor=colors.HexColor("#999999"), alignment=TA_CENTER)
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()