import httpx
import os

# Read .env file directly
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

SLACK_BOT_TOKEN = os.getenv("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL   = os.getenv("SLACK_CHANNEL", "#all-devops")

SEVERITY_COLOR = {
    "critical": "#E24B4A",
    "high":     "#EF9F27",
    "medium":   "#378ADD",
    "low":      "#1D9E75",
}

async def post_to_slack(service, severity, rca, memory):
    """
    Posts a formatted incident card to Slack.
    Shows both technical RCA and founder explanation.
    """
    if not SLACK_BOT_TOKEN:
        print("No Slack token — skipping Slack notification")
        return

    color        = SEVERITY_COLOR.get(severity, "#888780")
    root_cause   = rca.get("root_cause", "Unknown")
    actions      = rca.get("action_items", [])
    founder_exp  = rca.get("founder_explanation", "")
    impact       = rca.get("estimated_impact", "")

    # Format action items as numbered list
    actions_text = "\n".join(f"{i+1}. {a}" for i, a in enumerate(actions))

    blocks = [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":red_circle: *Incident detected — {service}* (Severity: {severity.upper()})"
            }
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Root cause*\n{root_cause}"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Action items*\n{actions_text}"
            }
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":bust_in_silhouette: *For your manager*\n{founder_exp}"
            }
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f":chart_with_downwards_trend: *Impact:* {impact}  |  :brain: *Memory:* {memory}"
                }
            ]
        }
    ]

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "https://slack.com/api/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {SLACK_BOT_TOKEN}",
                    "Content-Type":  "application/json",
                },
                json={
                    "channel":     SLACK_CHANNEL,
                    "attachments": [{
                        "color":  color,
                        "blocks": blocks,
                    }]
                }
            )
        result = response.json()
        if result.get("ok"):
            print("Slack notification sent!")
        else:
            print(f"Slack error: {result.get('error')}")

    except Exception as e:
        print(f"Failed to send Slack message: {e}")