from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from database import SessionLocal, Incident

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request):
    db        = SessionLocal()
    incidents = db.query(Incident).order_by(Incident.created_at.desc()).all()
    db.close()

    service_counts  = {}
    severity_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}

    for inc in incidents:
        service_counts[inc.service_name] = service_counts.get(inc.service_name, 0) + 1
        severity_counts[inc.severity]    = severity_counts.get(inc.severity, 0) + 1

    rows = ""
    for inc in incidents:
        color = {"critical":"#E24B4A","high":"#EF9F27","medium":"#378ADD","low":"#1D9E75"}.get(inc.severity,"#888780")
        rows += f"<tr><td>{inc.id}</td><td>{inc.service_name}</td><td><span style='color:{color}'>{inc.severity.upper()}</span></td><td>{inc.root_cause}</td><td>{inc.created_at.strftime('%d %b %Y %H:%M')}</td></tr>"

    top_services = ""
    for service, count in sorted(service_counts.items(), key=lambda x: x[1], reverse=True):
        top_services += f"<div style='display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #2a2a2a;'><span>{service}</span><span style='background:#1a1a2e;padding:2px 10px;border-radius:20px;color:#7b8cde'>{count}</span></div>"

    html = f"""<!DOCTYPE html>
<html>
<head>
<title>IncidentIQ Dashboard</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,sans-serif;background:#0d0d0d;color:#e0e0e0;padding:30px}}
h1{{font-size:24px;font-weight:600;color:#fff;margin-bottom:4px}}
.sub{{color:#666;font-size:14px;margin-bottom:30px}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:30px}}
.card{{background:#1a1a1a;border-radius:12px;padding:20px;border:1px solid #2a2a2a}}
.num{{font-size:32px;font-weight:700;color:#fff}}
.lbl{{font-size:13px;color:#666;margin-top:4px}}
.section{{background:#1a1a1a;border-radius:12px;padding:20px;border:1px solid #2a2a2a;margin-bottom:20px}}
.stitle{{font-size:15px;font-weight:600;color:#fff;margin-bottom:16px}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;padding:10px 12px;font-size:12px;color:#666;text-transform:uppercase;border-bottom:1px solid #2a2a2a}}
td{{padding:12px;font-size:14px;border-bottom:1px solid #1f1f1f;vertical-align:top}}
.empty{{color:#444;text-align:center;padding:40px}}
textarea{{width:100%;background:#111;border:1px solid #2a2a2a;border-radius:8px;color:#e0e0e0;padding:12px;font-family:monospace;font-size:13px;resize:vertical;min-height:120px}}
textarea:focus{{outline:none;border-color:#7b8cde}}
.btn{{background:#7b8cde;color:#fff;border:none;padding:10px 24px;border-radius:8px;font-size:14px;cursor:pointer;margin-top:12px}}
.btn:hover{{background:#6a6fcc}}
.result{{background:#111;border:1px solid #2a2a2a;border-radius:8px;padding:16px;margin-top:16px;display:none}}
.result-title{{font-size:13px;font-weight:600;color:#7b8cde;margin-bottom:8px}}
.result-body{{font-size:13px;color:#ccc;line-height:1.6}}
</style>
</head>
<body>
<h1>IncidentIQ</h1>
<p class="sub">Real-time incident intelligence dashboard</p>

<div class="section" style="margin-bottom:20px">
<div class="stitle">Analyze logs instantly</div>
<p style="font-size:13px;color:#666;margin-bottom:12px">Paste any server error logs below and get an AI-generated root cause analysis in seconds.</p>
<textarea id="logInput" placeholder="Paste your logs here...&#10;[ERROR] db-conn-pool exhausted max=50&#10;[ERROR] orders-service timeout 5001ms&#10;[ERROR] HTTP 503 /api/checkout failed"></textarea>
<button class="btn" onclick="analyzeLogs()">Analyze logs</button>
<div class="result" id="result">
  <div class="result-title">Root cause</div>
  <div class="result-body" id="rootCause"></div>
  <div class="result-title" style="margin-top:12px">Action items</div>
  <div class="result-body" id="actionItems"></div>
  <div class="result-title" style="margin-top:12px">For your manager</div>
  <div class="result-body" id="founderExp"></div>
  <div class="result-title" style="margin-top:12px">Estimated impact</div>
  <div class="result-body" id="impact"></div>
</div>
</div>

<div class="section" style="margin-bottom:20px">
<div class="stitle">Cloud cost intelligence</div>
<p style="font-size:13px;color:#666;margin-bottom:16px">Calculate incident revenue impact and optimize your cloud spend.</p>

<div style="display:grid;grid-template-columns:1fr 1fr;gap:20px">

<div>
<div style="font-size:13px;font-weight:600;color:#aaa;margin-bottom:10px">Incident cost calculator</div>
<div style="margin-bottom:8px">
  <label style="font-size:12px;color:#666">Average order value (₹)</label>
  <input id="orderValue" type="number" value="850" style="width:100%;background:#111;border:1px solid #2a2a2a;border-radius:6px;color:#e0e0e0;padding:8px;font-size:13px;margin-top:4px">
</div>
<div style="margin-bottom:8px">
  <label style="font-size:12px;color:#666">Orders per hour</label>
  <input id="ordersHour" type="number" value="300" style="width:100%;background:#111;border:1px solid #2a2a2a;border-radius:6px;color:#e0e0e0;padding:8px;font-size:13px;margin-top:4px">
</div>
<div style="margin-bottom:8px">
  <label style="font-size:12px;color:#666">Downtime (minutes)</label>
  <input id="downtimeMins" type="number" value="5" style="width:100%;background:#111;border:1px solid #2a2a2a;border-radius:6px;color:#e0e0e0;padding:8px;font-size:13px;margin-top:4px">
</div>
<button class="btn" onclick="calcIncidentCost()">Calculate cost</button>
<div id="incidentCostResult" style="margin-top:12px;font-size:13px;color:#7b8cde;display:none"></div>
</div>

<div>
<div style="font-size:13px;font-weight:600;color:#aaa;margin-bottom:10px">Cloud cost optimizer</div>
<textarea id="costData" style="width:100%;background:#111;border:1px solid #2a2a2a;border-radius:8px;color:#e0e0e0;padding:12px;font-family:monospace;font-size:12px;resize:vertical;min-height:140px" placeholder="Paste your AWS/GCP bill here...&#10;Example:&#10;EC2: $450/month (t3.large x4)&#10;RDS: $280/month (db.t3.medium)&#10;S3: $45/month (500GB)&#10;CloudWatch: $30/month"></textarea>
<button class="btn" onclick="optimizeCosts()" style="margin-top:8px">Optimize costs</button>
</div>

</div>

<div id="costOptResult" style="margin-top:16px;display:none">
  <div style="font-size:13px;font-weight:600;color:#7b8cde;margin-bottom:8px">Optimization recommendations</div>
  <div id="costOptBody" style="font-size:13px;color:#ccc;line-height:1.7"></div>
</div>
</div>

<div class="cards">
<div class="card"><div class="num">{len(incidents)}</div><div class="lbl">Total incidents</div></div>
<div class="card"><div class="num" style="color:#E24B4A">{severity_counts['critical']+severity_counts['high']}</div><div class="lbl">High + critical</div></div>
<div class="card"><div class="num" style="color:#EF9F27">{len(service_counts)}</div><div class="lbl">Services affected</div></div>
<div class="card"><div class="num" style="color:#1D9E75">{severity_counts['low']+severity_counts['medium']}</div><div class="lbl">Low + medium</div></div>
</div>

<div style="display:grid;grid-template-columns:2fr 1fr;gap:20px">
<div class="section">
<div class="stitle">All incidents</div>
<table>
<thead><tr><th>#</th><th>Service</th><th>Severity</th><th>Root cause</th><th>Time</th></tr></thead>
<tbody>{rows if rows else '<tr><td colspan="5" class="empty">No incidents yet</td></tr>'}</tbody>
</table>
</div>
<div class="section">
<div class="stitle">Most affected services</div>
{top_services if top_services else '<div class="empty">No data yet</div>'}
</div>
</div>

<script>
async function analyzeLogs() {{
  const logs = document.getElementById('logInput').value.trim();
  if (!logs) {{ alert('Please paste some logs first'); return; }}
  
  const btn = document.querySelector('.btn');
  btn.textContent = 'Analyzing...';
  btn.disabled = true;

  try {{
    const response = await fetch('/webhook/raw', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{logs: logs}})
    }});
    
    const data = await response.json();
    const rca  = data.rca;

    document.getElementById('rootCause').textContent   = rca.root_cause || 'Not found';
    document.getElementById('actionItems').innerHTML   = (rca.action_items || []).map((a,i) => `${{i+1}}. ${{a}}`).join('<br>');
    document.getElementById('founderExp').textContent  = rca.founder_explanation || 'Not available';
    document.getElementById('impact').textContent      = rca.estimated_impact || 'Not available';
    document.getElementById('result').style.display    = 'block';

  }} catch(e) {{
    alert('Error: ' + e.message);
  }}

  btn.textContent = 'Analyze logs';
  btn.disabled    = false;
}}

async function calcIncidentCost() {{
  const orderValue  = document.getElementById('orderValue').value;
  const ordersHour  = document.getElementById('ordersHour').value;
  const downtimeMins = document.getElementById('downtimeMins').value;

  const response = await fetch('/cost/incident', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{
      downtime_minutes: parseFloat(downtimeMins),
      orders_per_hour:  parseFloat(ordersHour),
      avg_order_value:  parseFloat(orderValue)
    }})
  }});

  const data = await response.json();
  const el   = document.getElementById('incidentCostResult');
  el.style.display = 'block';
  el.innerHTML = `<strong>Orders lost:</strong> ${{data.orders_lost}}<br>
                  <strong>Revenue impact:</strong> ₹${{data.revenue_lost.toLocaleString()}}<br>
                  <span style="color:#666">${{data.summary}}</span>`;
}}

async function optimizeCosts() {{
  const costData = document.getElementById('costData').value.trim();
  if (!costData) {{ alert('Please paste your cloud cost data first'); return; }}

  const btn = document.querySelectorAll('.btn')[1];
  btn.textContent = 'Analyzing...';
  btn.disabled = true;

  const response = await fetch('/cost/optimize', {{
    method: 'POST',
    headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{cost_data: costData}})
  }});

  const data = await response.json();

  if (data.error) {{
    alert('Error: ' + data.error);
    btn.textContent = 'Optimize costs';
    btn.disabled = false;
    return;
  }}

  const recs = (data.top_recommendations || []).map(r =>
    `<div style="padding:10px 0;border-bottom:1px solid #2a2a2a">
      <span style="color:#7b8cde;font-weight:600">${{r.service}}</span>
      <span style="color:#666;font-size:12px;margin-left:8px">${{r.difficulty}} fix</span><br>
      <span style="color:#ccc">${{r.recommended_action}}</span><br>
      <span style="color:#1D9E75">Save: ${{r.estimated_saving}}/month</span>
    </div>`
  ).join('');

  const quickWins = (data.quick_wins || []).map((w,i) =>
    `${{i+1}}. ${{w}}`
  ).join('<br>');

  document.getElementById('costOptBody').innerHTML = `
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-bottom:16px">
      <div style="background:#111;border-radius:8px;padding:12px;border:1px solid #2a2a2a">
        <div style="font-size:11px;color:#666">Monthly spend</div>
        <div style="font-size:20px;font-weight:700;color:#fff">${{data.total_monthly_spend}}</div>
      </div>
      <div style="background:#111;border-radius:8px;padding:12px;border:1px solid #2a2a2a">
        <div style="font-size:11px;color:#666">Potential savings</div>
        <div style="font-size:20px;font-weight:700;color:#1D9E75">${{data.potential_savings}}</div>
      </div>
      <div style="background:#111;border-radius:8px;padding:12px;border:1px solid #2a2a2a">
        <div style="font-size:11px;color:#666">Savings %</div>
        <div style="font-size:20px;font-weight:700;color:#EF9F27">${{data.savings_percentage}}</div>
      </div>
    </div>
    <div style="margin-bottom:12px;color:#ccc">${{data.summary}}</div>
    <div style="font-size:13px;font-weight:600;color:#aaa;margin-bottom:8px">Top recommendations</div>
    ${{recs}}
    <div style="font-size:13px;font-weight:600;color:#aaa;margin:16px 0 8px">Quick wins (do today)</div>
    <div style="color:#ccc;line-height:1.8">${{quickWins}}</div>
  `;

  document.getElementById('costOptResult').style.display = 'block';
  btn.textContent = 'Optimize costs';
  btn.disabled = false;
}}
</script>
</body>
</html>"""
    return HTMLResponse(content=html)