import os
import json
import httpx

# Read .env directly
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


async def calculate_incident_cost(downtime_minutes, orders_per_hour, avg_order_value):
    """
    Calculate revenue lost during an incident.
    Simple math — no AI needed for this part.
    """
    hours_down    = downtime_minutes / 60
    orders_lost   = hours_down * orders_per_hour
    revenue_lost  = orders_lost * avg_order_value

    return {
        "downtime_minutes": downtime_minutes,
        "orders_lost":      round(orders_lost),
        "revenue_lost":     round(revenue_lost),
        "currency":         "INR",
        "summary":          f"Approximately {round(orders_lost)} orders lost. Estimated revenue impact: ₹{round(revenue_lost):,}"
    }


async def optimize_cloud_costs(cost_data: str) -> dict:
    """
    Send cloud cost data to AI and get optimization recommendations.
    cost_data can be pasted text or extracted PDF text.
    """
    if not GROQ_API_KEY:
        return {"error": "GROQ_API_KEY not set"}

    if not cost_data.strip():
        return {"error": "No cost data provided"}

    system_prompt = """You are a cloud cost optimization expert with 10 years experience.

Analyze the cloud cost data provided and return ONLY a JSON object like this:

{
  "total_monthly_spend": "amount in INR or USD",
  "potential_savings": "estimated amount you can save per month",
  "savings_percentage": "percentage you can save",
  "top_recommendations": [
    {
      "service": "service name e.g. EC2, RDS, S3",
      "current_spend": "current monthly cost",
      "recommended_action": "specific action to take",
      "estimated_saving": "how much this saves per month",
      "difficulty": "easy/medium/hard"
    }
  ],
  "quick_wins": ["3-5 immediate actions that take less than 1 hour each"],
  "summary": "2-3 sentence plain English summary of findings"
}

Rules:
- Be specific — name exact instance types, services, regions
- quick_wins must be actionable today
- Return ONLY the JSON. No extra text."""

    user_message = f"""Analyze this cloud cost data and provide optimization recommendations:

{cost_data}

Return the optimization JSON."""

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


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extract text from a PDF invoice.
    Returns the text content as a string.
    """
    try:
        import PyPDF2
        import io

        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text   = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text.strip()

    except Exception as e:
        return f"Error reading PDF: {e}"