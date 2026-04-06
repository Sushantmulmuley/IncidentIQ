import re
from datetime import datetime

def normalize(raw_text):
    """
    Takes raw messy log text.
    Returns a clean dictionary the AI can work with.
    """
    return {
        "service_name": extract_service(raw_text),
        "severity":     extract_severity(raw_text),
        "log_lines":    extract_lines(raw_text),
        "timestamp":    datetime.utcnow().isoformat(),
    }

def extract_service(text):
    """Try to find the broken service name from the log text."""
    # Look for patterns like "orders-service" or "payment-gateway"
    match = re.search(r'\b([a-z][a-z0-9]*[-][a-z][a-z0-9]*)\b', text)
    if match:
        return match.group(1)
    return "unknown-service"

def extract_severity(text):
    """Guess how serious the incident is from keywords."""
    text_lower = text.lower()
    if any(w in text_lower for w in ["critical", "fatal", "outage"]):
        return "critical"
    if any(w in text_lower for w in ["error", "failed", "503", "500"]):
        return "high"
    if any(w in text_lower for w in ["warn", "warning", "slow", "timeout"]):
        return "medium"
    return "low"

def extract_lines(text):
    """Split into clean lines. Remove blanks. Max 100 lines."""
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines[:100]