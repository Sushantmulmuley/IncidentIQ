from fastapi import FastAPI, Request
from normalizer import normalize

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

    # Clean and extract info from the raw logs
    cleaned = normalize(logs)

    print("--- Alert received! ---")
    print(f"Service:  {cleaned['service_name']}")
    print(f"Severity: {cleaned['severity']}")
    print(f"Lines:    {len(cleaned['log_lines'])}")
    print("-----------------------")

    return cleaned