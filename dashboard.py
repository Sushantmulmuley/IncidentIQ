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
</style>
</head>
<body>
<h1>IncidentIQ</h1>
<p class="sub">Real-time incident intelligence dashboard</p>
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
</body>
</html>"""
    return HTMLResponse(content=html)