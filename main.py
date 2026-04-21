from fastapi import FastAPI, Request
from normalizer import normalize
from analyzer import analyze
from database import get_db, save_incident, find_similar
from slack_notifier import post_to_slack
from whatsapp_notifier import send_whatsapp
from dashboard import router as dashboard_router
import json

app = FastAPI()
app.include_router(dashboard_router)

@app.get("/")
def home():
    return {"message": "IncidentIQ is alive!"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/webhook/raw")
async def receive_alert(request: Request):
    data = await request.json()
    logs = data.get("logs", "")

    # Step 1 — clean the logs
    cleaned  = normalize(logs)
    service  = cleaned["service_name"]
    severity = cleaned["severity"]
    print(f"Service: {service} | Severity: {severity}")

    # Step 2 — check memory
    db             = next(get_db())
    past_incidents = find_similar(db, service)

    memory_text = ""
    if past_incidents:
        last        = past_incidents[0]
        memory_text = f"Seen before. Last fix: {last.root_cause}"
        print(f"Memory found: {len(past_incidents)} past incidents")
    else:
        memory_text = "First time seeing this incident."
        print("No memory — first time")

    # Step 3 — AI analysis
    print("Sending to AI...")
    rca = await analyze(cleaned)
    print("AI responded!")

    # Step 4 — save to database
    save_incident(
        db           = db,
        service      = service,
        severity     = severity,
        raw_logs     = logs,
        root_cause   = rca.get("root_cause", ""),
        action_items = json.dumps(rca.get("action_items", [])),
    )
    print("Saved to database.")

    # Step 5 — post to Slack
    await post_to_slack(service, severity, rca, memory_text)

    # Step 6 — post to WhatsApp
    await send_whatsapp(service, severity, rca)

    # Step 7 — return full response
    return {
        "service":  service,
        "severity": severity,
        "memory":   memory_text,
        "rca":      rca,
    }