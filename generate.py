#!/usr/bin/env python3
"""Generate a professional Gantt chart (standalone SVG + interactive HTML) from the project plan."""

import datetime as dt
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

START = dt.date(2026, 9, 13)
DEADLINE = dt.date(2026, 12, 19)
TOTAL_DAYS = (DEADLINE - START).days + 1
WEEKS = TOTAL_DAYS // 7
if TOTAL_DAYS % 7:
    raise SystemExit("project span must be a whole number of weeks")

PROJECT = "Project Implementation Plan (Gantt Chart)"
SUBTITLE = (
    "13 September \u2013 19 December 2026 \u00b7 14-week semester, 10-week task plan \u00b7 "
    "Critical path T1 \u2192 T2 \u2192 T3 \u2192 T5 \u2192 T6 \u2192 T7 \u2192 T8"
)

TASKS = [
    dict(id="T1", name="Project Initiation & Scope Definition", start=0, end=7, phase="init", deps=[]),
    dict(id="T2", name="Conduct Literature Review", start=7, end=21, phase="res", deps=["T1"]),
    dict(id="T3", name="Requirements Analysis", start=21, end=28, phase="res", deps=["T2"]),
    dict(id="T4", name="Draft Report: Introduction & Literature Review", start=21, end=35, phase="doc", deps=["T2"]),
    dict(id="T5", name="System Design (Architecture & DFDs)", start=28, end=42, phase="des", deps=["T3"]),
    dict(id="T6", name="Draft Report: Methodology & Design", start=42, end=56, phase="doc", deps=["T5"]),
    dict(id="T7", name="Final Report Compilation & Plagiarism Check", start=56, end=63, phase="doc", deps=["T4", "T6"]),
    dict(id="T8", name="Oral Presentation Preparation", start=63, end=70, phase="pre", deps=["T7"]),
]

PHASES = {
    "init": ("Initiation", "#334155", "#cbd5e1", "#1e293b"),
    "res": ("Research", "#1d4ed8", "#bfdbfe", "#1e40af"),
    "des": ("Design", "#0f766e", "#99f6e4", "#115e59"),
    "doc": ("Documentation", "#b45309", "#fde68a", "#92400e"),
    "pre": ("Presentation", "#6d28d9", "#ddd6fe", "#5b21b6"),
}

PAD = 26
LEFT_W = 284
ID_W = 46
DUR_W = 44
WEEK_W = 72
PLOT_X = PAD + LEFT_W
PLOT_W = WEEKS * WEEK_W
WIDTH = PLOT_X + PLOT_W + PAD + 4
TITLE_Y = 40
SUBTITLE_Y = 64
LEGEND_BASE = 100
AXIS_TOP = 118
AXIS_H = 54
PLOT_TOP = AXIS_TOP + AXIS_H
ROW_H = 42
BAR_H = 24
BAR_OFF = (ROW_H - BAR_H) // 2
ROWS_BOTTOM = PLOT_TOP + len(TASKS) * ROW_H
HEIGHT = ROWS_BOTTOM + 42

FONT = "Segoe UI, Helvetica Neue, Arial, sans-serif"
INK = "#0f172a"
MUTED = "#64748b"
FAINT = "#94a3b8"
GRID = "#e6ebf1"
PANEL = "#f8fafc"

SVG_CSS = """
text{font-family:%s}
.dep{fill:none;stroke:#8b98a9;stroke-width:1.5}
.bar{cursor:pointer}
.bar .lbl{font-size:11.5px;font-weight:700}
.bar .dur{font-size:10px}
.bar:hover .b{stroke:#0f172a !important;stroke-width:2.2 !important}
.bar:hover .lbl{font-weight:800}
.p-init.crit .b{fill:#334155;stroke:#1e293b;stroke-width:1}
.p-res.crit .b{fill:#1d4ed8;stroke:#1e40af;stroke-width:1}
.p-des.crit .b{fill:#0f766e;stroke:#115e59;stroke-width:1}
.p-doc.crit .b{fill:#b45309;stroke:#92400e;stroke-width:1}
.p-pre.crit .b{fill:#6d28d9;stroke:#5b21b6;stroke-width:1}
.p-init.slack .b{fill:#cbd5e1;stroke:#334155;stroke-width:1.2;stroke-dasharray:5 3}
.p-res.slack .b{fill:#bfdbfe;stroke:#1d4ed8;stroke-width:1.2;stroke-dasharray:5 3}
.p-des.slack .b{fill:#99f6e4;stroke:#0f766e;stroke-width:1.2;stroke-dasharray:5 3}
.p-doc.slack .b{fill:#fde68a;stroke:#b45309;stroke-width:1.2;stroke-dasharray:5 3}
.p-pre.slack .b{fill:#ddd6fe;stroke:#6d28d9;stroke-width:1.2;stroke-dasharray:5 3}
.crit .lbl{fill:#ffffff}
.slack .lbl{fill:#0f172a}
.crit .dur{fill:#e8edf5}
.slack .dur{fill:#475569}
.rowband:hover{fill:#eef2f7}
""" % FONT


def n(v):
    v = round(float(v), 1)
    return str(int(v)) if v == int(v) else str(v)


def x_of(day):
    return PLOT_X + day * WEEK_W / 7.0


def row_y(i):
    return PLOT_TOP + i * ROW_H


def date_of(day):
    return START + dt.timedelta(days=day)


def esc(s):
    return escape(str(s))


def esc_attr(s):
    return escape(str(s), {'"': "&quot;"})


def R(x, y, w, h, fill="none", stroke="none", rx=None, cls=None, extra=""):
    rx_a = f' rx="{n(rx)}"' if rx else ""
    cls_a = f' class="{cls}"' if cls else ""
    return (
        f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" '
        f'fill="{fill}" stroke="{stroke}"{rx_a}{cls_a}{extra}/>'
    )


def T(x, y, s, size=11, fill=INK, weight="400", anchor="start", cls=None, italic=False, extra=""):
    cls_a = f' class="{cls}"' if cls else ""
    it_a = ' font-style="italic"' if italic else ""
    return (
        f'<text x="{n(x)}" y="{n(y)}" font-size="{size}" fill="{fill}" '
        f'font-weight="{weight}" text-anchor="{anchor}"{cls_a}{it_a}{extra}>{esc(s)}</text>'
    )


def L(x1, y1, x2, y2, stroke=GRID, width=1, dash=None, marker=None, cls=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    m = f' marker-end="url(#{marker})"' if marker else ""
    c = f' class="{cls}"' if cls else ""
    return (
        f'<line x1="{n(x1)}" y1="{n(y1)}" x2="{n(x2)}" y2="{n(y2)}" '
        f'stroke="{stroke}" stroke-width="{n(width)}"{d}{m}{c}/>'
    )


def run_cpm(tasks):
    by_id = {t["id"]: t for t in tasks}
    for t in tasks:
        for d in t["deps"]:
            if d not in by_id:
                raise ValueError(f"{t['id']}: unknown dependency {d}")
            if by_id[d]["end"] > t["start"]:
                raise ValueError(f"{t['id']}: starts before {d} finishes")
        if t["end"] <= t["start"]:
            raise ValueError(f"{t['id']}: non-positive duration")
        if not (0 <= t["start"] and t["end"] <= TOTAL_DAYS):
            raise ValueError(f"{t['id']}: outside project span")
        if t["start"] % 7 or t["end"] % 7:
            raise ValueError(f"{t['id']}: not week-aligned")

    succ = {t["id"]: [] for t in tasks}
    for t in tasks:
        for d in t["deps"]:
            succ[d].append(t["id"])

    finish = max(t["end"] for t in tasks)
    ef = {}
    for t in tasks:
        es = max((ef[d] for d in t["deps"]), default=0)
        ef[t["id"]] = t["end"]
        t["es"] = es

    lf = {}
    for t in reversed(tasks):
        latest = min((lf[s] for s in succ[t["id"]]), default=finish)
        ls = latest - (t["end"] - t["start"])
        lf[t["id"]] = ls
        t["float"] = ls - t["es"]
        t["critical"] = t["float"] == 0

    crit = {t["id"] for t in tasks if t["critical"]}
    expected = {"T1", "T2", "T3", "T5", "T6", "T7", "T8"}
    if crit != expected:
        raise ValueError(f"critical path mismatch: {sorted(crit)}")
    if by_id["T4"]["float"] != 21:
        raise ValueError("T4 float changed unexpectedly")
    if finish != 70:
        raise ValueError("plan no longer finishes at week 10")
    return succ


def wrap_name(name, width=35):
    lines, cur = [], ""
    for word in name.split():
        cand = (cur + " " + word).strip()
        if len(cand) <= width:
            cur = cand
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    if len(lines) > 2:
        lines = lines[:2]
        lines[1] = lines[1][: width - 1] + "\u2026"
    return lines


def week_span(t):
    a = t["start"] // 7 + 1
    b = (t["end"] - 1) // 7 + 1
    return f"W{a}" if a == b else f"W{a}\u2013W{b}"


def fmt_span(t):
    a = date_of(t["start"])
    b = date_of(t["end"] - 1)
    return f"{a:%a %-d %b} \u2013 {b:%a %-d %b %Y}"


def tip_html(t):
    deps = ", ".join(t["deps"]) if t["deps"] else "None"
    status = "On the critical path" if t["critical"] else f"Float: {t['float'] // 7} weeks ({t['float']} days)"
    body = (
        f"<b>{t['id']} \u2014 {t['name']}</b><br>"
        f"{fmt_span(t)} \u00b7 {t['end'] - t['start']} days ({week_span(t)})<br>"
        f"Phase: {PHASES[t['phase']][0]} \u00b7 Depends on: {deps}<br>{status}"
    )
    return esc_attr(body)


def build_svg():
    succ = run_cpm(TASKS)
    by_id = {t["id"]: t for t in TASKS}
    idx = {t["id"]: i for i, t in enumerate(TASKS)}
    plot_right = PLOT_X + PLOT_W

    def bar_y(t):
        return row_y(idx[t["id"]]) + BAR_OFF

    def bar_right(t):
        return x_of(t["end"]) - 3

    p = []
    p.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
             f'viewBox="0 0 {WIDTH} {HEIGHT}" role="img" aria-label="{esc_attr(PROJECT)}">')
    p.append(f"<defs><style>{SVG_CSS}</style>")
    p.append(
        '<marker id="ah" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        'orient="auto" markerUnits="userSpaceOnUse"><path d="M0 0 L10 5 L0 10 z" fill="#8b98a9"/></marker>'
    )
    p.append("</defs>")
    p.append(R(0, 0, WIDTH, HEIGHT, fill="#ffffff"))

    p.append(T(PAD, TITLE_Y, PROJECT, size=20, weight="700"))
    p.append(T(PAD, SUBTITLE_Y, SUBTITLE, size=11, fill="#475569"))

    lx = PAD
    ly = LEGEND_BASE
    p.append(T(lx, ly, "Phases:", size=10, fill=MUTED, weight="600"))
    lx += 46
    for key, (label, fill, tint, stroke) in PHASES.items():
        p.append(R(lx, ly - 10, 14, 12, fill=fill, rx=2))
        lx += 19
        p.append(T(lx, ly, label, size=10.5, fill="#334155"))
        lx += len(label) * 5.5 + 16
    lx += 6
    p.append(L(lx, ly - 9, lx, ly + 3, stroke="#cbd5e1", width=1))
    lx += 16
    p.append(R(lx, ly - 10, 26, 12, fill="#1d4ed8", stroke="#1e40af", rx=3))
    p.append(T(lx + 32, ly, "Critical path", size=10.5, fill="#334155"))
    lx += 32 + len("Critical path") * 5.5 + 16
    p.append(R(lx, ly - 10, 26, 12, fill="#fde68a", stroke="#b45309", rx=3))
    p.append('<rect x="%s" y="%s" width="26" height="12" fill="none" stroke="#b45309" '
             'stroke-width="1.2" stroke-dasharray="5 3" rx="3"/>' % (n(lx), n(ly - 10)))
    p.append(T(lx + 32, ly, "Has float", size=10.5, fill="#334155"))
    lx += 32 + len("Has float") * 5.5 + 16
    p.append(L(lx, ly - 4, lx + 24, ly - 4, stroke="#8b98a9", width=1.5, marker="ah"))
    p.append(T(lx + 32, ly, "Dependency", size=10.5, fill="#334155"))
    lx += 32 + len("Dependency") * 5.5 + 16
    p.append(L(lx, ly - 10, lx, ly + 3, stroke="#dc2626", width=1.6, dash="5 4"))
    p.append(T(lx + 10, ly, "Final deadline", size=10.5, fill="#334155"))

    for i, t in enumerate(TASKS):
        if i % 2:
            p.append(R(PAD, row_y(i), plot_right - PAD, ROW_H, fill=PANEL, cls="rowband"))

    p.append(R(PLOT_X, AXIS_TOP, PLOT_W, AXIS_H, fill=PANEL))
    for w in range(WEEKS + 1):
        gx = PLOT_X + w * WEEK_W
        p.append(L(gx, PLOT_TOP, gx, ROWS_BOTTOM, stroke=GRID, width=1))
    p.append(L(PAD, PLOT_TOP, plot_right, PLOT_TOP, stroke="#cbd5e1", width=1))
    p.append(L(PAD, ROWS_BOTTOM, plot_right, ROWS_BOTTOM, stroke="#cbd5e1", width=1))
    p.append(L(PLOT_X, AXIS_TOP, PLOT_X, ROWS_BOTTOM, stroke="#cbd5e1", width=1))

    for w in range(WEEKS):
        wx = PLOT_X + w * WEEK_W
        buffer = w + 1 > 10
        col = FAINT if buffer else INK
        dcol = FAINT if buffer else MUTED
        p.append(T(wx + 8, AXIS_TOP + 21, f"W{w + 1}", size=12 if not buffer else 11, fill=col, weight="700"))
        p.append(T(wx + 8, AXIS_TOP + 37, date_of(w * 7).strftime("%b %-d"), size=9, fill=dcol))

    buffer_x = x_of(70)
    p.append(R(buffer_x, PLOT_TOP, plot_right - buffer_x, ROWS_BOTTOM - PLOT_TOP, fill="#eef2f7"))
    p.append(L(buffer_x, PLOT_TOP, buffer_x, ROWS_BOTTOM, stroke="#cbd5e1", width=1, dash="4 3"))
    deadline_x = x_of(TOTAL_DAYS)
    p.append(L(deadline_x, AXIS_TOP, deadline_x, ROWS_BOTTOM, stroke="#dc2626", width=1.6, dash="5 4"))
    p.append(T(deadline_x - 8, PLOT_TOP + 15, "Final deadline \u2014 Sat 19 Dec 2026", size=10, fill="#b91c1c", weight="600", anchor="end"))
    p.append(T(x_of(84), ROWS_BOTTOM - 10, "Buffer / reserve \u2014 4 weeks (W11\u2013W14)", size=10, fill=FAINT, anchor="middle", italic=True))

    for pred_id, succs in succ.items():
        pred = by_id[pred_id]
        for k, sid in enumerate(succs):
            t = by_id[sid]
            ax = bar_right(pred)
            ay = bar_y(pred) + BAR_H // 2
            x_start = x_of(t["start"])
            gap = x_start - ax
            if gap < 34:
                off = 14 + 10 * k
                path = f"M{n(ax)} {n(ay)} H{n(ax + off)} V{n(bar_y(t) - 1)}"
            else:
                path = (f"M{n(ax)} {n(ay)} H{n(x_start - 10)} V{n(bar_y(t) + BAR_H // 2)} "
                        f"H{n(x_start - 1)}")
            p.append(f'<path class="dep" d="{path}" marker-end="url(#ah)"/>')

    for t in TASKS:
        phase = t["phase"]
        status = "crit" if t["critical"] else "slack"
        by = bar_y(t)
        bx = x_of(t["start"])
        bw = (t["end"] - t["start"]) * WEEK_W / 7 - 3
        p.append(
            f'<g class="bar p-{phase} {status}" data-task="{t["id"]}" data-tip="{tip_html(t)}">'
            f'{R(bx, by, bw, BAR_H, rx=4, cls="b")}'
            f'{T(bx + 10, by + 16, t["id"], cls="lbl")}'
            f'{T(bx + bw - 8, by + 16, f"{(t["end"] - t["start"]) // 7}w", cls="dur", anchor="end")}'
            f"</g>"
        )
        if not t["critical"]:
            next_start = min(by_id[s]["start"] for s in succ[t["id"]])
            fx = x_of(t["end"])
            fw = x_of(next_start) - fx
            p.append('<rect x="%s" y="%s" width="%s" height="5" fill="#e2e8f0" stroke="%s" '
                     'stroke-width="1" stroke-dasharray="4 3" rx="2.5"/>' % (n(fx), n(by + BAR_H + 3), n(fw), FAINT))
            p.append(T(fx + fw + 8, by + BAR_H + 7, f"{t['float'] // 7}w float", size=9.5, fill=FAINT, italic=True))

    p.append(T(PAD + 6, AXIS_TOP + 21, "ID", size=10, fill=MUTED, weight="600"))
    p.append(T(PAD + ID_W, AXIS_TOP + 21, "Task", size=10, fill=MUTED, weight="600"))
    p.append(T(PLOT_X - 10, AXIS_TOP + 21, "Dur.", size=10, fill=MUTED, weight="600", anchor="end"))
    for i, t in enumerate(TASKS):
        ry = row_y(i)
        lines = wrap_name(t["name"])
        p.append(T(PAD + 6, ry + 26, t["id"], size=11.5, weight="700"))
        if len(lines) == 1:
            p.append(T(PAD + ID_W, ry + 26, lines[0], size=10.5, fill="#334155"))
        else:
            p.append(T(PAD + ID_W, ry + 18, lines[0], size=10.5, fill="#334155"))
            p.append(T(PAD + ID_W, ry + 32, lines[1], size=10.5, fill="#334155"))
        p.append(T(PLOT_X - 10, ry + 26, f"{(t['end'] - t['start']) // 7}w", size=10.5, fill=MUTED, anchor="end"))

    p.append(T(PAD, HEIGHT - 14, "Weeks run Sunday\u2013Saturday \u00b7 buffer weeks W11\u2013W14 held before the final deadline (19 Dec 2026).", size=9.5, fill=FAINT))
    p.append(T(plot_right, HEIGHT - 14, "Figure generated from the project schedule table.", size=9.5, fill=FAINT, anchor="end"))
    p.append("</svg>")
    return "\n".join(p)


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Project Implementation Plan (Gantt Chart)</title>
<style>
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  body { margin: 0; background: #eef1f5; color: #0f172a;
         font-family: "Segoe UI", "Helvetica Neue", Arial, sans-serif; }
  .wrap { max-width: 1400px; margin: 24px auto 40px; padding: 0 20px; }
  .toolbar { display: flex; justify-content: flex-end; gap: 8px; margin-bottom: 12px; }
  .toolbar button { font: 600 13px/1 inherit; padding: 10px 16px; border-radius: 8px;
                    border: 1px solid #cbd5e1; background: #fff; color: #0f172a; cursor: pointer; }
  .toolbar button:hover { background: #f1f5f9; }
  .toolbar button.primary { background: #1d4ed8; border-color: #1d4ed8; color: #fff; }
  .toolbar button.primary:hover { background: #1e40af; }
  .card { background: #fff; border: 1px solid #e2e8f0; border-radius: 12px;
          box-shadow: 0 10px 30px rgba(15, 23, 42, .08); padding: 10px; }
  .card svg { display: block; width: 100%; height: auto; }
  #tip { position: fixed; left: 0; top: 0; z-index: 50; pointer-events: none;
         background: #0f172a; color: #e2e8f0; padding: 10px 12px; border-radius: 8px;
         font-size: 12px; line-height: 1.55; max-width: 360px;
         box-shadow: 0 12px 24px rgba(15, 23, 42, .28); opacity: 0; transition: opacity .1s; }
  #tip.on { opacity: 1; }
  #tip b { color: #fff; }
  @media print {
    @page { size: A4 landscape; margin: 8mm; }
    body { background: #fff; }
    .toolbar, #tip { display: none; }
    .wrap { margin: 0; max-width: none; padding: 0; }
    .card { border: 0; box-shadow: none; padding: 0; }
  }
</style>
</head>
<body>
<div class="wrap">
  <div class="toolbar">
    <button id="print">Print / Save as PDF</button>
    <button id="png" class="primary">Download PNG</button>
  </div>
  <div class="card">__SVG__</div>
</div>
<div id="tip"></div>
<script>
(function () {
  var svg = document.querySelector('.card svg');
  var tip = document.getElementById('tip');
  document.querySelectorAll('.bar').forEach(function (g) {
    g.addEventListener('mouseenter', function () {
      tip.innerHTML = g.getAttribute('data-tip');
      tip.classList.add('on');
    });
    g.addEventListener('mousemove', function (e) {
      var r = tip.getBoundingClientRect();
      var x = e.clientX + 16, y = e.clientY + 16;
      if (x + r.width > window.innerWidth - 8) x = e.clientX - r.width - 16;
      if (y + r.height > window.innerHeight - 8) y = e.clientY - r.height - 16;
      tip.style.left = x + 'px';
      tip.style.top = y + 'px';
    });
    g.addEventListener('mouseleave', function () { tip.classList.remove('on'); });
  });
  document.getElementById('print').addEventListener('click', function () { window.print(); });
  document.getElementById('png').addEventListener('click', function () {
    var w = +svg.getAttribute('width'), h = +svg.getAttribute('height'), s = 2;
    var xml = new XMLSerializer().serializeToString(svg);
    var url = URL.createObjectURL(new Blob([xml], { type: 'image/svg+xml;charset=utf-8' }));
    var img = new Image();
    img.onload = function () {
      var c = document.createElement('canvas');
      c.width = w * s; c.height = h * s;
      var ctx = c.getContext('2d');
      ctx.fillStyle = '#ffffff';
      ctx.fillRect(0, 0, c.width, c.height);
      ctx.drawImage(img, 0, 0, c.width, c.height);
      URL.revokeObjectURL(url);
      var a = document.createElement('a');
      a.download = 'gantt.png';
      a.href = c.toDataURL('image/png');
      a.click();
    };
    img.src = url;
  });
})();
</script>
</body>
</html>
"""


def main():
    svg = build_svg()
    Path("gantt.svg").write_text(svg, encoding="utf-8")
    page = HTML.replace("__SVG__", svg)
    Path("gantt.html").write_text(page, encoding="utf-8")
    Path("index.html").write_text(page, encoding="utf-8")
    ET.fromstring(svg)
    try:
        import subprocess

        subprocess.run(["rsvg-convert", "-z", "2", "gantt.svg", "-o", "gantt.png"], check=True)
        print("wrote gantt.png (2x, via rsvg-convert)")
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("rsvg-convert not found \u2014 use the Download PNG button in gantt.html instead")
    print(f"wrote gantt.svg and gantt.html \u00b7 {WEEKS} weeks, {len(TASKS)} tasks, "
          f"critical path ends {date_of(70 - 1):%a %-d %b %Y}")
    for t in TASKS:
        a, b = date_of(t["start"]), date_of(t["end"] - 1)
        flag = "critical" if t["critical"] else f"float {t['float'] // 7}w"
        print(f"  {t['id']}  {a:%a %-d %b} \u2013 {b:%a %-d %b}  {(t['end'] - t['start']) // 7}w  "
              f"{flag:10}  {t['name']}")


if __name__ == "__main__":
    main()
