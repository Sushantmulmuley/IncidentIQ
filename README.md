python -c "
content = open('README.md', 'w', encoding='utf-8')
content.write('''# IncidentIQ

> AI-powered DevOps incident intelligence platform for teams without a dedicated SRE.

## Live demo

https://web-production-1b3385.up.railway.app
Dashboard: https://web-production-1b3385.up.railway.app/dashboard

## What it does

IncidentIQ reads your server error logs and explains what broke, why it broke, and exactly what to fix in plain English - delivered to Slack in under 60 seconds. No more 2am log archaeology.

## What makes it different

| Feature | IncidentIQ | AWS DevOps Agent | Datadog |
|---|---|---|---|
| Works with any stack | Yes | No - AWS only | Yes |
| Two-audience RCA | Yes | No | No |
| Incident memory | Yes | No | No |
| Auto postmortem PDF | Yes | No | No |
| Cloud cost optimizer | Yes | No | No |
| DevOps AI chatbot | Yes | No | No |
| Free to run | Yes | No | No |

## Features

- AI root cause analysis using Groq LLaMA 3.3-70B - explains what broke in 60 seconds
- Two-audience RCA - technical explanation for engineers + plain English for founders in one AI call
- Incident memory - remembers every past incident, surfaces last known fix on repeat failures
- Auto postmortem PDF - generates complete professional postmortem report automatically
- Cloud cost optimizer - paste your AWS/GCP bill or upload PDF invoice, get specific savings recommendations
- Universal incident cost calculator - calculates revenue lost, engineering cost, SLA penalty, churn risk
- DevOps AI chatbot - ask anything about your incidents OR general DevOps questions
- AWS CloudWatch monitoring - auto-polls log groups every 60 seconds
- Slack notifications - color-coded Block Kit cards with root cause, action items, impact
- Tabbed dashboard - Overview, Analyze, Cost, Incidents, Chat

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

4. Run the CloudWatch monitor

    python monitor.py

Server at http://localhost:8000
Dashboard at http://localhost:8000/dashboard

## Project structure

    main.py              - Web server and pipeline orchestration
    normalizer.py        - Log cleaning and extraction
    analyzer.py          - Groq AI integration
    database.py          - Incident memory (SQLAlchemy + SQLite)
    slack_notifier.py    - Slack Block Kit notifications
    dashboard.py         - Tabbed web dashboard
    monitor.py           - AWS CloudWatch auto-monitoring
    postmortem.py        - Auto postmortem PDF generator
    cost_analyzer.py     - Cloud cost optimizer and incident cost calculator
    whatsapp_notifier.py - WhatsApp alerts (Twilio)

## Tech stack

Python, FastAPI, Groq API (LLaMA 3.3-70B), SQLAlchemy, SQLite, boto3, Slack Block Kit, AWS CloudWatch, ReportLab, PyPDF2, Twilio

## Built by

Sushant Mulmuley
GitHub: https://github.com/Sushantmulmuley
Project: https://github.com/Sushantmulmuley/IncidentIQ
''')
content.close()
print('Done')
"