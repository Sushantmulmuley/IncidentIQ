import os
from twilio.rest import Client

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN  = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_FROM_SMS    = os.getenv("TWILIO_FROM_SMS", "")
SMS_TO             = os.getenv("WHATSAPP_TO", "")


async def send_whatsapp(service, severity, rca):
    """
    Sends incident alert via SMS using Twilio.
    Works on free trial — no template restrictions.
    """
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN or not SMS_TO:
        print("SMS not configured — skipping")
        return

    root_cause = rca.get("root_cause", "Unknown")
    impact     = rca.get("estimated_impact", "Unknown")
    actions    = rca.get("action_items", [])
    first_fix  = actions[0] if actions else "Check logs"

    message = f"""IncidentIQ Alert
Service: {service}
Severity: {severity.upper()}
Root cause: {root_cause}
Fix: {first_fix}
Impact: {impact}"""

    try:
        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        client.messages.create(
            from_ = TWILIO_FROM_SMS,
            to    = SMS_TO,
            body  = message
        )
        print(f"SMS alert sent to {SMS_TO}")

    except Exception as e:
        print(f"SMS error: {e}")