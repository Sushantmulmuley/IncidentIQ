from fastapi import FastAPI, Request
from normalizer import normalize
from analyzer import analyze
from database import get_db, save_incident, find_similar
import json

app = FastAPI()

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
    cleaned = normalize(logs)
    service  = cleaned["service_name"]
    severity = cleaned["severity"]

    print(f"Service: {service} | Severity: {severity}")

    # Step 2 — check memory — has this happened before?
    db = next(get_db())
    past_incidents = find_similar(db, service)

    memory_text = ""
    if past_incidents:
        print(f"Found {len(past_incidents)} past incidents for {service}!")
        last = past_incidents[0]
        memory_text = f"This service had an incident before. Last root cause: {last.root_cause}"
    else:
        print("First time seeing this service — no memory yet.")

    # Step 3 — AI analysis
    print("Sending to AI...")
    rca = await analyze(cleaned)
    print("AI responded!")

    # Step 4 — save to database (build the memory)
    save_incident(
        db           = db,
        service      = service,
        severity     = severity,
        raw_logs     = logs,
        root_cause   = rca.get("root_cause", ""),
        action_items = json.dumps(rca.get("action_items", [])),
    )
    print("Saved to database.")

    # Step 5 — return everything including memory
    return {
        "service":    service,
        "severity":   severity,
        "memory":     memory_text if memory_text else "First time seeing this incident.",
        "rca":        rca,
    }