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


async def calculate_incident_cost(data: dict) -> dict:
    """
    Universal incident cost calculator.
    Works for any business type — not just e-commerce.
    Uses industry standard DevOps cost formula.
    """

    # Basic info — required
    downtime_minutes = float(data.get("downtime_minutes", 0))
    monthly_revenue  = float(data.get("monthly_revenue", 0))
    business_type    = data.get("business_type", "other")
    users_affected   = int(data.get("users_affected", 0))

    # Engineering cost — optional
    engineers        = int(data.get("engineers", 0))
    hours_spent      = float(data.get("hours_spent", 0))
    engineer_cost_hr = float(data.get("engineer_cost_hr", 0))

    # SLA penalty — optional
    sla_penalty_hr   = float(data.get("sla_penalty_hr", 0))

    # Churn risk — optional
    customer_ltv     = float(data.get("customer_ltv", 0))
    churn_pct        = float(data.get("churn_pct", 0))

    # Support cost — optional
    support_tickets  = int(data.get("support_tickets", 0))
    cost_per_ticket  = float(data.get("cost_per_ticket", 0))
    refunds          = float(data.get("refunds", 0))

    # ── Calculations ──────────────────────────────────────────

    # 1. Revenue lost
    revenue_per_hour = monthly_revenue / 720  # 720 hours in a month
    hours_down       = downtime_minutes / 60
    revenue_lost     = revenue_per_hour * hours_down

    # 2. Engineering cost
    engineering_cost = engineers * hours_spent * engineer_cost_hr

    # 3. SLA penalty
    sla_penalty = sla_penalty_hr * hours_down

    # 4. Churn risk
    # If churn % not provided, estimate based on business type
    if churn_pct == 0 and users_affected > 0:
        churn_estimates = {
            "ecommerce":  2.0,
            "saas":       1.5,
            "fintech":    3.0,
            "healthcare": 0.5,
            "logistics":  1.0,
            "other":      2.0,
        }
        churn_pct = churn_estimates.get(business_type, 2.0)
        churn_estimated = True
    else:
        churn_estimated = False

    churned_users = round(users_affected * (churn_pct / 100))
    churn_cost    = churned_users * customer_ltv

    # 5. Support cost
    support_cost = (support_tickets * cost_per_ticket) + refunds

    # ── Total ──────────────────────────────────────────────────
    total = revenue_lost + engineering_cost + sla_penalty + churn_cost + support_cost

    return {
        "business_type":     business_type,
        "downtime_minutes":  downtime_minutes,
        "breakdown": {
            "revenue_lost":      round(revenue_lost),
            "engineering_cost":  round(engineering_cost),
            "sla_penalty":       round(sla_penalty),
            "churn_cost":        round(churn_cost),
            "support_cost":      round(support_cost),
        },
        "churn_estimated":   churn_estimated,
        "churned_users":     churned_users,
        "total_cost":        round(total),
        "currency":          "INR",
        "summary":           f"This incident cost approximately ₹{round(total):,} in total. Revenue lost: ₹{round(revenue_lost):,}. Engineering time: ₹{round(engineering_cost):,}."
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