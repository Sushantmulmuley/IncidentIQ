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

    # Recent 5 incidents for overview tab
    recent_rows = ""
    for inc in incidents[:5]:
        color = {"critical":"#E24B4A","high":"#EF9F27","medium":"#378ADD","low":"#1D9E75"}.get(inc.severity,"#888780")
        recent_rows += f"<tr><td>{inc.id}</td><td>{inc.service_name}</td><td><span style='color:{color}'>{inc.severity.upper()}</span></td><td>{inc.root_cause[:80]}...</td><td>{inc.created_at.strftime('%d %b %H:%M')}</td></tr>"

    # All incidents for incidents tab
    all_rows = ""
    for inc in incidents:
        color = {"critical":"#E24B4A","high":"#EF9F27","medium":"#378ADD","low":"#1D9E75"}.get(inc.severity,"#888780")
        all_rows += f"<tr><td>{inc.id}</td><td>{inc.service_name}</td><td><span style='color:{color}'>{inc.severity.upper()}</span></td><td>{inc.root_cause}</td><td>{inc.created_at.strftime('%d %b %Y %H:%M')}</td><td><a href='/postmortem/{inc.id}' style='color:#7b8cde;font-size:12px;text-decoration:none'>Download PDF</a></td></tr>"

    # Top services
    top_services = ""
    for service, count in sorted(service_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
        top_services += f"<div style='display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #2a2a2a;'><span>{service}</span><span style='background:#1a1a2e;padding:2px 10px;border-radius:20px;color:#7b8cde'>{count}</span></div>"

    html = f"""<!DOCTYPE html>
<html>
<head>
<title>IncidentIQ Dashboard</title>
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:-apple-system,sans-serif;background:#0d0d0d;color:#e0e0e0}}
.header{{background:#111;border-bottom:1px solid #2a2a2a;padding:16px 30px;display:flex;align-items:center;gap:16px}}
.logo{{font-size:18px;font-weight:600;color:#fff}}
.logo span{{color:#7b8cde}}
.nav{{display:flex;gap:4px;margin-left:auto}}
.nav-btn{{background:none;border:none;color:#666;font-size:13px;padding:8px 14px;border-radius:6px;cursor:pointer;transition:all .15s}}
.nav-btn:hover{{background:#1a1a1a;color:#e0e0e0}}
.nav-btn.active{{background:#1a1a2e;color:#7b8cde;font-weight:500}}
.content{{padding:28px 30px}}
.tab{{display:none}}
.tab.active{{display:block}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:24px}}
.card{{background:#1a1a1a;border-radius:10px;padding:18px;border:1px solid #2a2a2a}}
.num{{font-size:28px;font-weight:700;color:#fff}}
.lbl{{font-size:12px;color:#666;margin-top:4px}}
.section{{background:#1a1a1a;border-radius:10px;padding:20px;border:1px solid #2a2a2a;margin-bottom:16px}}
.stitle{{font-size:14px;font-weight:600;color:#fff;margin-bottom:14px}}
table{{width:100%;border-collapse:collapse}}
th{{text-align:left;padding:10px 12px;font-size:11px;color:#666;text-transform:uppercase;letter-spacing:.05em;border-bottom:1px solid #2a2a2a}}
td{{padding:11px 12px;font-size:13px;border-bottom:1px solid #1f1f1f;vertical-align:top}}
.empty{{color:#444;text-align:center;padding:40px}}
textarea{{width:100%;background:#111;border:1px solid #2a2a2a;border-radius:8px;color:#e0e0e0;padding:12px;font-family:monospace;font-size:13px;resize:vertical;min-height:120px}}
textarea:focus{{outline:none;border-color:#7b8cde}}
.btn{{background:#7b8cde;color:#fff;border:none;padding:10px 20px;border-radius:8px;font-size:13px;cursor:pointer;margin-top:10px}}
.btn:hover{{background:#6a6fcc}}
.two-col{{display:grid;grid-template-columns:1fr 1fr;gap:20px}}
input[type=number],input[type=text],select{{width:100%;background:#111;border:1px solid #2a2a2a;border-radius:6px;color:#e0e0e0;padding:8px 10px;font-size:13px;margin-top:4px}}
label{{font-size:12px;color:#666}}
.field{{margin-bottom:10px}}
details summary{{font-size:12px;color:#7b8cde;cursor:pointer;margin-bottom:8px;list-style:none}}
details summary::-webkit-details-marker{{display:none}}
.chat-box{{background:#111;border:1px solid #2a2a2a;border-radius:10px;height:400px;overflow-y:auto;padding:16px;margin-bottom:12px;display:flex;flex-direction:column;gap:12px}}
.chat-msg{{max-width:80%;padding:10px 14px;border-radius:8px;font-size:13px;line-height:1.6}}
.chat-user{{background:#1a1a2e;color:#e0e0e0;align-self:flex-end;border:1px solid #2a2a3e}}
.chat-ai{{background:#1a1a1a;color:#ccc;align-self:flex-start;border:1px solid #2a2a2a}}
.chat-input-row{{display:flex;gap:10px}}
.chat-input{{flex:1;background:#111;border:1px solid #2a2a2a;border-radius:8px;color:#e0e0e0;padding:10px 14px;font-size:13px}}
.chat-input:focus{{outline:none;border-color:#7b8cde}}
.send-btn{{background:#7b8cde;color:#fff;border:none;padding:10px 20px;border-radius:8px;font-size:13px;cursor:pointer}}
</style>
</head>
<body>

<div class="header">
  <div class="logo">Incident<span>IQ</span></div>
  <div class="nav">
    <button class="nav-btn active" onclick="showTab('overview', this)">Overview</button>
    <button class="nav-btn" onclick="showTab('analyze', this)">Analyze</button>
    <button class="nav-btn" onclick="showTab('cost', this)">Cost</button>
    <button class="nav-btn" onclick="showTab('incidents', this)">Incidents</button>
    <button class="nav-btn" onclick="showTab('chat', this)">Chat</button>
  </div>
</div>

<div class="content">

<!-- TAB 1: OVERVIEW -->
<div id="tab-overview" class="tab active">
  <div class="cards">
    <div class="card"><div class="num">{len(incidents)}</div><div class="lbl">Total incidents</div></div>
    <div class="card"><div class="num" style="color:#E24B4A">{severity_counts['critical']+severity_counts['high']}</div><div class="lbl">High + critical</div></div>
    <div class="card"><div class="num" style="color:#EF9F27">{len(service_counts)}</div><div class="lbl">Services affected</div></div>
    <div class="card"><div class="num" style="color:#1D9E75">{severity_counts['low']+severity_counts['medium']}</div><div class="lbl">Low + medium</div></div>
  </div>

  <div style="display:grid;grid-template-columns:2fr 1fr;gap:16px">
    <div class="section">
      <div class="stitle">Recent incidents</div>
      <table>
        <thead><tr><th>#</th><th>Service</th><th>Severity</th><th>Root cause</th><th>Time</th></tr></thead>
        <tbody>{recent_rows if recent_rows else '<tr><td colspan="5" class="empty">No incidents yet</td></tr>'}</tbody>
      </table>
    </div>
    <div class="section">
      <div class="stitle">Most affected services</div>
      {top_services if top_services else '<div class="empty">No data yet</div>'}
    </div>
  </div>
</div>

<!-- TAB 2: ANALYZE -->
<div id="tab-analyze" class="tab">
  <div class="section">
    <div class="stitle">Analyze logs instantly</div>
    <p style="font-size:13px;color:#666;margin-bottom:12px">Paste any server error logs and get an AI-generated root cause analysis in seconds.</p>
    <textarea id="logInput" placeholder="Paste your logs here...&#10;[ERROR] db-conn-pool exhausted max=50&#10;[ERROR] orders-service timeout 5001ms&#10;[ERROR] HTTP 503 /api/checkout failed"></textarea>
    <button class="btn" onclick="analyzeLogs()">Analyze logs</button>
    <div id="result" style="display:none;margin-top:16px">
      <div class="section" style="margin-top:0">
        <div style="font-size:13px;font-weight:600;color:#7b8cde;margin-bottom:6px">Root cause</div>
        <div id="rootCause" style="font-size:13px;color:#ccc;margin-bottom:12px"></div>
        <div style="font-size:13px;font-weight:600;color:#7b8cde;margin-bottom:6px">Action items</div>
        <div id="actionItems" style="font-size:13px;color:#ccc;margin-bottom:12px"></div>
        <div style="font-size:13px;font-weight:600;color:#7b8cde;margin-bottom:6px">For your manager</div>
        <div id="founderExp" style="font-size:13px;color:#ccc;margin-bottom:12px"></div>
        <div style="font-size:13px;font-weight:600;color:#7b8cde;margin-bottom:6px">Estimated impact</div>
        <div id="impact" style="font-size:13px;color:#ccc"></div>
      </div>
    </div>
  </div>
</div>

<!-- TAB 3: COST -->
<div id="tab-cost" class="tab">
  <div class="two-col">

    <div class="section">
      <div class="stitle">Incident cost calculator</div>
      <div class="field"><label>Business type</label>
        <select id="bizType">
          <option value="ecommerce">E-commerce</option>
          <option value="saas">SaaS</option>
          <option value="fintech">Fintech</option>
          <option value="healthcare">Healthcare</option>
          <option value="logistics">Logistics</option>
          <option value="other">Other</option>
        </select>
      </div>
      <div class="field"><label>Monthly revenue (₹)</label><input id="monthlyRevenue" type="number" value="5000000"></div>
      <div class="field"><label>Downtime (minutes)</label><input id="downtimeMins" type="number" value="7"></div>
      <div class="field"><label>Users affected</label><input id="usersAffected" type="number" value="500"></div>

      <details style="margin-bottom:10px">
        <summary>+ Engineering cost</summary>
        <div style="padding:8px 0">
          <div class="field"><label>Engineers involved</label><input id="engineers" type="number" placeholder="3"></div>
          <div class="field"><label>Hours spent</label><input id="hoursSpent" type="number" placeholder="2"></div>
          <div class="field"><label>Cost per engineer/hour (₹)</label><input id="engineerCost" type="number" placeholder="2000"></div>
        </div>
      </details>

      <details style="margin-bottom:10px">
        <summary>+ SLA penalty</summary>
        <div style="padding:8px 0">
          <div class="field"><label>Penalty per hour of breach (₹)</label><input id="slaPenalty" type="number" placeholder="50000"></div>
        </div>
      </details>

      <details style="margin-bottom:10px">
        <summary>+ Churn risk</summary>
        <div style="padding:8px 0">
          <div class="field"><label>Customer lifetime value (₹)</label><input id="customerLtv" type="number" placeholder="12000"></div>
          <div class="field"><label>Churn % (leave blank to auto-estimate)</label><input id="churnPct" type="number" placeholder="2"></div>
        </div>
      </details>

      <details style="margin-bottom:10px">
        <summary>+ Support cost</summary>
        <div style="padding:8px 0">
          <div class="field"><label>Extra support tickets</label><input id="supportTickets" type="number" placeholder="45"></div>
          <div class="field"><label>Cost per ticket (₹)</label><input id="costPerTicket" type="number" placeholder="500"></div>
          <div class="field"><label>Refunds issued (₹)</label><input id="refunds" type="number" placeholder="8000"></div>
        </div>
      </details>

      <button class="btn" onclick="calcIncidentCost()">Calculate total cost</button>
      <div id="incidentCostResult" style="margin-top:12px;display:none"></div>
    </div>

    <div class="section">
      <div class="stitle">Cloud cost optimizer</div>
      <p style="font-size:13px;color:#666;margin-bottom:12px">Paste your AWS/GCP bill or upload an invoice PDF.</p>
      <textarea id="costData" style="min-height:140px" placeholder="EC2: $450/month (t3.large x4)&#10;RDS: $280/month (db.t3.medium)&#10;S3: $45/month (500GB)"></textarea>
      <div style="margin-top:10px;padding:10px;background:#0d0d0d;border:1px dashed #2a2a2a;border-radius:8px;text-align:center">
        <label style="font-size:12px;color:#666;cursor:pointer">
          Or upload invoice PDF
          <input type="file" id="pdfFile" accept=".pdf" style="display:none" onchange="handlePdfUpload(this)">
          <span style="color:#7b8cde;margin-left:6px;text-decoration:underline">Browse file</span>
        </label>
        <div id="pdfStatus" style="font-size:12px;color:#666;margin-top:4px"></div>
      </div>
      <button class="btn" onclick="optimizeCosts()">Optimize costs</button>
      <div id="costOptResult" style="margin-top:16px;display:none">
        <div id="costOptBody" style="font-size:13px;color:#ccc;line-height:1.7"></div>
      </div>
    </div>

  </div>
</div>

<!-- TAB 4: INCIDENTS -->
<div id="tab-incidents" class="tab">
  <div class="section">
    <div class="stitle">All incidents</div>
    <table>
      <thead><tr><th>#</th><th>Service</th><th>Severity</th><th>Root cause</th><th>Time</th><th>Postmortem</th></tr></thead>
      <tbody>{all_rows if all_rows else '<tr><td colspan="6" class="empty">No incidents yet</td></tr>'}</tbody>
    </table>
  </div>
</div>

<!-- TAB 5: CHAT -->
<div id="tab-chat" class="tab">
  <div class="section">
    <div class="stitle">DevOps AI Assistant</div>
    <p style="font-size:13px;color:#666;margin-bottom:12px">Ask anything — about your incidents or general DevOps questions.</p>

    <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px">
      <button onclick="askSuggested(this)" style="background:#1a1a2e;border:1px solid #2a2a3e;color:#7b8cde;padding:6px 12px;border-radius:20px;font-size:12px;cursor:pointer">Which service breaks most?</button>
      <button onclick="askSuggested(this)" style="background:#1a1a2e;border:1px solid #2a2a3e;color:#7b8cde;padding:6px 12px;border-radius:20px;font-size:12px;cursor:pointer">What happened this week?</button>
      <button onclick="askSuggested(this)" style="background:#1a1a2e;border:1px solid #2a2a3e;color:#7b8cde;padding:6px 12px;border-radius:20px;font-size:12px;cursor:pointer">How to fix connection pool exhaustion?</button>
      <button onclick="askSuggested(this)" style="background:#1a1a2e;border:1px solid #2a2a3e;color:#7b8cde;padding:6px 12px;border-radius:20px;font-size:12px;cursor:pointer">What is MTTR and how to improve it?</button>
      <button onclick="askSuggested(this)" style="background:#1a1a2e;border:1px solid #2a2a3e;color:#7b8cde;padding:6px 12px;border-radius:20px;font-size:12px;cursor:pointer">Best practices for AWS CloudWatch alerts?</button>
      <button onclick="askSuggested(this)" style="background:#1a1a2e;border:1px solid #2a2a3e;color:#7b8cde;padding:6px 12px;border-radius:20px;font-size:12px;cursor:pointer">What caused the last critical incident?</button>
    </div>

    <div class="chat-box" id="chatBox">
      <div class="chat-msg chat-ai">Hi! I am your DevOps AI Assistant. I can answer questions about your incidents AND general DevOps topics — AWS, Kubernetes, monitoring, incident response, best practices. What do you want to know?</div>
    </div>
    <div class="chat-input-row">
      <input class="chat-input" id="chatInput" type="text" placeholder="Ask about your incidents or any DevOps question..." onkeydown="if(event.key==='Enter') sendChat()">
      <button class="send-btn" onclick="sendChat()">Send</button>
    </div>
  </div>
</div>

</div>

<script>
function showTab(name, btn) {{
  document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
  document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
  document.getElementById('tab-' + name).classList.add('active');
  btn.classList.add('active');
}}

async function analyzeLogs() {{
  const logs = document.getElementById('logInput').value.trim();
  if (!logs) {{ alert('Please paste some logs first'); return; }}
  const btn = document.querySelector('#tab-analyze .btn');
  btn.textContent = 'Analyzing...'; btn.disabled = true;
  try {{
    const response = await fetch('/webhook/raw', {{
      method: 'POST', headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{logs: logs}})
    }});
    const data = await response.json();
    const rca  = data.rca;
    document.getElementById('rootCause').textContent  = rca.root_cause || 'Not found';
    document.getElementById('actionItems').innerHTML  = (rca.action_items || []).map((a,i) => `${{i+1}}. ${{a}}`).join('<br>');
    document.getElementById('founderExp').textContent = rca.founder_explanation || 'Not available';
    document.getElementById('impact').textContent     = rca.estimated_impact || 'Not available';
    document.getElementById('result').style.display   = 'block';
  }} catch(e) {{ alert('Error: ' + e.message); }}
  btn.textContent = 'Analyze logs'; btn.disabled = false;
}}

async function calcIncidentCost() {{
  const payload = {{
    business_type:    document.getElementById('bizType').value,
    monthly_revenue:  parseFloat(document.getElementById('monthlyRevenue').value) || 0,
    downtime_minutes: parseFloat(document.getElementById('downtimeMins').value) || 0,
    users_affected:   parseInt(document.getElementById('usersAffected').value) || 0,
    engineers:        parseFloat(document.getElementById('engineers').value) || 0,
    hours_spent:      parseFloat(document.getElementById('hoursSpent').value) || 0,
    engineer_cost_hr: parseFloat(document.getElementById('engineerCost').value) || 0,
    sla_penalty_hr:   parseFloat(document.getElementById('slaPenalty').value) || 0,
    customer_ltv:     parseFloat(document.getElementById('customerLtv').value) || 0,
    churn_pct:        parseFloat(document.getElementById('churnPct').value) || 0,
    support_tickets:  parseInt(document.getElementById('supportTickets').value) || 0,
    cost_per_ticket:  parseFloat(document.getElementById('costPerTicket').value) || 0,
    refunds:          parseFloat(document.getElementById('refunds').value) || 0,
  }};
  const response = await fetch('/cost/incident', {{
    method: 'POST', headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify(payload)
  }});
  const data = await response.json();
  const b    = data.breakdown || {{}};
  const el   = document.getElementById('incidentCostResult');
  el.style.display = 'block';
  el.innerHTML = `
    <div style="background:#0d0d0d;border-radius:8px;padding:14px;border:1px solid #2a2a2a">
      <div style="font-size:11px;font-weight:600;color:#666;margin-bottom:10px;text-transform:uppercase;letter-spacing:.05em">Cost breakdown</div>
      ${{b.revenue_lost     ? `<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #1f1f1f"><span style="color:#888">Revenue lost</span><span style="color:#E24B4A">₹${{b.revenue_lost.toLocaleString()}}</span></div>` : ''}}
      ${{b.engineering_cost ? `<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #1f1f1f"><span style="color:#888">Engineering cost</span><span style="color:#EF9F27">₹${{b.engineering_cost.toLocaleString()}}</span></div>` : ''}}
      ${{b.sla_penalty      ? `<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #1f1f1f"><span style="color:#888">SLA penalty</span><span style="color:#EF9F27">₹${{b.sla_penalty.toLocaleString()}}</span></div>` : ''}}
      ${{b.churn_cost       ? `<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #1f1f1f"><span style="color:#888">Churn risk${{data.churn_estimated ? ' (estimated)' : ''}}</span><span style="color:#EF9F27">₹${{b.churn_cost.toLocaleString()}}</span></div>` : ''}}
      ${{b.support_cost     ? `<div style="display:flex;justify-content:space-between;padding:5px 0;border-bottom:1px solid #1f1f1f"><span style="color:#888">Support cost</span><span style="color:#EF9F27">₹${{b.support_cost.toLocaleString()}}</span></div>` : ''}}
      <div style="display:flex;justify-content:space-between;padding:8px 0;margin-top:4px">
        <span style="color:#fff;font-weight:600">Total incident cost</span>
        <span style="color:#1D9E75;font-weight:700;font-size:16px">₹${{data.total_cost.toLocaleString()}}</span>
      </div>
      <div style="font-size:12px;color:#666;margin-top:6px">${{data.summary}}</div>
    </div>`;
}}

async function handlePdfUpload(input) {{
  const file = input.files[0];
  if (!file) return;
  document.getElementById('pdfStatus').textContent = 'Reading PDF...';
  const formData = new FormData();
  formData.append('file', file);
  try {{
    const response = await fetch('/cost/optimize-pdf', {{ method: 'POST', body: formData }});
    const data = await response.json();
    if (data.error) {{ document.getElementById('pdfStatus').textContent = 'Error: ' + data.error; return; }}
    document.getElementById('pdfStatus').textContent = 'PDF read — showing results below';
    showCostResults(data);
  }} catch(e) {{ document.getElementById('pdfStatus').textContent = 'Error: ' + e.message; }}
}}

async function optimizeCosts() {{
  const costData = document.getElementById('costData').value.trim();
  if (!costData) {{ alert('Please paste your cloud cost data first'); return; }}
  const btn = document.querySelector('#tab-cost .section:last-child .btn');
  btn.textContent = 'Analyzing...'; btn.disabled = true;
  const response = await fetch('/cost/optimize', {{
    method: 'POST', headers: {{'Content-Type': 'application/json'}},
    body: JSON.stringify({{cost_data: costData}})
  }});
  const data = await response.json();
  if (data.error) {{ alert('Error: ' + data.error); btn.textContent = 'Optimize costs'; btn.disabled = false; return; }}
  showCostResults(data);
  btn.textContent = 'Optimize costs'; btn.disabled = false;
}}

function showCostResults(data) {{
  const recs = (data.top_recommendations || []).map(r =>
    `<div style="padding:10px 0;border-bottom:1px solid #2a2a2a">
      <span style="color:#7b8cde;font-weight:600">${{r.service}}</span>
      <span style="color:#666;font-size:12px;margin-left:8px">${{r.difficulty}} fix</span><br>
      <span style="color:#ccc">${{r.recommended_action}}</span><br>
      <span style="color:#1D9E75">Save: ${{r.estimated_saving}}/month</span>
    </div>`
  ).join('');
  const quickWins = (data.quick_wins || []).map((w,i) => `${{i+1}}. ${{w}}`).join('<br>');
  document.getElementById('costOptBody').innerHTML = `
    <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:10px;margin-bottom:14px">
      <div style="background:#0d0d0d;border-radius:8px;padding:12px;border:1px solid #2a2a2a"><div style="font-size:11px;color:#666">Monthly spend</div><div style="font-size:18px;font-weight:700;color:#fff">${{data.total_monthly_spend}}</div></div>
      <div style="background:#0d0d0d;border-radius:8px;padding:12px;border:1px solid #2a2a2a"><div style="font-size:11px;color:#666">Potential savings</div><div style="font-size:18px;font-weight:700;color:#1D9E75">${{data.potential_savings}}</div></div>
      <div style="background:#0d0d0d;border-radius:8px;padding:12px;border:1px solid #2a2a2a"><div style="font-size:11px;color:#666">Savings %</div><div style="font-size:18px;font-weight:700;color:#EF9F27">${{data.savings_percentage}}</div></div>
    </div>
    <div style="margin-bottom:12px;color:#ccc">${{data.summary}}</div>
    <div style="font-size:12px;font-weight:600;color:#aaa;margin-bottom:8px">Top recommendations</div>
    ${{recs}}
    <div style="font-size:12px;font-weight:600;color:#aaa;margin:14px 0 8px">Quick wins</div>
    <div style="color:#ccc;line-height:1.8">${{quickWins}}</div>`;
  document.getElementById('costOptResult').style.display = 'block';
}}


  let chatHistory = [];

function askSuggested(btn) {{
  document.getElementById('chatInput').value = btn.textContent;
  sendChat();
}}

async function sendChat() {{
  const input    = document.getElementById('chatInput');
  const question = input.value.trim();
  if (!question) return;
  input.value = '';

  const chatBox = document.getElementById('chatBox');
  chatBox.innerHTML += `<div class="chat-msg chat-user">${{question}}</div>`;
  const typingId = 'typing-' + Date.now();
  chatBox.innerHTML += `<div class="chat-msg chat-ai" id="${{typingId}}">Thinking...</div>`;
  chatBox.scrollTop = chatBox.scrollHeight;

  chatHistory.push({{"role": "user", "content": question}});

  try {{
    const response = await fetch('/chat', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{
        question: question,
        history:  chatHistory.slice(-6)
      }})
    }});
    const data   = await response.json();
    const answer = data.answer || 'Sorry, I could not answer that.';
    document.getElementById(typingId).textContent = answer;
    document.getElementById(typingId).removeAttribute('id');
    chatHistory.push({{"role": "assistant", "content": answer}});
  }} catch(e) {{
    document.getElementById(typingId).textContent = 'Error: ' + e.message;
    document.getElementById(typingId).removeAttribute('id');
  }}

  chatBox.scrollTop = chatBox.scrollHeight;
}}
</script>
</body>
</html>"""
    return HTMLResponse(content=html)