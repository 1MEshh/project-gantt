#!/usr/bin/env python3
"""Generate the Discrepancy Modeling two-phase project plan: standalone SVG figure plus an interactive page."""

import datetime as dt
import xml.etree.ElementTree as ET
from pathlib import Path
from xml.sax.saxutils import escape

START1 = dt.date(2026, 9, 13)
START2 = dt.date(2027, 1, 14)
P1_WEEKS = 14
P2_WEEKS = 15
P1_DAYS = P1_WEEKS * 7
P2_DAYS = P2_WEEKS * 7
COLS = P1_WEEKS + P2_WEEKS

TASKS = [
    dict(id="1.0", name="Project Initialization (Motivation, Problem, Objective)", phase=1, sw=1, ew=2, kind="core", deps=[]),
    dict(id="1.1", name="Draft Chapter 1: Introduction", phase=1, sw=2, ew=3, kind="draft", deps=["1.0"]),
    dict(id="2.0", name="Systematic Literature Review", phase=1, sw=4, ew=6, kind="core", deps=["1.0"]),
    dict(id="2.1", name="Draft Chapter 2: Literature review", phase=1, sw=6, ew=8, kind="draft", deps=["2.0"]),
    dict(id="3.0", name="Stage 1: Data collection", phase=1, sw=8, ew=9, kind="core", deps=["2.0"]),
    dict(id="3.1", name="Stage 2: Data analysis", phase=1, sw=9, ew=10, kind="core", deps=["3.0"]),
    dict(id="3.2", name="Stage 3: Methodology design", phase=1, sw=10, ew=12, kind="core", deps=["3.1"]),
    dict(id="3.3", name="Draft Chapter 3: Methodology", phase=1, sw=11, ew=13, kind="draft", deps=["3.2"]),
    dict(id="4.0", name="Phase One Final Review & Polish", phase=1, sw=13, ew=14, kind="core", deps=["3.3"]),
    dict(id="M1", name="Phase 1 Final Submission", phase=1, sw=14, ew=14, kind="milestone", deps=["4.0"]),
    dict(id="5.0", name="System Implementation & App Deployment", phase=2, sw=1, ew=6, kind="core", deps=["M1"]),
    dict(id="5.1", name="Draft Chapter 4: Implementation", phase=2, sw=5, ew=7, kind="draft", deps=["5.0"]),
    dict(id="6.0", name="System Results and Testing", phase=2, sw=7, ew=10, kind="core", deps=["5.0"]),
    dict(id="6.1", name="Draft Chapter 5: Result and testing", phase=2, sw=9, ew=12, kind="draft", deps=["6.0"]),
    dict(id="7.0", name="Draft Chapter 6: Conclusion", phase=2, sw=12, ew=13, kind="draft", deps=["6.1"]),
    dict(id="8.0", name="Final Report Review & Formatting", phase=2, sw=13, ew=15, kind="core", deps=["7.0"]),
    dict(id="M2", name="Phase 2 Final Submission", phase=2, sw=15, ew=15, kind="milestone", deps=["8.0"]),
]

PHASES = {
    1: ("Phase 1", "Sep 13 \u2013 Dec 19, 2026", "#1D4E7C", "#D7E3EE", "#143A5C"),
    2: ("Phase 2", "Jan 14 \u2013 Apr 29, 2027", "#2A7D74", "#D3E6E3", "#1F5E57"),
}

MILESTONE_DATES = {"M1": dt.date(2026, 12, 19), "M2": dt.date(2027, 4, 29)}
OVERLAP_PAIRS = {
    ("1.0", "1.1"), ("2.0", "2.1"), ("3.0", "3.1"), ("3.1", "3.2"), ("3.2", "3.3"), ("3.3", "4.0"),
    ("5.0", "5.1"), ("6.0", "6.1"), ("6.1", "7.0"), ("7.0", "8.0"),
}

INK = "#16232E"
TEXT = "#3A4A54"
MUTED = "#5B6B77"
FAINT = "#8C9AA5"
HAIR = "#E8ECEC"
LINE = "#D9DEDF"
PANEL = "#F5F7F7"
CRIMSON = "#A32B2B"
CLEAN = "#7E8C97"
OVERLAP = "#A9B5BD"
ARCHIVO = "Archivo, 'Liberation Sans', 'Helvetica Neue', Arial, sans-serif"

PROJECT = "Discrepancy Modeling for Biological vs. Chronological Facial Age Estimation"
PAGE_TITLE = PROJECT + " \u2014 two-phase project plan"
PNG_NAME = "Discrepancy-Modeling-plan.png"

PAD = 28
LEFT_W = 300
ID_W = 48
WEEK_W = 58
PLOT_X = PAD + LEFT_W
PLOT_W = COLS * WEEK_W
PLOT_RIGHT = PLOT_X + PLOT_W
WIDTH = PLOT_RIGHT + PAD + 4
TITLE_Y = 44
LEGEND_Y = 82
BANNER_TOP = 104
BANNER_H = 24
BANNER_BOTTOM = BANNER_TOP + BANNER_H
WEEK_Y = 147
DATE_Y = 161
PLOT_TOP = 171
ROW_H = 38
BAR_H = 20
BAR_OFF = 9
ROWS_BOTTOM = PLOT_TOP + len(TASKS) * ROW_H
HEIGHT = ROWS_BOTTOM + 34
MONTH_LINES = [(18, "Oct"), (49, "Nov"), (79, "Dec"), (116, "Feb"), (144, "Mar"), (175, "Apr")]

SVG_CSS = """
text{font-family:%s}
.dep{fill:none;stroke-linecap:square}
.clean{stroke:%s;stroke-width:1.5}
.overlap{stroke:%s;stroke-width:1.2;stroke-dasharray:4 3}
.bar,.ms{cursor:pointer;transition:opacity .15s ease}
.dep.dim,.bar.dim,.ms.dim{opacity:.12}
.bar .lbl{font-size:10.5px;font-weight:700}
.bar .dur{font-size:9px;font-weight:500}
.bar:hover .bx{stroke:%s;stroke-width:2}
.ms:hover polygon{stroke:%s;stroke-width:2}
""" % (ARCHIVO, CLEAN, OVERLAP, INK, INK)


def n(v):
    v = round(float(v), 1)
    return str(int(v)) if v == int(v) else str(v)


def xg(g):
    return PLOT_X + g * WEEK_W / 7.0


def gdate(g, phase):
    if phase == 1:
        return START1 + dt.timedelta(days=g)
    return START2 + dt.timedelta(days=g - P1_DAYS)


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
    c = f' class="{cls}"' if cls else ""
    return (f'<line x1="{n(x1)}" y1="{n(y1)}" x2="{n(x2)}" y2="{n(y2)}" '
            f'stroke="{stroke}" stroke-width="{n(width)}"{d}{m}{c}/>')


def diamond(cx, cy, r, fill, stroke="#FFFFFF", sw=1.5, extra=""):
    pts = f"{n(cx)},{n(cy - r)} {n(cx + r)},{n(cy)} {n(cx)},{n(cy + r)} {n(cx - r)},{n(cy)}"
    return f'<polygon points="{pts}" fill="{fill}" stroke="{stroke}" stroke-width="{n(sw)}"{extra}/>'


def prepare(tasks):
    by_id = {t["id"]: t for t in tasks}
    for t in tasks:
        for d in t["deps"]:
            if d not in by_id:
                raise ValueError(f"{t['id']}: unknown dependency {d}")
        weeks = P1_WEEKS if t["phase"] == 1 else P2_WEEKS
        if not (1 <= t["sw"] <= t["ew"] <= weeks):
            raise ValueError(f"{t['id']}: weeks out of range")
        if t["kind"] == "milestone":
            if t["sw"] != t["ew"]:
                raise ValueError(f"{t['id']}: milestone spans more than one week")
        t["dur"] = t["ew"] - t["sw"] + 1
        offset = 0 if t["phase"] == 1 else P1_DAYS
        t["start"] = (t["sw"] - 1) * 7 + offset
        t["end"] = t["ew"] * 7 + offset
        if t["kind"] == "milestone":
            t["point"] = t["end"]
            t["start"] = t["end"] = t["point"]

    for t in tasks:
        if t["kind"] != "milestone":
            continue
        t["date"] = MILESTONE_DATES[t["id"]]
    if gdate(by_id["M1"]["point"] - 1, 1) != MILESTONE_DATES["M1"]:
        raise ValueError("M1: date mismatch")
    if gdate(by_id["M2"]["point"], 2) != MILESTONE_DATES["M2"]:
        raise ValueError("M2: date mismatch")

    succ = {t["id"]: [] for t in tasks}
    overlaps = set()
    for t in tasks:
        for d in t["deps"]:
            succ[d].append(t["id"])
            if by_id[d]["end"] > t["start"]:
                overlaps.add((d, t["id"]))
    if overlaps != OVERLAP_PAIRS:
        raise ValueError(f"overlap set changed: {overlaps ^ OVERLAP_PAIRS}")
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
    if t["kind"] == "milestone":
        return f"End of {PHASES[t['phase']][0]} \u00b7 {t['date']:%a %-d %b %Y}"
    a = gdate(t["start"], t["phase"])
    b = gdate(t["end"] - 1, t["phase"])
    return f"{a:%a %-d %b %Y} \u2013 {b:%a %-d %b %Y}"


def tip_html(t):
    deps = ", ".join(t["deps"]) if t["deps"] else "none"
    label, _, _, _, _ = PHASES[t["phase"]]
    if t["kind"] == "milestone":
        body = (f"<b>{t['id']} \u2014 {t['name']}</b><br>"
                f"{fmt_span(t)}<br>Milestone \u00b7 {label}<br>Depends on: {deps}")
    else:
        kind = "Core task" if t["kind"] == "core" else "Drafting / parallel task"
        body = (f"<b>{t['id']} \u2014 {t['name']}</b><br>"
                f"{fmt_span(t)}<br>"
                f"{week_span(t)} \u00b7 {t['dur']} weeks \u00b7 {label}<br>"
                f"{kind} \u00b7 Depends on: {deps}")
    return esc_attr(body)


def build_svg():
    by_id, succ = prepare(TASKS)
    order = sorted(TASKS, key=lambda t: (t["phase"], t["start"], t["end"], t["id"]))
    idx = {t["id"]: i for i, t in enumerate(order)}
    xb = xg(P1_DAYS)

    def ry(i):
        return PLOT_TOP + i * ROW_H

    def yc(t):
        return ry(idx[t["id"]]) + BAR_OFF + BAR_H // 2

    def bar_y(t):
        return ry(idx[t["id"]]) + BAR_OFF

    def bar_left(t):
        return xg(t["start"])

    def bar_right(t):
        return xg(t["end"]) - 3

    def bar_width(t):
        return (t["end"] - t["start"]) * WEEK_W / 7

    def anchor(t):
        if t["kind"] == "milestone":
            return xg(t["point"]), yc(t)
        return bar_right(t), yc(t)

    p = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" '
         f'viewBox="0 0 {WIDTH} {HEIGHT}" font-family="{ARCHIVO}" role="img" '
         f'aria-label="{esc_attr(PROJECT)} \u2014 two-phase project plan, Gantt chart">']
    p.append(f'<title>{esc(PAGE_TITLE)}</title>')
    p.append(f"<defs><style>{SVG_CSS}</style>")
    p.append(f'<marker id="ah1" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6.5" markerHeight="6.5" '
             f'orient="auto" markerUnits="userSpaceOnUse"><path d="M0 0 L10 5 L0 10 z" fill="{CLEAN}"/></marker>')
    p.append(f'<marker id="ah2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" '
             f'orient="auto" markerUnits="userSpaceOnUse"><path d="M0 0 L10 5 L0 10 z" fill="{OVERLAP}"/></marker>')
    p.append("</defs>")
    p.append(R(0, 0, WIDTH, HEIGHT, fill="#FCFDFC"))

    p.append(f'<g class="svg-title">{T(PAD, TITLE_Y, PROJECT, size=30, weight="700", ls=-0.4)}</g>')

    lx = PAD
    p.append(f'<rect x="{n(lx)}" y="{n(LEGEND_Y - 10)}" width="22" height="12" rx="2" '
             f'fill="{PHASES[1][3]}" stroke="{PHASES[1][2]}" stroke-width="1.2"/>')
    p.append(T(lx + 30, LEGEND_Y, "Drafting / parallel task", size=11, fill=MUTED))
    lx += 30 + 25 * 5.6 + 22
    p.append(diamond(lx + 6, LEGEND_Y - 5, 5.5, INK, sw=1.2))
    p.append(T(lx + 20, LEGEND_Y, "Milestone", size=11, fill=MUTED))
    lx += 20 + 9 * 5.6 + 22
    p.append(L(lx, LEGEND_Y - 4, lx + 22, LEGEND_Y - 4, stroke=CLEAN, width=1.5, marker="ah1"))
    p.append(T(lx + 30, LEGEND_Y, "Handoff", size=11, fill=MUTED))
    lx += 30 + 7 * 5.6 + 22
    p.append(L(lx, LEGEND_Y - 4, lx + 22, LEGEND_Y - 4, stroke=OVERLAP, width=1.2, dash="4 3", marker="ah2"))
    p.append(T(lx + 30, LEGEND_Y, "Overlap (starts before its dependency ends)", size=11, fill=MUTED))
    lx += 30 + 44 * 5.6 + 22
    p.append(L(lx + 6, LEGEND_Y - 12, lx + 6, LEGEND_Y + 2, stroke=CRIMSON, width=1.4, dash="4 3"))
    p.append(T(lx + 16, LEGEND_Y, "Submission", size=11, fill=MUTED))
    lx += 16 + 10 * 5.6 + 30
    phase_legend = ['<g class="phase-legend">']
    for key, (label, span, accent, tint, dark) in PHASES.items():
        phase_legend.append(R(lx, LEGEND_Y - 10, 12, 12, fill=accent, rx=2))
        lx += 18
        phase_legend.append(T(lx, LEGEND_Y, label, size=11, fill=TEXT, weight="500"))
        lx += len(label) * 5.6 + 22
    phase_legend.append("</g>")
    p.append("".join(phase_legend))

    for r in range(len(order)):
        if r % 2:
            p.append(R(PAD, ry(r), PLOT_RIGHT - PAD, ROW_H, fill=PANEL))
    first_p2 = min(idx[t["id"]] for t in order if t["phase"] == 2)
    p.append(L(PAD, ry(first_p2), PLOT_RIGHT, ry(first_p2), stroke="#CED6D8", width=1))

    p.append(L(PLOT_RIGHT, BANNER_BOTTOM, PLOT_RIGHT, ROWS_BOTTOM, stroke=CRIMSON, width=1.4, dash="5 4"))
    for g, label in MONTH_LINES:
        mx = xg(g)
        p.append(L(mx, PLOT_TOP, mx, ROWS_BOTTOM, stroke="#DCE2E3", width=1))
        p.append(T(mx + 4, PLOT_TOP + 12, label, size=8.5, fill="#A9B4BA", weight="600"))
    for w in range(COLS + 1):
        gx = xg(w * 7)
        p.append(L(gx, PLOT_TOP, gx, ROWS_BOTTOM, stroke=HAIR, width=1))
    p.append(L(PAD, PLOT_TOP, PLOT_RIGHT, PLOT_TOP, stroke=LINE, width=1))
    p.append(L(PAD, ROWS_BOTTOM, PLOT_RIGHT, ROWS_BOTTOM, stroke=LINE, width=1))
    p.append(L(PLOT_X, BANNER_TOP, PLOT_X, ROWS_BOTTOM, stroke=LINE, width=1))

    for key, (label, span, accent, tint, dark) in PHASES.items():
        x1 = PLOT_X if key == 1 else xb
        x2 = xb if key == 1 else PLOT_RIGHT
        p.append(R(x1, BANNER_TOP, x2 - x1, BANNER_H, fill=tint))
        p.append(R(x1, BANNER_BOTTOM - 2, x2 - x1, 2, fill=accent))
        p.append(T(x1 + 10, BANNER_TOP + 16, label, size=12, fill=dark, weight="700"))
        p.append(T(x1 + 10 + len(label) * 7.2 + 12, BANNER_TOP + 16, span, size=10, fill=MUTED, weight="500"))
    p.append(L(PLOT_X, BANNER_BOTTOM, PLOT_RIGHT, BANNER_BOTTOM, stroke=LINE, width=1))

    p.append(L(xb - 3, BANNER_TOP, xb - 3, ROWS_BOTTOM, stroke="#BFC7CA", width=1))
    p.append(L(xb + 3, BANNER_TOP, xb + 3, ROWS_BOTTOM, stroke="#BFC7CA", width=1))
    p.append(R(xb - 9, BANNER_BOTTOM, 18, PLOT_TOP - BANNER_BOTTOM, fill="#FCFDFC"))
    p.append(L(xb - 4, PLOT_TOP - 4, xb + 2, BANNER_BOTTOM + 5, stroke=FAINT, width=1.3))
    p.append(L(xb + 2, PLOT_TOP - 4, xb + 8, BANNER_BOTTOM + 5, stroke=FAINT, width=1.3))

    for w in range(COLS):
        wx = xg(w * 7)
        phase = 1 if w < P1_WEEKS else 2
        local = w if phase == 1 else w - P1_WEEKS
        p.append(T(wx + 7, WEEK_Y, f"W{local + 1}", size=10.5, fill=INK, weight="600"))
        p.append(T(wx + 7, DATE_Y, gdate(w * 7, phase).strftime("%b %-d"), size=8.5, fill=FAINT))
    for d in range(COLS * 7):
        if d % 7 == 0:
            continue
        p.append(L(xg(d), PLOT_TOP - 4, xg(d), PLOT_TOP, stroke="#E1E6E7", width=1))
    for w in range(COLS + 1):
        p.append(L(xg(w * 7), PLOT_TOP - 6, xg(w * 7), PLOT_TOP, stroke="#C6CDD0", width=1))

    for pred_id, succ_ids in succ.items():
        pred = by_id[pred_id]
        overlap_k = 0
        for sid in succ_ids:
            s = by_id[sid]
            if s["kind"] == "milestone":
                mx = xg(s["point"])
                if pred["kind"] == "milestone":
                    continue
                if anchor(pred)[0] <= mx - 14:
                    path = f"M{n(bar_right(pred))} {n(yc(pred))} H{n(mx - 8)}"
                else:
                    path = f"M{n(mx)} {n(bar_y(pred) + BAR_H)} V{n(yc(s) - 8)}"
                p.append(f'<path class="dep clean" data-from="{pred_id}" data-to="{sid}" '
                         f'd="{path}" marker-end="url(#ah1)"/>')
                continue
            x1, yc1 = anchor(pred)
            xs = bar_left(s)
            yc2 = yc(s)
            gap = xs - x1
            if pred["kind"] == "milestone":
                tx = min(max(x1 + 14, xs + 10), bar_right(s) - 10)
                if xs >= x1 + 20:
                    path = f"M{n(x1)} {n(yc1)} H{n(xs - 12)} V{n(yc2)} H{n(xs - 1)}"
                else:
                    path = f"M{n(x1)} {n(yc1)} H{n(tx)} V{n(bar_y(s) - 2)}"
                p.append(f'<path class="dep clean" data-from="{pred_id}" data-to="{sid}" '
                         f'd="{path}" marker-end="url(#ah1)"/>')
            elif gap >= 24:
                path = f"M{n(x1)} {n(yc1)} H{n(xs - 12 - 8 * overlap_k)} V{n(yc2)} H{n(xs - 1)}"
                p.append(f'<path class="dep clean" data-from="{pred_id}" data-to="{sid}" '
                         f'd="{path}" marker-end="url(#ah1)"/>')
            elif gap >= 0:
                path = f"M{n(x1)} {n(yc1)} H{n(x1 - 8 * overlap_k)} V{n(yc2)} H{n(xs - 1)}"
                p.append(f'<path class="dep clean" data-from="{pred_id}" data-to="{sid}" '
                         f'd="{path}" marker-end="url(#ah1)"/>')
            else:
                tx = min(max(x1 + 16 + 10 * overlap_k, xs + 10), bar_right(s) - 10)
                overlap_k += 1
                path = f"M{n(x1)} {n(yc1)} H{n(tx)} V{n(bar_y(s) - 2)}"
                p.append(f'<path class="dep overlap" data-from="{pred_id}" data-to="{sid}" '
                         f'd="{path}" marker-end="url(#ah2)"/>')

    for t in order:
        if t["kind"] == "milestone":
            continue
        phase = t["phase"]
        label, span, accent, tint, dark = PHASES[phase]
        by = bar_y(t)
        bx = bar_left(t)
        bw = bar_width(t) - 3
        if t["kind"] == "core":
            bar = R(bx, by, bw, BAR_H, fill=accent, rx=3, cls="bx")
            lbl_fill, dur_fill = "#FFFFFF", "#E4EAEE"
        else:
            bar = (f'<rect x="{n(bx)}" y="{n(by)}" width="{n(bw)}" height="{n(BAR_H)}" rx="3" '
                   f'fill="{tint}" stroke="{accent}" stroke-width="1.2" class="bx"/>')
            lbl_fill, dur_fill = INK, MUTED
        dur_label = T(bx + bw - 8, by + 14, f"{t['dur']}w", cls="dur", fill=dur_fill, anchor="end")
        p.append(f'<g class="bar" data-task="{t["id"]}" data-phase="{phase}" data-tip="{tip_html(t)}">'
                 f'{bar}'
                 f'{T(bx + 9, by + 14, t["id"], cls="lbl", fill=lbl_fill)}'
                 f'{dur_label}'
                 f"</g>")

    for t in order:
        if t["kind"] != "milestone":
            continue
        phase = t["phase"]
        label, span, accent, tint, dark = PHASES[phase]
        mx = xg(t["point"])
        my = yc(t)
        p.append(f'<g class="ms" data-task="{t["id"]}" data-phase="{phase}" data-tip="{tip_html(t)}">'
                 f'{diamond(mx, my, 6, INK)}'
                 f'{T(mx - 10, my + 3, t["date"].strftime("%-d %b %Y"), size=9.5, fill=dark, weight="600", anchor="end")}'
                 f'</g>')

    p.append(T(PAD + 4, WEEK_Y, "ID", size=10.5, fill=FAINT, weight="600"))
    p.append(T(PAD + ID_W, WEEK_Y, "Task", size=10.5, fill=FAINT, weight="600"))
    p.append(T(PLOT_X - 12, WEEK_Y, "Weeks", size=10.5, fill=FAINT, weight="600", anchor="end"))
    for i, t in enumerate(order):
        lines = wrap_name(t["name"])
        weeks = "\u2014" if t["kind"] == "milestone" else f"{t['dur']}w"
        p.append(T(PAD + 4, ry(i) + 24, t["id"], size=11.5, weight="600"))
        if len(lines) == 1:
            p.append(T(PAD + ID_W, ry(i) + 24, lines[0], size=10.5, fill=TEXT))
        else:
            p.append(T(PAD + ID_W, ry(i) + 16, lines[0], size=10.5, fill=TEXT))
            p.append(T(PAD + ID_W, ry(i) + 29, lines[1], size=10.5, fill=TEXT))
        p.append(T(PLOT_X - 12, ry(i) + 24, weeks, size=10.5, fill=MUTED, weight="500", anchor="end"))

    p.append("</svg>")
    return "\n".join(p)


HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>__PAGE_TITLE__</title>
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
  .shell { max-width: 2100px; margin: 0 auto; padding: 24px 26px 56px; }
  .chrome { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px 24px; flex-wrap: wrap; margin-bottom: 14px; }
  .controls { min-width: 280px; }
  .hint { margin: 0 0 9px; font-size: 11.5px; line-height: 1.45; color: var(--faint); }
  .chips { display: flex; flex-wrap: wrap; gap: 7px; }
  .chip {
    display: inline-flex; align-items: center; gap: 8px; padding: 8px 14px;
    background: #fff; border: 1px solid var(--line); border-radius: 2px;
    font: 500 12.5px/1 inherit; color: var(--ink); cursor: pointer;
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
  .scroll { overflow-x: auto; -webkit-overflow-scrolling: touch; overscroll-behavior-x: contain; }
  .sheet svg { display: block; width: 100%; height: auto; min-width: 1400px; }
  .sheet svg .phase-legend { display: none; }
  .touch-hint { display: none; }
  .mobile-title { display: none; margin: 0 0 14px; font-size: 19px; line-height: 1.3; font-weight: 700; letter-spacing: -.2px; }
  #tip {
    position: fixed; left: 0; top: 0; z-index: 50; pointer-events: none;
    background: var(--ink); color: #E8EDF0; padding: 10px 12px; border-radius: 3px;
    font-size: 12px; line-height: 1.55; max-width: min(380px, calc(100vw - 28px));
    box-shadow: 0 6px 18px rgba(22, 35, 46, .18); opacity: 0; transition: opacity .1s;
  }
  #tip.on { opacity: 1; }
  #tip b { color: #fff; }
  @media (max-width: 700px) {
    .shell { padding: 16px 14px 40px; }
    .hint { font-size: 11px; }
    .touch-hint { display: block; }
    .chips { gap: 8px; }
    .chip { padding: 10px 14px; }
    .actions { width: 100%; margin-left: 0; }
    .btn { flex: 1; padding: 14px 12px; }
    .sheet svg { min-width: 2000px; }
    .sheet svg .svg-title { display: none; }
    .mobile-title { display: block; }
  }
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
  <h1 class="mobile-title">__PROJECT__</h1>
  <div class="chrome">
    <div class="controls">
      <p class="hint">Select a phase to isolate it on the chart. Select it again to show everything.</p>
      <div class="chips">__CHIPS__</div>
      <p class="hint touch-hint">Drag the chart sideways to see the full timeline.</p>
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
  var dimmable = '.bar, .ms';
  var isTouch = window.matchMedia('(hover: none)').matches;
  function placeTip(cx, cy) {
    var r = tip.getBoundingClientRect();
    var x = cx + 16, y = cy + 16;
    if (x + r.width > window.innerWidth - 8) x = cx - r.width - 16;
    if (y + r.height > window.innerHeight - 8) y = cy - r.height - 16;
    tip.style.left = Math.max(8, x) + 'px';
    tip.style.top = Math.max(8, y) + 'px';
  }
  function showTip(g, cx, cy) {
    tip.innerHTML = g.getAttribute('data-tip');
    tip.dataset.task = g.getAttribute('data-task');
    tip.classList.add('on');
    placeTip(cx, cy);
  }
  function hideTip() { tip.classList.remove('on'); tip.dataset.task = ''; }
  document.querySelectorAll(dimmable).forEach(function (g) {
    g.addEventListener('mouseenter', function (e) { showTip(g, e.clientX, e.clientY); });
    g.addEventListener('mousemove', function (e) { placeTip(e.clientX, e.clientY); });
    g.addEventListener('mouseleave', hideTip);
    if (isTouch) {
      g.addEventListener('click', function (e) {
        e.stopPropagation();
        if (tip.dataset.task === g.getAttribute('data-task') && tip.classList.contains('on')) {
          hideTip();
        } else {
          showTip(g, e.clientX, e.clientY);
        }
      });
    }
  });
  document.addEventListener('click', function (e) {
    if (!e.target.closest || !e.target.closest('.bar, .ms')) hideTip();
  });
  var active = new Set();
  function apply() {
    var on = active.size > 0;
    document.querySelectorAll(dimmable).forEach(function (g) {
      g.classList.toggle('dim', on && !active.has(g.getAttribute('data-phase')));
    });
    document.querySelectorAll('.dep').forEach(function (p) {
      var a = p.getAttribute('data-from'), b = p.getAttribute('data-to');
      var pa = a.charAt(0) === 'M' ? a.charAt(1) : a.charAt(0);
      var pb = b.charAt(0) === 'M' ? b.charAt(1) : b.charAt(0);
      p.classList.toggle('dim', on && !(active.has(pa) && active.has(pb)));
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
      a.download = '__PNG__';
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
    for key, (label, span, accent, tint, dark) in PHASES.items():
        out.append(f'<button class="chip" data-phase="{key}" aria-pressed="false" style="--c:{accent}">'
                   f'<span class="sw"></span>{esc(label)}</button>')
    return "\n      ".join(out)


def main():
    svg = build_svg()
    page = (HTML.replace("__CHIPS__", build_chips())
                .replace("__SVG__", svg)
                .replace("__PAGE_TITLE__", esc(PAGE_TITLE))
                .replace("__PROJECT__", esc(PROJECT))
                .replace("__PNG__", PNG_NAME))
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
    print(f"wrote gantt.svg, gantt.html, index.html \u00b7 {COLS} week columns, {len(TASKS)} rows")
    for t in sorted(TASKS, key=lambda x: (x["phase"], x["start"], x["id"])):
        if t["kind"] == "milestone":
            print(f"  {t['id']:<3} milestone                 {t['date']:%a %-d %b %Y}   {t['name']}")
        else:
            a, b = gdate(t["start"], t["phase"]), gdate(t["end"] - 1, t["phase"])
            print(f"  {t['id']:<3} {a:%a %-d %b %Y} \u2013 {b:%a %-d %b %Y}  {t['dur']}w  "
                  f"{'core' if t['kind'] == 'core' else 'draft':5}  {t['name']}")


if __name__ == "__main__":
    main()
