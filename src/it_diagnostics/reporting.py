"""Offline HTML and machine-readable JSON. All dynamic HTML content is escaped."""

import html
import json
import os
import tempfile
from pathlib import Path
from uuid import uuid4

from .models import Report, STATUSES

CSS = """
:root{color-scheme:light;--ink:#17313c;--muted:#516670;--line:#dce5e8;--bg:#f3f7f8}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.55 system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:1120px;margin:auto;padding:42px 30px 30px}.eyebrow{font-size:12px;letter-spacing:.16em;font-weight:750;text-transform:uppercase}
header{display:flex;justify-content:space-between;gap:24px;border-bottom:1px solid var(--line);padding-bottom:26px}
h1{font-size:40px;line-height:1.12;letter-spacing:-.04em;margin:12px 0}h2{font-size:21px;margin:0 0 8px}h3{font-size:16px;margin:0}
p{margin:6px 0}.muted{color:var(--muted)}.badge{display:inline-block;font-size:12px;letter-spacing:.03em;font-weight:800;border-radius:6px;padding:5px 10px;white-space:nowrap}
.OK{background:#e1f1ea;color:#176748}.WARNING{background:#fff0ce;color:#835503}.FAIL{background:#fbe6e4;color:#a33229}.SKIP{background:#e8eef1;color:#4d626d}
.hero-status{text-align:right;min-width:160px;padding-top:5px}.hero-status .badge{font-size:15px}.notice{padding:12px 16px;background:#e5eef8;border:1px solid #c9dbed;border-radius:8px;margin:24px 0 0}
.counts{display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin:24px 0}.count{background:white;border:1px solid var(--line);border-radius:10px;padding:16px 20px}.number{font-size:32px;font-weight:750;line-height:1.2;margin-bottom:8px}
.layout{display:grid;grid-template-columns:minmax(0,1fr) 265px;gap:24px;align-items:start}.panel{background:white;border:1px solid var(--line);border-radius:10px;padding:20px}
.check{border:1px solid var(--line);border-radius:10px;background:white;padding:18px 20px;margin:12px 0}.check-head{display:flex;justify-content:space-between;align-items:start;gap:15px}.category{font-size:11px;text-transform:uppercase;letter-spacing:.1em;color:var(--muted);margin-bottom:4px}
.recommendation{margin-top:12px;padding-top:11px;border-top:1px solid #edf1f2;font-size:14px}.recommendation strong{display:block;font-size:11px;letter-spacing:.07em;text-transform:uppercase;color:#52646e;margin-bottom:4px}
details{margin-top:12px;font-size:13px}summary{cursor:pointer;color:#246777;font-weight:650}pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f7f8;padding:12px;border-radius:6px;font-size:12px}
dl{margin:14px 0 0}dt{color:var(--muted);font-size:12px;margin-top:12px}dd{margin:2px 0 0;font-weight:600;overflow-wrap:anywhere}.filters{display:flex;gap:7px;flex-wrap:wrap;margin:14px 0}
button{cursor:pointer;border:1px solid #cbd8dc;background:white;color:var(--ink);padding:6px 12px;border-radius:20px;font:inherit;font-size:12px}button[aria-pressed=true]{background:var(--ink);color:white;border-color:var(--ink)}button:focus-visible{outline:3px solid #4099ab;outline-offset:2px}
footer{margin-top:26px;padding-top:18px;border-top:1px solid var(--line);font-size:12px;color:var(--muted)}[hidden]{display:none!important}
@media(max-width:760px){main{padding:22px 16px}.layout{grid-template-columns:1fr}.counts{grid-template-columns:repeat(2,1fr)}h1{font-size:30px}header{display:block}.hero-status{text-align:left;margin-top:16px}aside{order:-1}}
@media print{body{background:white}main{padding:0}.filters{display:none}.layout{display:block}.check{break-inside:avoid}aside{margin-top:20px}.check[hidden]{display:block!important}}
"""


def render_html(report: Report) -> str:
    esc = lambda value: html.escape(str(value), quote=True)
    cards = "".join(f'<div class="count"><div class="number">{report.counts[s]}</div>'
                    f'<span class="badge {s}">{s}</span></div>' for s in STATUSES)
    priority = {"FAIL": 0, "WARNING": 1, "OK": 2, "SKIP": 3}
    checks = []
    for check in sorted(report.checks, key=lambda c: priority[c.status]):
        evidence = esc(json.dumps(check.evidence, indent=2, ensure_ascii=False))
        checks.append(f'''<article class="check" data-status="{check.status}">
<div class="check-head"><div><div class="category">{esc(check.category)}</div><h3>{esc(check.title)}</h3></div>
<span class="badge {check.status}">{check.status}</span></div><p>{esc(check.summary)}</p>
<div class="recommendation"><strong>Next step</strong>{esc(check.recommendation)}</div>
<details><summary>Technical evidence</summary><pre>{evidence}</pre></details></article>''')
    inventory = "".join(f'<dt>{esc(k.replace("_", " ").capitalize())}</dt><dd>{esc("Unavailable" if v is None else v)}</dd>'
                        for k, v in report.inventory.items())
    notice = ('<div class="notice"><strong>DEMO / SYNTHETIC DATA</strong> &nbsp; '
              'Fictional scenario. No measurements or network requests were made.</div>' if report.mode.startswith("demo:") else "")
    if report.counts["SKIP"]:
        notice += ('<div class="notice"><strong>PARTIAL COVERAGE</strong> &nbsp; '
                   'Some checks were skipped. The overall result reflects completed checks only.</div>')
    buttons = "".join(f'<button type="button" data-filter="{s}" aria-pressed="{str(s == "ALL").lower()}">{s}</button>'
                      for s in ("ALL", *STATUSES))
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>IT Diagnostics | {esc(report.overall_status)}</title><style>{CSS}</style></head><body><main>
<header><div><div class="eyebrow">IT Diagnostics Toolkit / v{esc(report.tool_version)}</div>
<h1>System health snapshot</h1><p class="muted">Evidence, findings and practical next steps for IT support.</p></div>
<div class="hero-status"><div class="eyebrow">Overall result</div><p><span class="badge {report.overall_status}">{report.overall_status}</span></p>
<p class="muted">{len(report.checks)} checks recorded</p></div></header>{notice}
<section class="counts" aria-label="Check totals">{cards}</section>
<div class="layout"><section><h2>Diagnostic findings</h2><p class="muted">Failures and warnings appear first. SKIP means unverified.</p>
<nav class="filters" aria-label="Filter findings">{buttons}</nav><div id="findings">{''.join(checks)}</div>
<p id="empty" class="muted" hidden>No findings match this filter.</p></section>
<aside class="panel"><h2>System context</h2><dl><dt>Report time (UTC)</dt><dd>{esc(report.generated_at)}</dd>
<dt>Mode</dt><dd>{esc(report.mode)}</dd>{inventory}</dl></aside></div>
<footer>Read-only diagnostics: no settings changed, services restarted or files deleted. Only report files are written.
An OK result applies only to completed checks; it is not a hardware certification or a guarantee of application health.
Review live reports before sharing: configured paths, destinations and service names may be sensitive.</footer>
</main><script>
document.querySelectorAll('[data-filter]').forEach(button => button.addEventListener('click', () => {{
 const filter = button.dataset.filter;
 document.querySelectorAll('[data-filter]').forEach(b => b.setAttribute('aria-pressed', String(b === button)));
 let visible = 0;
 document.querySelectorAll('[data-status]').forEach(card => {{
   card.hidden = filter !== 'ALL' && card.dataset.status !== filter;
   if (!card.hidden) visible++;
 }});
 document.getElementById('empty').hidden = visible > 0;
}}));
</script></body></html>'''


def write_reports(report: Report, directory: Path, output_format: str = "both") -> list[Path]:
    if output_format not in ("both", "html", "json"):
        raise ValueError("Output format must be both, html or json")
    directory.mkdir(parents=True, exist_ok=True)
    stem = f"diagnostics-{uuid4().hex[:12]}"
    formats = ("json", "html") if output_format == "both" else (output_format,)
    paths = []
    for extension in formats:
        path = directory / f"{stem}.{extension}"
        content = (json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n"
                   if extension == "json" else render_html(report))
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=directory, delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(content)
            os.replace(temporary, path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        paths.append(path)
    return paths
