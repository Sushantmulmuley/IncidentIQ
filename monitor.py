import boto3
import asyncio
import os
import time
from datetime import datetime, timezone
from normalizer import normalize
from analyzer import analyze
from slack_notifier import post_to_slack
from database import SessionLocal, save_incident
import json

# Read .env directly
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()

AWS_ACCESS_KEY_ID     = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION            = os.getenv("AWS_REGION", "ap-south-1")

# Which log groups to monitor
LOG_GROUPS = [
    "/ecs/nodeapp-task-def",
    "/aws/codebuild/webapp-project-dev",
]

# How often to check (in seconds)
POLL_INTERVAL = 60


def get_cloudwatch_client():
    """Create and return a CloudWatch Logs client."""
    return boto3.client(
        "logs",
        aws_access_key_id     = AWS_ACCESS_KEY_ID,
        aws_secret_access_key = AWS_SECRET_ACCESS_KEY,
        region_name           = AWS_REGION,
    )


def fetch_recent_errors(client, log_group, minutes_back=2):
    """
    Fetch ERROR logs from CloudWatch from the last N minutes.
    Returns a list of log message strings.
    """
    now        = int(time.time() * 1000)
    start_time = now - (minutes_back * 60 * 1000)

    try:
        response = client.filter_log_events(
            logGroupName  = log_group,
            startTime     = start_time,
            endTime       = now,
            filterPattern = "ERROR",
        )
        events = response.get("events", [])
        return [e["message"] for e in events]

    except Exception as e:
        print(f"Error fetching logs from {log_group}: {e}")
        return []


async def process_errors(log_group, error_lines):
    """
    Run the full pipeline on detected errors:
    normalize → AI analyze → save to DB → post to Slack
    """
    log_text  = "\n".join(error_lines)
    normalized = normalize(log_text)

    # Override service name with the log group name for clarity
    service = log_group.split("/")[-1]
    normalized["service_name"] = service

    print(f"Analyzing {len(error_lines)} errors from {service}...")
    rca = await analyze(normalized)

    # Save to database
    db = SessionLocal()
    save_incident(
        db           = db,
        service      = service,
        severity     = normalized.get("severity", "high"),
        raw_logs     = log_text,
        root_cause   = rca.get("root_cause", ""),
        action_items = json.dumps(rca.get("action_items", [])),
    )
    db.close()

    # Post to Slack
    memory_text = f"Auto-detected from CloudWatch: {log_group}"
    await post_to_slack(service, normalized.get("severity", "high"), rca, memory_text)

    print(f"Done — incident saved and Slack notified for {service}")


async def monitor_loop():
    """
    Main loop — runs forever.
    Every 60 seconds, checks all log groups for new errors.
    """
    client = get_cloudwatch_client()
    print(f"IncidentIQ Monitor started.")
    print(f"Watching {len(LOG_GROUPS)} log groups every {POLL_INTERVAL} seconds.")
    print(f"Log groups: {LOG_GROUPS}\n")

    while True:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Checking logs...")

        for log_group in LOG_GROUPS:
            errors = fetch_recent_errors(client, log_group)

            if errors:
                print(f"Found {len(errors)} errors in {log_group}!")
                await process_errors(log_group, errors)
            else:
                print(f"No errors in {log_group} — all good.")

        print(f"Sleeping {POLL_INTERVAL} seconds...\n")
        await asyncio.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    asyncio.run(monitor_loop())