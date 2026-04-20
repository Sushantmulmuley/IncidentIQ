content = open("README.md", "w", encoding="utf-8")
content.write("""# IncidentIQ

> The AI-powered incident explainer for teams without a dedicated SRE.
              
## Live demo

https://web-production-1b3385.up.railway.app
Dashboard: https://web-production-1b3385.up.railway.app/dashboard

IncidentIQ reads your server error logs and explains what broke, why it broke, and exactly what to fix — in plain English — delivered to Slack in under 60 seconds. No more 2am log archaeology.

## The problem it solves

When a server breaks at 2am, engineers drown in raw error logs. IncidentIQ automatically explains root cause, timeline, and exact fixes — delivered to Slack in under 60 seconds.

## What makes it different

| Feature | IncidentIQ | AWS DevOps Agent | Datadog |
|---|---|---|---|
| Works with any stack | Yes | No - AWS only | Yes |
| Two-audience RCA | Yes | No | No |
| Incident memory | Yes | No | No |
| Free to run | Yes | No | No |

## Features

- AI root cause analysis using Groq LLaMA 3.3-70B
- Two-audience RCA — technical for engineers, plain English for founders
- Incident memory — surfaces last known fix on repeat failures
- CloudWatch monitoring — auto-polls AWS every 60 seconds
- Slack notifications — color-coded Block Kit cards
- Live incident dashboard at /dashboard

## Quick start

1. Clone and install
    git clone https://github.com/Sushantmulmuley/IncidentIQ
    cd IncidentIQ
    pip install -r requirements.txt

2. Create .env file
    GROQ_API_KEY=your_groq_key
    SLACK_BOT_TOKEN=xoxb-your-token
    SLACK_CHANNEL=#incidents
    AWS_ACCESS_KEY_ID=your_aws_key
    AWS_SECRET_ACCESS_KEY=your_secret
    AWS_REGION=ap-south-1

3. Run the server
    python start.py

4. Run the monitor
    python monitor.py

## Project structure

    main.py            — Web server and pipeline
    normalizer.py      — Log cleaning
    analyzer.py        — Groq AI integration
    database.py        — Incident memory
    slack_notifier.py  — Slack notifications
    dashboard.py       — Web dashboard
    monitor.py         — CloudWatch monitoring

## Tech stack

Python, FastAPI, Groq API, LLaMA 3.3-70B, SQLAlchemy, SQLite, boto3, Slack Block Kit, AWS CloudWatch

## Built by

Sushant Mulmuley — https://github.com/Sushantmulmuley
""")
content.close()
print("Done")