import os
from twilio.rest import Client

# Read .env directly
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

TWILIO_ACCOUNT_SID  = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN   = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM         = os.getenv("TWILIO_FROM", "whatsapp:+14155238886")
WHATSAPP_TO         = os.getenv("WHATSAPP_TO", "")


async def send_whatsapp(service, severity, rca):
    """
    Sends an incident summary to WhatsApp.
    Uses Twilio WhatsApp sandbox for testing.
    """
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not WHATSAPP_TO:
        print("WhatsApp not configured — skipping")
        return

    root_cause  = rca.get("root_cause", "Unknown")
    actions     = rca.get("action_items", [])
    impact      = rca.get("estimated_impact", "Unknown")
    founder_exp = rca.get("founder_explanation", "")

    # Format the message
    actions_text = "\n".join(f"{i+1}. {a}" for i, a in enumerate(actions[:3]))

    message = f"""*IncidentIQ Alert*

*Service:* {service}
*Severity:* {severity.upper()}

*Root cause:*
{root_cause}

*Action items:*
{actions_text}

*For your manager:*
{founder_exp}

*Impact:* {impact}"""

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            from_  = TWILIO_FROM,
            to     = f"whatsapp:{WHATSAPP_TO}",
            body   = message
        )
        print(f"WhatsApp alert sent to {WHATSAPP_TO}")

    except Exception as e:
        print(f"WhatsApp error: {e}")