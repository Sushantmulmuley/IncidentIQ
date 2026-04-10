import httpx
import json
import os

# Read .env file directly
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path, "r") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL   = "llama-3.3-70b-versatile"

SYSTEM_PROMPT = """You are an expert DevOps engineer AND a great communicator.

Analyze the server logs and return ONLY a JSON object like this:

{
  "root_cause": "one technical sentence explaining why this happened",
  "severity": "critical or high or medium or low",
  "timeline": ["first thing that happened", "then this", "then this"],
  "action_items": ["specific technical fix 1", "fix 2", "fix 3"],
  "summary": "2 sentence technical summary",
  "founder_explanation": "Plain English for a non-technical founder. No jargon at all. Tell them what the user experienced, roughly how long it lasted, and how long the fix takes. Max 3 sentences.",
  "estimated_impact": "rough business impact e.g. checkout was down for 7 min, roughly 30-50 orders affected"
}

Rules:
- founder_explanation must have ZERO technical jargon
- action_items must be specific with exact values not vague suggestions
- Return ONLY the JSON. No extra text. No markdown."""


async def analyze(normalized):
    if not GROQ_API_KEY:
        return {"error": "GROQ_API_KEY not set in .env file"}

    log_lines = normalized.get("log_lines", [])
    service   = normalized.get("service_name", "unknown")
    severity  = normalized.get("severity", "unknown")

    if not log_lines:
        return {"error": "No log lines found"}

    user_message = f"""
Service: {service}
Severity: {severity}
Logs:
{chr(10).join(log_lines)}

Analyze this incident and return the JSON.
"""

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
                    "max_tokens":  1500,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
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