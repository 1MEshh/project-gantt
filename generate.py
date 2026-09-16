#!/usr/bin/env python3
"""Generate the BioAgeVision project plan: standalone SVG figure plus an interactive page."""

import datetime as dt
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

START = dt.date(2026, 9, 13)
WEEKS = 14
TOTAL_DAYS = WEEKS * 7

TASKS = [
    dict(id="1.1", name="Define problem statement & objectives", sw=1, ew=2, phase="def", deps=[]),
    dict(id="1.2", name="Identify required resources", sw=2, ew=3, phase="def", deps=[]),
    dict(id="2.1", name="Research biological vs chronological age markers", sw=3, ew=4, phase="res", deps=["1.1"]),
    dict(id="2.2", name="Analyze CNNs, Vision Transformers & XAI", sw=4, ew=6, phase="res", deps=["1.1"]),
    dict(id="2.3", name="Critical analysis and comparison of models", sw=5, ew=7, phase="res", deps=["2.1", "2.2"]),
    dict(id="3.1", name="Define system requirements for BioAgeVision", sw=7, ew=8, phase="req", deps=["2.3"]),
    dict(id="3.2", name="Determine dataset constraints and facial imagery", sw=8, ew=9, phase="req", deps=["3.1"]),
    dict(id="4.1", name="Design deep neural network architecture", sw=9, ew=11, phase="des", deps=["3.2"]),
    dict(id="4.2", name="Design high-frequency spatial filters & XAI", sw=10, ew=12, phase="des", deps=["4.1"]),
    dict(id="5.1", name="Draft Chapter 1: Introduction", sw=3, ew=4, phase="doc", deps=["1.1", "1.2"]),
    dict(id="5.2", name="Draft Chapter 2: Literature Review", sw=5, ew=8, phase="doc", deps=["2.1", "2.2"]),
    dict(id="5.3", name="Draft Chapter 3: Methodology & Design", sw=9, ew=12, phase="doc", deps=["4.1", "4.2"]),
    dict(id="6.1", name="Group proof-reading & formatting checks", sw=13, ew=14, phase="fin", deps=["5.1", "5.2", "5.3"]),
    dict(id="6.2", name="Final Submission", sw=14, ew=14, phase="fin", deps=["6.1"]),
]

PHASES = {
    "def": ("Definition", "#1D3D5C", "#CBD8E4", "#12293D"),
    "res": ("Research & Analysis", "#1F6E9C", "#C4DEED", "#14506F"),
    "req": ("Requirements", "#2A8E88", "#C3E4E1", "#1C6661"),
    "des": ("Architecture & Design", "#6E9A38", "#DCE8C7", "#4F7026"),
    "doc": ("Documentation", "#C08A2E", "#F1E2C2", "#8F6519"),
    "fin": ("Finalization", "#8E3F6B", "#E5CEDC", "#692E4E"),
}

PROJECT = "BioAgeVision"
SUBTITLE = "Implementation plan for the 14-week semester, Sunday 13 September to Saturday 19 December 2026."

INK = "#16232E"
TEXT = "#3A4A54"
MUTED = "#5B6B77"
FAINT = "#8C9AA5"
HAIR = "#E8ECEC"
LINE = "#D9DEDF"
PANEL = "#F5F7F7"
DEADLINE = "#A32B2B"
ARCHIVO = "Archivo, 'Liberation Sans', 'Helvetica Neue', Arial, sans-serif"

PAD = 28
LEFT_W = 300
ID_W = 48
WEEK_W = 72
PLOT_X = PAD + LEFT_W
PLOT_W = WEEKS * WEEK_W
PLOT_RIGHT = PLOT_X + PLOT_W
WIDTH = PLOT_RIGHT + PAD + 4
TITLE_Y = 46
SUBTITLE_Y = 72
LEGEND1 = 104
LEGEND2 = 128
AXIS_TOP = 150
MONTH_BOTTOM = 170
WEEK_LABEL_Y = 190
DATE_LABEL_Y = 203
PLOT_TOP = 212
ROW_H = 40
BAR_H = 22
BAR_OFF = (ROW_H - BAR_H) // 2
ROWS_BOTTOM = PLOT_TOP + len(TASKS) * ROW_H
HEIGHT = ROWS_BOTTOM + 38
MONTHS = [(0, 18, "September"), (18, 49, "October"), (49, 79, "November"), (79, 98, "December")]

SVG_CSS = """
text{font-family:%s}
.dep{fill:none;stroke-linecap:square}
.clean{stroke:#7E8C97;stroke-width:1.5}
.overlap{stroke:#A9B5BD;stroke-width:1.2;stroke-dasharray:4 3}
.bar{cursor:pointer;transition:opacity .15s ease}
.dep.dim,.bar.dim{opacity:.12}
.bar .lbl{font-size:11px;font-weight:700}
.bar .dur{font-size:9.5px;font-weight:500}
.bar:hover .bx{stroke:%s;stroke-width:2}
""" % (ARCHIVO, INK)


def n(v):
    v = round(float(v), 1)
    return str(int(v)) if v == int(v) else str(v)


def x_of(day):
    return PLOT_X + day * WEEK_W / 7.0


def date_of(day):
    return START + dt.timedelta(days=day)


def esc(s):
    return escape(str(s))


def esc_attr(s):
    return escape(str(s), {'"': "&quot;"})


def R(x, y, w, h, fill="none", stroke=None, rx=None, cls=None, extra=""):
    rx_a = f' rx="{n(rx)}"' if rx else ""
    st = f' stroke="{stroke}"' if stroke else ""
    cls_a = f' class="{cls}"' if cls else ""
    return (f'<rect x="{n(x)}" y="{n(y)}" width="{n(w)}" height="{n(h)}" '
            f'fill="{fill}"{st}{rx_a}{cls_a}{extra}/>')


def T(x, y, s, size=11, fill=INK, weight="400", anchor="start", cls=None, ls=None, extra=""):
    cls_a = f' class="{cls}"' if cls else ""
    ls_a = f' letter-spacing="{n(ls)}"' if ls is not None else ""
    return (f'<text x="{n(x)}" y="{n(y)}" font-size="{n(size)}" fill="{fill}" '
            f'font-weight="{weight}" text-anchor="{anchor}"{cls_a}{ls_a}{extra}>{esc(s)}</text>')


def L(x1, y1, x2, y2, stroke=HAIR, width=1, dash=None, marker=None, cls=None):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    m = f' marker-end="url(#{marker})"' if marker else ""
    c = f' class="{c}"' if (c := cls) else ""
    return (f'<line x1="{n(x1)}" y1="{n(y1)}" x2="{n(x2)}" y2="{n(y2)}" '
            f'stroke="{stroke}" stroke-width="{n(width)}"{d}{m}{c}/>')


def diamond(cx, cy, r, fill, stroke="#FFFFFF", sw=1.5):
    pts = f"{n(cx)},{n(cy - r)} {n(cx + r)},{n(cy)} {n(cx)},{n(cy + r)} {n(cx - r)},{n(cy)}"
    return f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{n(sw)}"/>'


def prepare(tasks):
    by_id = {t["id"]: t for t in tasks}
    for t in tasks:
        for d in t["deps"]:
            if d not in by_id:
                raise ValueError(f"{t['id']}: unknown dependency {d}")
        if not (1 <= t["sw"] <= t["ew"] <= WEEKS):
            raise ValueError(f"{t['id']}: weeks out of range")
        t["dur"] = t["ew"] - t["sw"] + 1
        t["start"] = (t["sw"] - 1) * 7
        t["end"] = t["ew"] * 7

    succ = {t["id"]: [] for t in tasks}
    for t in tasks:
        for d in t["deps"]:
            succ[d].append(t["id"])

    clean = overlap = 0
    for t in tasks:
        starts = [by_id[s]["start"] for s in succ[t["id"]]]
        t["float"] = min(starts) - t["end"] if starts else 0
        t["critical"] = t["float"] <= 0
    for t in tasks:
        for d in t["deps"]:
            if by_id[d]["end"] <= t["start"]:
                clean += 1
            else:
                overlap += 1

    if clean != 8 or overlap != 10:
        raise ValueError(f"dependency mix changed: clean={clean} overlap={overlap}")
    floats = {t["id"]: t["float"] for t in tasks if not t["critical"]}
    if floats != {"5.1": 56, "5.2": 28}:
        raise ValueError(f"float set changed: {floats}")
    return by_id, succ


def wrap_name(name, width=37):
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
    return f"W{t['sw']}" if t["sw"] == t["ew"] else f"W{t['sw']}\u2013W{t['ew']}"


def fmt_span(t):
    a = date_of(t["start"])
    b = date_of(t["end"] - 1)
    return f"{a:%a %-d %b} \u2013 {b:%a %-d %b %Y}"


def tip_html(t):
    deps = ", ".join(t["deps"]) if t["deps"] else "none"
    if t["critical"]:
        status = "Driving chain (no float)"
    else:
        status = f"Float: {t['float'] // 7} weeks"
    body = (f"<b>{t['id']} \u2014 {t['name']}</b><br>"
            f"{fmt_span(t)}<br>"
            f"{week_span(t)} \u00b7 {t['dur']} weeks \u00b7 {PHASES[t['phase']][0]}<br>"
            f"Depends on: {deps} \u00b7 {status}")
    return esc_attr(body)


def build_svg():
    by_id, succ = prepare(TASKS)
    order = sorted(TASKS, key=lambda t: (t["start"], t["end"], t["id"]))
    idx = {t["id"]: i for i, t in enumerate(order)}
    dates = {t["id"]: t for t in TASKS}

    def ry(i):
        return PLOT_TOP + i * ROW_H

    def bar_y(t):
        return ry(idx[t["id"]]) + BAR_OFF

    def bar_right(t):
        return x_of(t["end"]) - 3

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
         f'viewBox="0 0 {WIDTH} {HEIGHT}" font-family="{ARCHIVO}" role="img" '
         f'aria-label="BioAgeVision project implementation plan, Gantt chart">']
    p.append(f'<title>{esc(PROJECT)} project implementation plan</title>')
    p.append(f"<defs><style>{SVG_CSS}</style>")
    p.append('<marker id="ah1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6.5" markerHeight="6.5" '
             'orient="auto" markerUnits="userSpaceOnUse"><path d="M0 0 L10 5 L0 10 z" fill="#7E8C97"/></marker>')
    p.append('<marker id="ah2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" '
             'orient="auto" markerUnits="userSpaceOnUse"><path d="M0 0 L10 5 L0 10 z" fill="#A9B5BD"/></marker>')
    p.append("</defs>")
    p.append(R(0, 0, WIDTH, HEIGHT, fill="#FCFDFC"))

    p.append(T(PAD, TITLE_Y, PROJECT, size=30, weight="700", ls=-0.4))
    p.append(T(PAD, SUBTITLE_Y, SUBTITLE, size=12, fill=MUTED))

    lx = PAD
    legend1 = ['<g class="phase-legend">']
    for key, (label, fill, tint, dark) in PHASES.items():
        legend1.append(R(lx, LEGEND1 - 10, 12, 12, fill=fill, rx=2))
        lx += 18
        legend1.append(T(lx, LEGEND1, label, size=11, fill=TEXT, weight="500"))
        lx += len(label) * 5.6 + 20
    legend1.append("</g>")
    p.append("".join(legend1))
    lx = PAD
    p.append(R(lx, LEGEND2 - 10, 22, 11, fill="#3F5566", rx=2))
    p.append(T(lx + 30, LEGEND2, "Driving chain (no float)", size=11, fill=MUTED))
    lx += 30 + 25 * 5.6 + 22
    p.append('<rect x="%s" y="%s" width="22" height="11" rx="2" fill="#C4DEED" stroke="#1F6E9C" '
             'stroke-width="1.2" stroke-dasharray="4 3"/>' % (n(lx), n(LEGEND2 - 10)))
    p.append(T(lx + 30, LEGEND2, "Float", size=11, fill=MUTED))
    lx += 30 + 5 * 5.6 + 22
    p.append(L(lx, LEGEND2 - 4, lx + 22, LEGEND2 - 4, stroke="#7E8C97", width=1.5, marker="ah1"))
    p.append(T(lx + 30, LEGEND2, "Handoff", size=11, fill=MUTED))
    lx += 30 + 7 * 5.6 + 22
    p.append(L(lx, LEGEND2 - 4, lx + 22, LEGEND2 - 4, stroke="#A9B5BD", width=1.2, dash="4 3", marker="ah2"))
    p.append(T(lx + 30, LEGEND2, "Overlap (starts before its dependency ends)", size=11, fill=MUTED))
    lx += 30 + 44 * 5.6 + 22
    p.append(diamond(lx + 6, LEGEND2 - 5, 5.5, PHASES["fin"][0], sw=1.2))
    p.append(T(lx + 20, LEGEND2, "Milestone", size=11, fill=MUTED))
    lx += 20 + 9 * 5.6 + 22
    p.append(L(lx + 6, LEGEND2 - 11, lx + 6, LEGEND2 + 3, stroke=DEADLINE, width=1.4, dash="4 3"))
    p.append(T(lx + 16, LEGEND2, "Deadline", size=11, fill=MUTED))

    p.append(R(PLOT_X, AXIS_TOP, PLOT_W, PLOT_TOP - AXIS_TOP, fill="#F2F4F4"))
    for a, b, label in MONTHS:
        x1, x2 = x_of(a), x_of(b)
        p.append(L(x1, AXIS_TOP, x1, ROWS_BOTTOM, stroke="#D3DADD", width=1))
        p.append(T(x1 + 9, AXIS_TOP + 14, label, size=10.5, fill=MUTED, weight="600", ls=0.3))
    p.append(L(PLOT_RIGHT, AXIS_TOP, PLOT_RIGHT, ROWS_BOTTOM, stroke="#D3DADD", width=1))
    p.append(L(PAD, MONTH_BOTTOM, PLOT_RIGHT, MONTH_BOTTOM, stroke=LINE, width=1))

    for w in range(WEEKS):
        wx = PLOT_X + w * WEEK_W
        p.append(T(wx + 9, WEEK_LABEL_Y, f"W{w + 1}", size=11, fill=INK, weight="600"))
        p.append(T(wx + 9, DATE_LABEL_Y, date_of(w * 7).strftime("%b %-d"), size=9, fill=FAINT))

    for d in range(TOTAL_DAYS + 1):
        dx = x_of(d)
        if d % 7 == 0:
            continue
        p.append(L(dx, PLOT_TOP - 4, dx, PLOT_TOP, stroke="#E1E6E7", width=1))
    for w in range(WEEKS + 1):
        gx = PLOT_X + w * WEEK_W
        p.append(L(gx, PLOT_TOP - 6, gx, PLOT_TOP, stroke="#C6CDD0", width=1))
        if w < WEEKS:
            p.append(L(gx, PLOT_TOP, gx, ROWS_BOTTOM, stroke=HAIR, width=1))
    p.append(L(PAD, PLOT_TOP, PLOT_RIGHT, PLOT_TOP, stroke=LINE, width=1))
    p.append(L(PAD, ROWS_BOTTOM, PLOT_RIGHT, ROWS_BOTTOM, stroke=LINE, width=1))
    p.append(L(PLOT_X, AXIS_TOP, PLOT_X, ROWS_BOTTOM, stroke=LINE, width=1))

    for i in range(len(order)):
        if i % 2:
            p.append(R(PAD, ry(i), PLOT_RIGHT - PAD, ROW_H, fill=PANEL))

    channel_k = {}
    for pred_id, succ_ids in succ.items():
        pred = dates[pred_id]
        overlap_k = 0
        for sid in succ_ids:
            s = dates[sid]
            x1 = bar_right(pred)
            yc1 = bar_y(pred) + BAR_H // 2
            xs = x_of(s["start"])
            yc2 = bar_y(s) + BAR_H // 2
            gap = xs - x1
            if gap >= 0:
                ck = channel_k.get(sid, 0)
                channel_k[sid] = ck + 1
                xv = (xs - 12 if gap >= 24 else x1) - 8 * ck
                path = f"M{n(x1)} {n(yc1)} H{n(xv)} V{n(yc2)} H{n(xs - 1)}"
                p.append(f'<path class="dep clean" data-from="{pred_id}" data-to="{sid}" '
                         f'd="{path}" marker-end="url(#ah1)"/>')
            else:
                tx = min(max(x1 + 16 + 10 * overlap_k, xs + 10), bar_right(s) - 10)
                overlap_k += 1
                path = f"M{n(x1)} {n(yc1)} H{n(tx)} V{n(bar_y(s) - 2)}"
                p.append(f'<path class="dep overlap" data-from="{pred_id}" data-to="{sid}" '
                         f'd="{path}" marker-end="url(#ah2)"/>')

    for t in order:
        key = t["phase"]
        label, fill, tint, dark = PHASES[key]
        status = "crit" if t["critical"] else "float"
        by = bar_y(t)
        bx = x_of(t["start"])
        bw = (t["end"] - t["start"]) * WEEK_W / 7 - 3
        if t["critical"]:
            bar = R(bx, by, bw, BAR_H, fill=fill, rx=3, cls="bx")
            lbl_fill = "#FFFFFF"
            dur_fill = "#E4EAEE"
        else:
            bar = (f'<rect x="{n(bx)}" y="{n(by)}" width="{n(bw)}" height="{n(BAR_H)}" rx="3" '
                   f'fill="{tint}" stroke="{fill}" stroke-width="1.2" stroke-dasharray="5 3" class="bx"/>')
            lbl_fill = INK
            dur_fill = MUTED
        dur_label = T(bx + bw - 8, by + 15, f"{t['dur']}w", cls="dur", fill=dur_fill, anchor="end")
        p.append(f'<g class="bar" data-task="{t["id"]}" data-phase="{key}" data-tip="{tip_html(t)}">'
                 f'{bar}'
                 f'{T(bx + 9, by + 15, t["id"], cls="lbl", fill=lbl_fill)}'
                 f'{dur_label}'
                 f"</g>")
        if not t["critical"]:
            p.append(T(bx + 6, by + BAR_H + 10, f"float {t['float'] // 7}w", size=9.5, fill=FAINT, weight="500"))

    p.append(T(PAD + 4, WEEK_LABEL_Y, "ID", size=10.5, fill=FAINT, weight="600"))
    p.append(T(PAD + ID_W, WEEK_LABEL_Y, "Task", size=10.5, fill=FAINT, weight="600"))
    p.append(T(PLOT_X - 12, WEEK_LABEL_Y, "Weeks", size=10.5, fill=FAINT, weight="600", anchor="end"))
    for i, t in enumerate(order):
        lines = wrap_name(t["name"])
        p.append(T(PAD + 4, ry(i) + 25, t["id"], size=11.5, weight="600"))
        if len(lines) == 1:
            p.append(T(PAD + ID_W, ry(i) + 25, lines[0], size=10.5, fill=TEXT))
        else:
            p.append(T(PAD + ID_W, ry(i) + 17, lines[0], size=10.5, fill=TEXT))
            p.append(T(PAD + ID_W, ry(i) + 31, lines[1], size=10.5, fill=TEXT))
        p.append(T(PLOT_X - 12, ry(i) + 25, f"{t['dur']}w", size=10.5, fill=MUTED, weight="500", anchor="end"))

    dl = x_of(TOTAL_DAYS)
    p.append(L(dl, MONTH_BOTTOM, dl, ROWS_BOTTOM, stroke=DEADLINE, width=1.4, dash="5 4"))
    p.append(f'<circle cx="{n(dl)}" cy="{n(MONTH_BOTTOM)}" r="3" fill="{DEADLINE}"/>')
    p.append(T(dl - 10, PLOT_TOP + 16, "Final deadline \u2014 Sat 19 Dec 2026", size=10, fill=DEADLINE, weight="600", anchor="end"))
    ms = dates["6.2"]
    p.append(diamond(dl, bar_y(ms) + BAR_H // 2, 5.5, PHASES["fin"][0]))

    p.append(T(PAD, HEIGHT - 14, "Weeks run Sunday to Saturday. Dashed handoffs mark tasks that start before their dependency finishes.", size=9.5, fill=FAINT))
    p.append(T(PLOT_RIGHT, HEIGHT - 14, "Generated from the project schedule table.", size=9.5, fill=FAINT, anchor="end"))
    p.append("</svg>")
    return "\n".join(p)


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>BioAgeVision \u2014 project implementation plan</title>
<style>
  @font-face {
    font-family: 'Archivo';
    src: url('fonts/archivo-latin.woff2') format('woff2');
    font-weight: 100 900;
    font-stretch: 62.5% 125%;
    font-display: swap;
  }
  :root {
    --page: #E9ECEB; --sheet: #FCFDFC; --ink: #16232E; --muted: #5B6B77; --faint: #8C9AA5;
    --line: #D9DEDF; --hardline: #BFC7CA;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; }
  body {
    background: var(--page); color: var(--ink);
    font-family: 'Archivo', 'Liberation Sans', 'Helvetica Neue', Arial, sans-serif;
    -webkit-font-smoothing: antialiased;
  }
  .shell { max-width: 1440px; margin: 0 auto; padding: 24px 26px 56px; }
  .chrome { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px 24px; flex-wrap: wrap; margin-bottom: 14px; }
  .controls { min-width: 280px; }
  .hint { margin: 0 0 9px; font-size: 11.5px; line-height: 1.45; color: var(--faint); }
  .chips { display: flex; flex-wrap: wrap; gap: 7px; }
  .chip {
    display: inline-flex; align-items: center; gap: 8px; padding: 8px 12px;
    background: #fff; border: 1px solid var(--line); border-radius: 2px;
    font: 500 12px/1 inherit; color: var(--ink); cursor: pointer;
  }
  .chip:hover { border-color: var(--hardline); }
  .chip .sw { width: 10px; height: 10px; border-radius: 1px; background: var(--c); }
  .chip[aria-pressed="true"] { border-color: var(--c); box-shadow: inset 0 -2px 0 var(--c); }
  .chip:focus-visible, .btn:focus-visible { outline: 2px solid var(--ink); outline-offset: 2px; }
  .actions { display: flex; gap: 8px; margin-left: auto; }
  .btn {
    padding: 11px 16px; border-radius: 2px; border: 1px solid var(--hardline);
    background: #fff; color: var(--ink); font: 600 12.5px/1 inherit; letter-spacing: .2px; cursor: pointer;
  }
  .btn:hover { background: #F2F4F4; }
  .btn.primary { background: var(--ink); border-color: var(--ink); color: #fff; }
  .btn.primary:hover { background: #0E1A23; }
  .sheet { background: var(--sheet); border: 1px solid var(--line); }
  .scroll { overflow-x: auto; }
  .sheet svg { display: block; width: 100%; height: auto; min-width: 1020px; }
  .sheet svg .phase-legend { display: none; }
  #tip {
    position: fixed; left: 0; top: 0; z-index: 50; pointer-events: none;
    background: var(--ink); color: #E8EDF0; padding: 10px 12px; border-radius: 3px;
    font-size: 12px; line-height: 1.55; max-width: 380px;
    box-shadow: 0 6px 18px rgba(22, 35, 46, .18); opacity: 0; transition: opacity .1s;
  }
  #tip.on { opacity: 1; }
  #tip b { color: #fff; }
  @media print {
    @page { size: A4 landscape; margin: 8mm; }
    body { background: #fff; }
    .chrome, #tip { display: none; }
    .shell { max-width: none; margin: 0; padding: 0; }
    .sheet { border: 0; }
    .scroll { overflow: visible; }
    .sheet svg { min-width: 0; }
    .sheet svg .phase-legend { display: inline; }
  }
</style>
</head>
<body>
<div class="shell">
  <div class="chrome">
    <div class="controls">
      <p class="hint">Select a phase to isolate it on the chart. Select it again to show everything.</p>
      <div class="chips">__CHIPS__</div>
    </div>
    <div class="actions">
      <button class="btn" id="print">Print / Save PDF</button>
      <button class="btn primary" id="png">Download PNG</button>
    </div>
  </div>
  <div class="sheet"><div class="scroll">__SVG__</div></div>
</div>
<div id="tip"></div>
<script>
(function () {
  var svg = document.querySelector('.sheet svg');
  var tip = document.getElementById('tip');
  var phaseOf = {};
  document.querySelectorAll('.bar').forEach(function (g) {
    phaseOf[g.getAttribute('data-task')] = g.getAttribute('data-phase');
  });
  var active = new Set();
  function apply() {
    var on = active.size > 0;
    document.querySelectorAll('.bar').forEach(function (g) {
      g.classList.toggle('dim', on && !active.has(g.getAttribute('data-phase')));
    });
    document.querySelectorAll('.dep').forEach(function (p) {
      var a = phaseOf[p.getAttribute('data-from')];
      var b = phaseOf[p.getAttribute('data-to')];
      p.classList.toggle('dim', on && !(active.has(a) || active.has(b)));
    });
  }
  document.querySelectorAll('.chip').forEach(function (c) {
    c.addEventListener('click', function () {
      var p = c.getAttribute('data-phase');
      if (active.has(p)) { active.delete(p); } else { active.add(p); }
      c.setAttribute('aria-pressed', active.has(p) ? 'true' : 'false');
      apply();
    });
  });
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
      ctx.fillStyle = '#FCFDFC';
      ctx.fillRect(0, 0, c.width, c.height);
      ctx.drawImage(img, 0, 0, c.width, c.height);
      URL.revokeObjectURL(url);
      var a = document.createElement('a');
      a.download = 'BioAgeVision-plan.png';
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


def build_chips():
    out = []
    for key, (label, fill, tint, dark) in PHASES.items():
        out.append(f'<button class="chip" data-phase="{key}" aria-pressed="false" style="--c:{fill}">'
                   f'<span class="sw"></span>{esc(label)}</button>')
    return "\n      ".join(out)


def main():
    order = sorted(TASKS, key=lambda t: (t["sw"], t["ew"], t["id"]))
    svg = build_svg()
    page = HTML.replace("__CHIPS__", build_chips()).replace("__SVG__", svg)
    Path("gantt.svg").write_text(svg, encoding="utf-8")
    Path("gantt.html").write_text(page, encoding="utf-8")
    Path("index.html").write_text(page, encoding="utf-8")
    ET.fromstring(svg)
    try:
        import subprocess

        subprocess.run(["rsvg-convert", "-z", "2", "gantt.svg", "-o", "gantt.png"], check=True)
        print("wrote gantt.png (2x, via rsvg-convert)")
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("rsvg-convert not found \u2014 use the Download PNG button in gantt.html instead")
    print(f"wrote gantt.svg, gantt.html, index.html \u00b7 {WEEKS} weeks, {len(TASKS)} tasks")
    for t in order:
        a, b = date_of((t["sw"] - 1) * 7), date_of(t["ew"] * 7 - 1)
        flag = "driving" if t["float"] <= 0 else f"float {t['float'] // 7}w"
        print(f"  {t['id']:<4} {a:%a %-d %b} \u2013 {b:%a %-d %b}  {t['dur']}w  {flag:10}  {t['name']}")


if __name__ == "__main__":
    main()
