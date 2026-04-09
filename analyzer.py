import httpx
import json
import os
from dotenv import load_dotenv

load_dotenv()

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
  "founder_explanation": "Explain this incident in plain English for a non-technical founder or manager. No jargon. Mention what the user experienced, how long it may have lasted, rough revenue/order impact if possible, and how long the fix takes. Max 3 sentences.",
  "estimated_impact": "rough estimate of business impact e.g. checkout down for ~7 min, ~30-50 orders affected"
}

Rules:
- founder_explanation must have ZERO technical jargon
- action_items must be specific — exact values, not vague suggestions
- Return ONLY the JSON. No extra text."""


async def analyze(normalized):
    """Send cleaned logs to Groq AI. Get back full RCA for both engineers and founders."""

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