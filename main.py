from postmortem import generate_postmortem_text, generate_pdf
from fastapi.responses import StreamingResponse
from database import SessionLocal, Incident
import io
from fastapi import FastAPI, Request
from normalizer import normalize
from analyzer import analyze
from database import get_db, save_incident, find_similar
from slack_notifier import post_to_slack
from whatsapp_notifier import send_whatsapp
from cost_analyzer import calculate_incident_cost, optimize_cloud_costs, extract_text_from_pdf
from fastapi import UploadFile, File, Form
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
@app.post("/cost/incident")
async def incident_cost(request: Request):
    """Universal incident cost calculator."""
    data   = await request.json()
    result = await calculate_incident_cost(data)
    return result


@app.post("/cost/optimize")
async def optimize_costs(request: Request):
    """Analyze cloud costs and suggest optimizations."""
    data      = await request.json()
    cost_text = data.get("cost_data", "")

    if not cost_text.strip():
        return {"error": "No cost data provided"}

    result = await optimize_cloud_costs(cost_text)
    return result


@app.post("/cost/optimize-pdf")
async def optimize_costs_pdf(file: UploadFile = File(...)):
    """Upload a PDF invoice and get optimization recommendations."""
    file_bytes = await file.read()
    text       = extract_text_from_pdf(file_bytes)

    if not text or "Error" in text:
        return {"error": "Could not read PDF. Try pasting the cost data instead."}

    result = await optimize_cloud_costs(text)
    return result

@app.get("/postmortem/{incident_id}")
async def get_postmortem(incident_id: int):
    """
    Generates and downloads a PDF postmortem for a given incident.
    """
    db       = SessionLocal()
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    db.close()

    if not incident:
        return {"error": "Incident not found"}

    # Build RCA dict from stored data
    rca = {
        "root_cause":          incident.root_cause or "",
        "action_items":        json.loads(incident.action_items) if incident.action_items else [],
        "timeline":            [],
        "founder_explanation": "",
        "estimated_impact":    "",
    }

    # Build incident dict
    inc_dict = {
        "id":           incident.id,
        "service_name": incident.service_name,
        "severity":     incident.severity,
        "raw_logs":     incident.raw_logs,
        "created_at":   str(incident.created_at),
    }

    # Generate postmortem text using AI
    postmortem = await generate_postmortem_text(inc_dict, rca)

    if "error" in postmortem:
        return {"error": postmortem["error"]}

    # Generate PDF
    pdf_bytes = generate_pdf(inc_dict, postmortem)

    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type = "application/pdf",
        headers    = {"Content-Disposition": f"attachment; filename=postmortem-incident-{incident_id}.pdf"}
    )

@app.post("/chat")
async def chat(request: Request):
    """Answer questions about incidents using AI."""
    from analyzer import analyze
    data     = await request.json()
    question = data.get("question", "")

    if not question:
        return {"answer": "Please ask a question."}

    # Get incident summary from database
    db        = SessionLocal()
    incidents = db.query(Incident).order_by(Incident.created_at.desc()).limit(50).all()
    db.close()

    # Build context from incidents
    incident_summary = "\n".join([
        f"#{inc.id} | {inc.service_name} | {inc.severity} | {inc.root_cause} | {inc.created_at}"
        for inc in incidents
    ])

    # Ask Groq with incident context
    import httpx
    import os

    env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if "=" in line:
                    key, value = line.split("=", 1)
                    os.environ[key.strip()] = value.strip()

    groq_key = os.getenv("GROQ_API_KEY", "")

    system_prompt = f"""You are IncidentIQ, an AI assistant that answers questions about a company's incident history.

Here is the incident history:
{incident_summary}

Answer the user's question based on this data. Be specific, concise, and helpful.
If the question cannot be answered from the data, say so honestly."""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={{"Authorization": f"Bearer {{groq_key}}", "Content-Type": "application/json"}},
                json={{
                    "model": "llama-3.3-70b-versatile",
                    "temperature": 0.3,
                    "max_tokens": 500,
                    "messages": [
                        {{"role": "system", "content": system_prompt}},
                        {{"role": "user", "content": question}},
                    ],
                }}
            )
        result  = response.json()
        answer  = result["choices"][0]["message"]["content"]
        return {{"answer": answer}}
    except Exception as e:
        return {{"answer": f"Error: {{str(e)}}"}}