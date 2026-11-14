#!/usr/bin/env python3
"""Generates the detail pages of the Lucifer Lab site from the published run.

    python3 tools/build.py [path-to-Lucifer-BenchMarks-checkout]

Every figure on the generated pages is computed here from results/published/qwen14b-convention/rows.json (copied to data/), and the
task text comes from the lab's own src/lucifer/tasks.py, so nothing is typed in by hand. The output is plain HTML committed to the repo;
there is no build step on the host. Re-run this after publishing a new run.
"""
from __future__ import annotations

import html
import json
import re
import shutil
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

SITE = Path(__file__).resolve().parent.parent
LAB = Path(sys.argv[1]) if len(sys.argv) > 1 else SITE.parent / "lucifer-lab"
RUN = LAB / "results" / "published" / "qwen14b-convention"
sys.path.insert(0, str(LAB / "src"))

from lucifer.agent import NOTES_HEADER, RETRY_MARKER, failure_lesson  # noqa: E402
from lucifer.sandbox import SandboxExecutor  # noqa: E402
from lucifer.tasks import BY_ID, TASKS  # noqa: E402

REPO = "https://github.com/Lakshit-Startup-Ideas/Lucifer-BenchMarks"
COMMIT = "1a88d19"
RUN_ID = "43163827087"
CONDS = ("baseline", "lucifer", "irrelevant")
CNAME = {"baseline": "No memory", "lucifer": "Lucifer", "irrelevant": "Wrong notes"}
PHASES = ("experience", "similar", "transfer", "replay")

rows = json.loads((RUN / "rows.json").read_text())
audits = json.loads((RUN / "audits.json").read_text())
meta = json.loads((RUN / "meta.json").read_text())
report = (RUN / "report.txt").read_text()

e = html.escape


def pct(n: int, d: int) -> str:
    return f"{round(100 * n / d)}%" if d else "–"


def frac(n: int, d: int) -> str:
    return f"{n} of {d}"


def sel(cond=None, phase=None, family=None, task=None, seed=None, phases=None):
    out = []
    for r in rows:
        if cond and r["condition"] != cond:
            continue
        if phase and r["phase"] != phase:
            continue
        if phases and r["phase"] not in phases:
            continue
        if family and r["family"] != family:
            continue
        if task and r["task_id"] != task:
            continue
        if seed is not None and r["seed"] != seed:
            continue
        out.append(r)
    return out


def p1(rs):
    return sum(1 for r in rs if r["pass_at_1"])


def p2(rs):
    return sum(1 for r in rs if r["pass_at_2"])


PRIMARY = ("similar", "transfer")
NAV = [("results", "Results"), ("method", "Method"), ("tasks", "Tasks"), ("memory", "Memory"), ("proof", "Proof"), ("journey", "Journey"), ("limits", "Limits")]
EXTRA_NAV = [("milestones", "Milestones")]  # top-level pages outside the Previous/Next chain, so no existing page's pager changes
PAGES = {s: n for s, n in NAV + EXTRA_NAV}

# ---------------------------------------------------------------------------------------------------------------- chrome
MARK = '<svg class="brand-mark" viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><path d="M12 2c1.2 4.6 3 6.4 7.6 7.6-4.6 1.2-6.4 3-7.6 7.6-1.2-4.6-3-6.4-7.6-7.6C9 8.4 10.8 6.6 12 2Z" fill="currentColor"/><circle cx="19" cy="19" r="2" fill="currentColor" opacity=".6"/></svg>'
MARK_SM = '<svg viewBox="0 0 24 24" width="20" height="20" aria-hidden="true"><path d="M12 2c1.2 4.6 3 6.4 7.6 7.6-4.6 1.2-6.4 3-7.6 7.6-1.2-4.6-3-6.4-7.6-7.6C9 8.4 10.8 6.6 12 2Z" fill="currentColor"/></svg>'


def head(title: str, desc: str, slug: str) -> str:
    return f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{e(title)} — Lucifer Lab</title>
<meta name="description" content="{e(desc)}">
<meta name="theme-color" content="#0d0c11">
<meta property="og:type" content="website">
<meta property="og:title" content="{e(title)} — Lucifer Lab">
<meta property="og:description" content="{e(desc)}">
<meta name="twitter:card" content="summary">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Geist:wght@400;500;600&family=Geist+Mono:wght@400;500&family=Instrument+Serif:ital@0;1&display=swap" rel="stylesheet">
<link rel="stylesheet" href="styles.css">
</head>
<body data-page="{slug}">
<a class="skip" href="#main">Skip to content</a>
<div class="progress" aria-hidden="true"><i></i></div>
'''


def nav(slug: str) -> str:
    cur = ' aria-current="page"'
    links = "\n".join(f'      <li><a href="{s}.html"{cur if s == slug else ""}>{n}</a></li>' for s, n in NAV + EXTRA_NAV)
    return f'''<header class="nav-wrap">
  <nav class="nav" aria-label="Main">
    <a class="brand" href="index.html" aria-label="Lucifer Lab, home">
      {MARK}
      <span>Lucifer Lab</span>
    </a>
    <ul class="nav-links" id="nav-links">
{links}
    </ul>
    <a class="btn btn-light nav-cta" href="{REPO}" rel="noopener">View code</a>
    <button class="menu-btn" type="button" aria-expanded="false" aria-controls="nav-links" aria-label="Open menu">
      <span></span><span></span>
    </button>
  </nav>
</header>
'''


def footer() -> str:
    pages = "".join(f'<li><a href="{s}.html">{n}</a></li>' for s, n in NAV + EXTRA_NAV)
    return f'''<footer class="footer">
  <div class="wrap foot-in">
    <div class="brand">{MARK_SM}<span>Lucifer Lab</span></div>
    <p>Built by Lakshit Mathur. A personal research project, open source.</p>
    <ul>
      <li><a href="index.html">Home</a></li>{pages}
      <li><a href="index.html#faq">FAQ</a></li>
      <li><a href="{REPO}" rel="noopener">GitHub</a></li>
    </ul>
  </div>
</footer>
<script src="script.js" defer></script>
</body>
</html>
'''


def hero(slug: str, kicker: str, h1: str, lede: str, toc: list[tuple[str, str]]) -> str:
    chips = "".join(f'<a href="#{i}">{e(t)}</a>' for i, t in toc)
    return f'''<section class="phero">
  <div class="sky" aria-hidden="true"><div class="sky-glow" data-depth="14"></div><div class="orbs"><i class="orb o1" data-depth="30"></i><i class="orb o3" data-depth="40"></i></div></div>
  <div class="wrap phero-in">
    <p class="crumbs"><a href="index.html">Lucifer Lab</a><span>/</span><span>{e(PAGES[slug])}</span></p>
    <p class="kicker-pill">{e(kicker)}</p>
    <h1 data-split>{h1}</h1>
    <p class="lede">{lede}</p>
    <nav class="chips-nav" aria-label="On this page">{chips}</nav>
  </div>
</section>
'''


def block(id_: str, title: str, intro: str, inner: str, alt: bool = False) -> str:
    intro_html = f"<p>{intro}</p>" if intro else ""
    return f'''<section class="block{' block-alt' if alt else ''}" id="{id_}">
  <div class="wrap">
    <div class="block-head reveal"><h2>{title}</h2>{intro_html}</div>
{inner}
  </div>
</section>
'''


def pager(slug: str) -> str:
    if slug in dict(EXTRA_NAV):
        back = f'<a class="card pg" href="limits.html"><small>← Previous</small><b>Limits</b><span>What this does not show, and how to help</span></a>'
        code = f'<a class="card pg pg-next" href="{REPO}" rel="noopener"><small>Next →</small><b>The code</b><span>Open the repository</span></a>'
        return f'<section class="block"><div class="wrap pager">{back}{code}</div></section>\n'
    order = [s for s, _ in NAV]
    i = order.index(slug)
    prev = order[i - 1] if i > 0 else None
    nxt = order[i + 1] if i < len(order) - 1 else None
    blurb = {
        "results": "Every number, with counts",
        "method": "How the test is built and scored",
        "tasks": "All 30 tasks, hidden tests and outcomes",
        "memory": "The store, the chain, the audit",
        "proof": "Recompute it in your browser",
        "journey": "What was tried, caught and fixed",
        "limits": "What this does not show, and how to help",
    }
    a = f'<a class="card pg" href="{prev}.html"><small>← Previous</small><b>{PAGES[prev]}</b><span>{blurb[prev]}</span></a>' if prev else '<a class="card pg" href="index.html"><small>← Back</small><b>Home</b><span>The short version</span></a>'
    b = f'<a class="card pg pg-next" href="{nxt}.html"><small>Next →</small><b>{PAGES[nxt]}</b><span>{blurb[nxt]}</span></a>' if nxt else f'<a class="card pg pg-next" href="{REPO}" rel="noopener"><small>Next →</small><b>The code</b><span>Open the repository</span></a>'
    return f'<section class="block"><div class="wrap pager">{a}{b}</div></section>\n'


def write(slug: str, title: str, desc: str, kicker: str, h1: str, lede: str, toc, body: str) -> None:
    out = head(title, desc, slug) + nav(slug) + "<main id=\"main\">\n" + hero(slug, kicker, h1, lede, toc) + body + pager(slug) + "</main>\n" + footer()
    (SITE / f"{slug}.html").write_text(out)
    print("wrote", f"{slug}.html", len(out) // 1024, "KB")


def table(head_cells: list[str], body_rows: list[list[str]], cls: str = "dt", min_w: int = 520) -> str:
    th = "".join(f"<th>{c}</th>" for c in head_cells)
    trs = "".join("<tr" + (' class="hot"' if r and r[0].startswith("§") else "") + ">" + "".join(f"<td>{c.lstrip('§')}</td>" for c in r) + "</tr>" for r in body_rows)
    return f'<div class="table-wrap reveal"><table class="{cls}" style="min-width:{min_w}px"><thead><tr>{th}</tr></thead><tbody>{trs}</tbody></table></div>'


def meter(n: int, d: int, hot: bool = False) -> str:
    w = round(100 * n / d) if d else 0
    return f'<span class="cellmeter{" hot" if hot else ""}"><b>{n}<small>/{d}</small></b><span class="meter"><i style="--w:{w}%"></i></span><em>{w}%</em></span>'


def spec_html(spec: str) -> str:
    """A task spec with its backticked names shown as inline code."""
    return re.sub(r"`([^`]+)`", r"<code>\1</code>", e(spec))


def code(s: str, cls: str = "") -> str:
    return f'<pre class="{cls}"><code>{e(s)}</code></pre>'


# ---------------------------------------------------------------------------------------------------------------- numbers
N = {}
for c in CONDS:
    prim = sel(c, phases=PRIMARY)
    N[c] = dict(prim_n=len(prim), prim_p1=p1(prim), prim_p2=p2(prim))
assert N["lucifer"]["prim_p1"] == 45 and N["baseline"]["prim_p1"] == 0 and N["irrelevant"]["prim_p1"] == 0, N
seeds = sorted({r["seed"] for r in rows})
conv = [t for t in TASKS if t.set == "convention"]
assert len(conv) == 30 and len(rows) == 630
GENS = sum(r["attempts"] for r in rows)
RETRIED = sum(1 for r in rows if r["attempts"] > 1)
assert (GENS, RETRIED) == (1115, 485)


def mean(xs):
    return st.mean(xs) if xs else 0.0


# ================================================================================================================ RESULTS
def build_results() -> None:
    kp = f'''<div class="kpis">
  <div class="kpi reveal"><small>First-try success, similar + transfer</small><b>{pct(N["lucifer"]["prim_p1"], 90)}</b><span>Lucifer · {frac(N["lucifer"]["prim_p1"], 90)} task runs: similar {pct(p1(sel("lucifer", "similar")), 60)}, transfer {pct(p1(sel("lucifer", "transfer")), 30)}<br>No memory: {frac(0, 90)} · Wrong notes: {frac(0, 90)}</span></div>
  <div class="kpi reveal"><small>Gain over no memory</small><b>+0.50</b><span>95% interval +0.30 to +0.70, paired bootstrap over 18 tasks</span></div>
  <div class="kpi reveal"><small>After one retry</small><b>{pct(N["lucifer"]["prim_p2"], 90)}</b><span>No memory {pct(N["baseline"]["prim_p2"], 90)} · Wrong notes {pct(N["irrelevant"]["prim_p2"], 90)}</span></div>
</div>
<div class="callout reveal"><b>Terms.</b> A <b>task run</b> is one task given to the model once for one condition and seed, with at most one retry. There are 630 of them, and the model was called {GENS:,} times counting retries. <b>First try</b> (pass@1) is the first answer of a task run. When a table says “out of 60”, it means 60 task runs.</div>
<div class="prose reveal"><p>The <strong>primary metric</strong> was fixed before the run: pass@1, meaning the very first answer passes every hidden test, on the <em>similar</em> and <em>transfer</em> tasks. That is 18 tasks, each tried on 5 seeds, so 90 attempts per condition. A retry is allowed afterwards, with the failing test's message, but it does not count for pass@1.</p></div>'''

    # by phase
    phase_desc = {
        "experience": ("Experience", "Tasks the model works through first. Lucifer and Wrong notes write lessons here, so memory is still filling up. Not part of the primary metric."),
        "similar": ("Similar", "New tasks that need the same convention as an experience task. Memory is frozen. <b>Primary.</b>"),
        "transfer": ("Transfer", "New tasks that combine conventions, sometimes with a prefix not seen before. Memory is frozen. <b>Primary.</b>"),
        "replay": ("Replay", "The experience tasks again, memory frozen. Shows what was kept. A high score here is memorisation."),
    }
    body = []
    for ph in PHASES:
        cells = [f"<b>{phase_desc[ph][0]}</b><br><small>{phase_desc[ph][1]}</small>"]
        for c in CONDS:
            rs = sel(c, ph)
            cells.append(meter(p1(rs), len(rs), c == "lucifer"))
        body.append(cells)
    t_phase = table(["Phase", "No memory", "Lucifer", "Wrong notes"], body, "dt dt-wide", 680)
    ex_irr = p1(sel("irrelevant", "experience"))
    notes_phase = f'''<div class="callout warn reveal"><b>Worth noticing.</b> In the experience phase Wrong notes solved {ex_irr} of 60 on the first try, while No memory solved 0. In the evaluation phases it solved {p1(sel("irrelevant", phases=PRIMARY))} of 90. So irrelevant notes can leak a little useful information while memory is small and every lesson is short, which is a reason the primary metric is measured on frozen memory and why the control is reported, not hidden.</div>'''

    # by family
    fam_info = {
        "ident": ("Identifiers", "KIND in capitals (first three letters), a hyphen, number padded to 5 digits"),
        "price": ("Prices", "₹, thousands separators, two decimals; refunds and discounts get a leading minus"),
        "date": ("Dates", "DD-Mon-YYYY, for example 05-Mar-2026"),
        "errors": ("Error messages", "ValueError with “invalid &lt;noun&gt;: &lt;input as given&gt;”"),
    }
    frow = []
    for f, (name, conv_txt) in fam_info.items():
        l, b, i = sel("lucifer", "similar", f), sel("baseline", "similar", f), sel("irrelevant", "similar", f)
        frow.append([f"<b>{name}</b><br><small>{conv_txt}</small>", meter(p1(l), len(l), True), meter(p2(l), len(l)), meter(p1(b), len(b)), meter(p2(b), len(b)), meter(p2(i), len(i))])
    t_fam = table(["Hidden convention", "Lucifer · first try", "Lucifer · after retry", "No memory · first try", "No memory · after retry", "Wrong notes · after retry"], frow, "dt dt-wide", 820)
    idl = sel("lucifer", "similar", "ident")
    id4 = sel("lucifer", task="ident-4", phase="similar")
    id6 = sel("lucifer", task="ident-6", phase="similar")
    fam_notes = f'''<div class="prose reveal">
<p>Memory worked best where the lesson is a single, unambiguous example: <strong>dates and error messages were solved first try on all 15 attempts</strong> by Lucifer. It was weakest on identifiers ({frac(p1(idl), len(idl))}). The identifier tasks <code>shipment_id</code> and <code>ticket_id</code> were never solved first try ({frac(p1(id4), 5)} and {frac(p1(id6), 5)} seeds), although all five seeds passed them after the retry. The earlier lessons show <code>ORD-</code>, <code>INV-</code> and <code>CUS-</code>, so a model has to infer “first three letters of the kind”, and <code>SHP</code> or <code>TKT</code> are natural-looking alternatives. That is a reading of the numbers, not a tested cause; it is listed on the Limits page as a task-design question.</p>
<p>Look also at the “No memory · after retry” column. Error messages are hard even with feedback ({pct(p2(sel("baseline", "similar", "errors")), 15)} after one retry), which is where Lucifer's lessons help most.</p></div>'''

    # transfer tasks
    mixed_desc = {
        "mixed-11": "identifier + price",
        "mixed-12": "identifier + price + date",
        "mixed-13": "identifier + refund price",
        "mixed-14": "new identifier prefix (REC) + date",
        "mixed-15": "identifier + error message, new noun",
        "mixed-16": "price only, as a “Total:” line",
    }
    trow = []
    for tid, d in mixed_desc.items():
        t = BY_ID[tid]
        l, b, i = sel("lucifer", task=tid), sel("baseline", task=tid), sel("irrelevant", task=tid)
        trow.append([f"<a href=\"tasks.html#{tid}\"><code>{t.entry}</code></a><br><small>{d}</small>", meter(p1(l), 5, True), meter(p2(l), 5), meter(p1(b), 5), meter(p2(b), 5), meter(p2(i), 5)])
    t_xfer = table(["Transfer task", "Lucifer · first try", "Lucifer · after retry", "No memory · first try", "No memory · after retry", "Wrong notes · after retry"], trow, "dt dt-wide", 820)
    xfer_note = f'''<div class="prose reveal"><p>Transfer is the weak spot: Lucifer solved {frac(p1(sel("lucifer", "transfer")), 30)} first try ({pct(p1(sel("lucifer", "transfer")), 30)}). Five of the six transfer tasks needed two or three conventions at once, or a prefix not seen in any lesson. Four of those were never solved first try and one was solved on 1 of 5 seeds. The one that needed a single convention (<code>total_line</code>, prices) was solved on 4 of 5 seeds. After one retry Lucifer reaches {pct(p2(sel("lucifer", "transfer")), 30)} on transfer, against {pct(p2(sel("baseline", "transfer")), 30)} for No memory.</p></div>'''

    # per seed
    srow = []
    for s in seeds:
        cells = [f"<b>Seed {s}</b>"]
        for c in CONDS:
            rs = sel(c, phases=PRIMARY, seed=s)
            cells.append(meter(p1(rs), 18, c == "lucifer"))
        cells.append(meter(p2(sel("lucifer", phases=PRIMARY, seed=s)), 18))
        srow.append(cells)
    t_seed = table(["Seed", "No memory · first try", "Lucifer · first try", "Wrong notes · first try", "Lucifer · after retry"], srow, "dt dt-wide", 720)
    lp = [p1(sel("lucifer", phases=PRIMARY, seed=s)) for s in seeds]
    seed_note = f'<div class="prose reveal"><p>Each seed reshuffles the order of the experience tasks and the sampling of the model. Lucifer solved {", ".join(map(str, lp))} of 18 first try across the five seeds, never fewer than {min(lp)} and never more than {max(lp)}. The two controls solved 0 in every seed. Five seeds is thin, but the direction did not change once.</p></div>'

    # retry
    rrow = []
    for c in CONDS:
        cells = [f"<b>{CNAME[c]}</b>"]
        for ph in ("similar", "transfer"):
            rs = sel(c, ph)
            cells.append(meter(p1(rs), len(rs), c == "lucifer"))
            cells.append(meter(p2(rs), len(rs)))
        pr = sel(c, phases=PRIMARY)
        cells.append(meter(p2(pr), len(pr), c == "lucifer"))
        rrow.append(cells)
    t_retry = table(["Condition", "Similar · first", "Similar · after retry", "Transfer · first", "Transfer · after retry", "Both · after retry"], rrow, "dt dt-wide", 820)
    retry_note = f'<div class="callout reveal"><b>How to read this.</b> The conventions are hidden, so No memory was not expected to pass first try, and did not ({frac(0, 210)} task runs in the whole run). But it can fix the mistake once it sees the failing test: {pct(N["baseline"]["prim_p2"], 90)} pass after one retry. What memory buys is skipping the failed first try. After a retry the gap is about 30 points (82% against 52%), not 50.</div>'

    # cost
    crow = []
    for c in CONDS:
        rs = sel(c)
        crow.append([f"<b>{CNAME[c]}</b>", f"{round(mean([r['prompt_tokens'] for r in rs]))}", f"{round(mean([r['completion_tokens'] for r in rs]))}", f"<b>{round(mean([r['prompt_tokens'] + r['completion_tokens'] for r in rs]))}</b>", f"{mean([r['attempts'] for r in rs]):.2f}", f"{mean([r['wall_ms'] for r in rs]) / 1000:.0f} s", f"{sum(r['wall_ms'] for r in rs) / 3.6e6:.1f} h"])
    t_cost = table(["Condition", "Prompt tokens / task", "Completion tokens / task", "Total tokens / task", "Attempts / task", "Wall time / task", "Wall time, all 210"], crow, "dt dt-wide", 860)
    cost_note = f'<div class="prose reveal"><p>Wrong notes cost the most tokens ({round(mean([r["prompt_tokens"] + r["completion_tokens"] for r in sel("irrelevant")]))} per task), almost twice Lucifer, and bought nothing on the primary metric. Lucifer wrote shorter answers and needed fewer retries, so it was also the fastest on the runner ({sum(r["wall_ms"] for r in sel("lucifer")) / 3.6e6:.1f} hours of model time across its 210 tasks, against {sum(r["wall_ms"] for r in sel("baseline")) / 3.6e6:.1f} for No memory). These are 4-CPU runner timings with a 14B model; they say little about a GPU.</p></div>'

    # retrieval
    rv = []
    for c in ("lucifer", "irrelevant"):
        for ph in ("similar", "transfer", "replay"):
            rs = sel(c, ph)
            rv.append([f"<b>{CNAME[c]}</b>", ph.capitalize(), f"{sum(1 for r in rs if r['lessons_shown'])} of {len(rs)}", f"{mean([len(r['lessons_shown']) for r in rs]):.2f}"])
    t_ret = table(["Condition", "Phase", "Attempts shown at least one lesson", "Lessons shown, average (max 3)"], rv, "dt", 560)

    # gates
    g = f'''<div class="gates-detail">
  <article class="card reveal"><span class="chip chip-ok">Pass</span><h3>Gate 1 · Improvement</h3><p>The 95% interval of (Lucifer − baseline) on the primary metric must sit above zero, <em>and</em> so must (Lucifer − wrong notes).</p><div class="kv"><span>Lucifer − baseline</span><b>+0.50</b></div><div class="kv"><span>95% interval</span><b>+0.30 … +0.70</b></div><div class="kv"><span>Lucifer − wrong notes</span><b>+0.50</b></div><div class="kv"><span>95% interval</span><b>+0.30 … +0.70</b></div></article>
  <article class="card reveal"><span class="chip chip-mid">Inconclusive</span><h3>Gate 2 · Retention</h3><p>On tasks the baseline reliably solves (at least 80%, chosen on half the seeds), Lucifer may lose at most 5 points on the other half.</p><div class="kv"><span>Tasks the baseline masters</span><b>0</b></div><div class="kv"><span>Mean drop</span><b>+0.00</b></div><p class="foot">With nothing mastered there is nothing to lose, so this gate cannot be passed or failed here. It is reported as inconclusive, not as a pass.</p></article>
  <article class="card reveal"><span class="chip chip-ok">Pass</span><h3>Gate 3 · Auditability</h3><p>Every memory store must verify its hash chain, reproduce an earlier version after a rollback, and give every lesson provenance.</p><div class="kv"><span>Stores audited</span><b>{len(audits)}</b></div><div class="kv"><span>All three checks</span><b>{sum(1 for a in audits if a["ok"])} of {len(audits)}</b></div><p class="foot"><a href="memory.html#audit">See the audit table →</a></p></article>
</div>
<div class="callout warn reveal"><b>The overall verdict is “not passed”.</b> The workflow's own report ends with “All three gates: NOT passed”, because gate 2 is inconclusive. Gate 1, the question this version set out to answer, passed. The site does not round that up.</div>'''

    # data
    files = [("report.txt", "The text report and gate verdicts"), ("rows.json", "One row per task run (630 rows)"), ("audits.json", "The memory audits (10 stores)"), ("meta.json", "Model, seeds, settings")]
    drows = []
    for fn, d in files:
        sz = (RUN / fn).stat().st_size
        drows.append([f'<a href="data/{fn}" download><code>{fn}</code></a>', d, f"{sz / 1024:.1f} KB" if sz > 1024 else f"{sz} B"])
    t_data = table(["File", "What is in it", "Size"], drows, "dt", 520)
    fields = '<div class="prose reveal"><p>Each row of <code>rows.json</code> holds: <code>run_id</code>, <code>trace_id</code>, <code>seed</code>, <code>condition</code>, <code>phase</code>, <code>task_id</code>, <code>family</code>, <code>pass_at_1</code>, <code>pass_at_2</code>, <code>attempts</code>, <code>lessons_shown</code> (the ids of the lessons put in the prompt), <code>prompt_tokens</code>, <code>completion_tokens</code>, <code>wall_ms</code> and <code>memory_version</code>. Everything on this page is a count or average over those rows. The same files are committed in the repository as <a href="%s/tree/main/results/published/qwen14b-convention" rel="noopener">results/published/qwen14b-convention</a> (commit <code>%s</code>), written by the workflow run, not by hand.</p><p><a class="btn btn-light" href="proof.html#recompute">Recompute the headline in your browser →</a></p></div>' % (REPO, COMMIT)

    body = (
        block("headline", "The headline, with its counts", "", kp)
        + block("phase", "By phase", "The same three conditions across the four phases of a run. Each cell shows first-try passes out of attempts.", t_phase + notes_phase, True)
        + block("family", "By hidden convention", "The 12 similar tasks are three each of four conventions. Five seeds each makes 15 attempts per family and condition.", t_fam + fam_notes)
        + block("transfer", "Transfer, task by task", "Six tasks that combine what was learned. This is the hardest test of whether memory generalises.", t_xfer + xfer_note, True)
        + block("seeds", "Seed by seed", "Whether the result holds on each independent run, not just on the average.", t_seed + seed_note)
        + block("retry", "First try against after one retry", "Every condition gets one retry with the failing test's output, so No memory is not handicapped.", t_retry + retry_note, True)
        + block("cost", "What it cost", "Tokens and time per task, averaged over all phases.", t_cost + cost_note)
        + block("retrieval", "What memory actually showed the model", "How many lessons were put into the prompt. Lucifer picks the three most relevant, Wrong notes the three least relevant.", t_ret, True)
        + block("gates", "The three gates, in detail", "Rules fixed before the run. The numbers come from the workflow's own report.", g)
        + block("data", "The raw data", "Download the files this page was built from.", t_data + fields, True)
    )
    write("results", "Results", "The full Version 1 result of Lucifer Lab: first-try and after-retry success by phase, family, task and seed, cost, retrieval and the three gates, all computed from the published rows.", "Results",
          "Every number from the first real run, <em>with the counts behind it.</em>",
          "One model, 30 hidden-convention tasks, 5 seeds, 3 conditions: 630 task runs and 1,115 model generations counting retries. Nothing here is typed in by hand: this page is generated from the published rows.",
          [("headline", "Headline"), ("phase", "By phase"), ("family", "By convention"), ("transfer", "Transfer"), ("seeds", "Seeds"), ("retry", "Retry"), ("cost", "Cost"), ("retrieval", "Retrieval"), ("gates", "Gates"), ("data", "Raw data")], body)


# ================================================================================================================ METHOD
def build_method() -> None:
    q = '''<div class="prose reveal"><p>The one claim: <strong>an ordinary open-weight language model, given persistent memory of its own earlier attempts and a feedback signal, solves later, related tasks at a higher rate than the same model without them.</strong> A “no” would have been a valid result and would have been published. Everything else (other mechanisms, training, bigger systems) waits until this has a measured answer.</p></div>'''

    cond = table(["", "Writes lessons", "Reads at evaluation", "What it is for"], [
        ["<b>A · No memory</b>", "no", "nothing", "The honest starting line."],
        ["<b>B · Lucifer</b>", "yes, in the experience phase", "the 3 most relevant lessons", "The thing being tested."],
        ["<b>C · Wrong notes</b>", "yes, the same way", "the 3 least relevant lessons", "The control that matters most. If B beat A but not C, the gain would come from a longer prompt, not from learning."],
    ], "dt", 640)
    cond_note = '<div class="prose reveal"><p>All three get the same model, the same prompts, the same tasks in the same order within a seed, and the same single retry. Memory is built fresh for every seed and condition, so nothing leaks between runs.</p></div>'

    ph = table(["Phase", "Tasks", "Per condition and seed", "Memory"], [
        ["<b>1 · Experience</b>", "12, in a seeded random order", "12 task runs", "Written to (Lucifer and Wrong notes)"],
        ["<b>2 · Similar</b>", "12 new tasks, same convention as an experience task", "12", "Read-only"],
        ["<b>3 · Transfer</b>", "6 new tasks that combine conventions", "6", "Read-only"],
        ["<b>4 · Replay</b>", "the 12 experience tasks again", "12", "Read-only"],
    ], "dt", 640)
    ph_note = f'<div class="prose reveal"><p>That is 42 task runs per condition and seed. Over 5 seeds and 3 conditions: 42 × 5 × 3 = <strong>630 task runs</strong>. A task run is one task given to the model once, with at most one retry. {RETRIED} of the 630 needed the retry, so the model was called {GENS:,} times in all. The evaluation order is shuffled once per seed and is the same for all three conditions. Learning happens only in phase 1; in phases 2 to 4 memory is frozen, so nothing can be learned from the exam itself.</p></div>'

    why = f'''<div class="grid-2">
<article class="card reveal"><h3>Why the conventions are hidden</h3><p>The first exam used fully specified tasks and strong models scored 96 to 100% with no memory, so it could show nothing. Memory can only help where the model cannot be expected to know something up front but can learn it from feedback, like a house format or an exact error message. So each convention task gives a natural spec that leaves the convention out, and only the failing test reveals it. A model could in principle guess a convention right; the baseline never did (0 of 210 task runs).</p></article>
<article class="card reveal"><h3>What “hidden” looks like</h3><p>The spec for <code>order_id</code> is just “returns the identifier of order number n”. The tests expect <code>'ORD-00007'</code>. Nothing in the spec says the prefix or the padding. A test (<code>test_convention_tasks_hide_their_convention_from_the_spec</code>) checks that no convention task leaks its convention into the spec.</p><p class="foot"><a href="tasks.html">Browse all 30 tasks →</a></p></article>
</div>'''

    fam = table(["Family", "Convention", "Experience", "Similar", "Transfer"], [
        ["Identifiers", "<code>KIND-00007</code>: first three letters of the kind in capitals, a hyphen, five digits", "3", "3", "in mixed tasks"],
        ["Prices", "<code>₹1,234.56</code>: whole cents, rupee sign, separators, two decimals; refunds <code>-₹25.00</code>", "3", "3", "in mixed tasks"],
        ["Dates", "<code>05-Mar-2026</code>: two-digit day, three-letter month, four-digit year", "3", "3", "in mixed tasks"],
        ["Error messages", "<code>ValueError('invalid age: abc')</code>: “invalid”, the noun, a colon, the input as given", "3", "3", "in mixed tasks"],
        ["Mixed (transfer)", "one line combining two or three of the above, or a new prefix", "–", "–", "6"],
    ], "dt", 760)
    fam_note = '<div class="prose reveal"><p>This run used the 30 <em>convention</em> tasks (12 experience, 12 similar, 6 transfer). The lab also holds 50 older <em>pitfall</em> tasks (fully specified, with traps like off-by-one ranges). They were used to build and calibrate the harness and are not part of this result.</p></div>'

    steps = f'''<ol class="pipe reveal">
<li><b>retrieve_memory</b><span>Lucifer: the top 3 lessons for this task. Wrong notes: the 3 least relevant. No memory: none.</span></li>
<li><b>build_prompt</b><span>If there are lessons, they are placed first under a short header, then the task.</span></li>
<li><b>attempt 1</b><span>The model writes a function (seeded, so the run can be repeated). The sandbox runs the hidden tests in a separate process.</span></li>
<li><b>attempt 2, only if attempt 1 failed</b><span>The previous code and the failing test's message are appended. Every condition gets exactly this one retry.</span></li>
<li><b>memory.write, experience phase only</b><span>A failed first try writes a failure lesson. A failure fixed on the retry also writes a fix lesson.</span></li>
<li><b>one row is recorded</b><span>First-try pass, pass after retry, attempts, tokens, time, which lessons were shown. Plus a trace of every step.</span></li>
</ol>'''

    prompts = f'''<div class="grid-2">
<article class="card reveal"><h3>The task prompt</h3>{code("Write a Python function `order_id`.\n\n`order_id(n)` returns the identifier of order number n.\n\nReply with the complete function in one ```python code block and nothing else.")}</article>
<article class="card reveal"><h3>With lessons from memory</h3>{code(NOTES_HEADER + chr(10) + "- <lesson 1>" + chr(10) + "- <lesson 2>" + chr(10) + "- <lesson 3>" + chr(10) + chr(10) + "<the task prompt above>")}</article>
<article class="card reveal"><h3>The retry prompt</h3>{code("<the prompt above>\n\n" + RETRY_MARKER + "\n```python\n<the previous code>\n```\n<the failing test's message>\nReply with the corrected function in one ```python code block.")}</article>
<article class="card reveal"><h3>The two kinds of lesson</h3>{code("failure:  A first attempt at '<function>' failed.\n          The spec said: <spec> <the failing test's message>\n\nfix:      For '<function>' (<spec>) this version passed after a\n          failed first attempt:\n          <the passing code, first 500 characters>")}</article>
</div>
<div class="prose reveal"><p>These are the exact templates from <code>src/lucifer/agent.py</code>. Lessons are plain text; the model is told they “may or may not apply”.</p></div>'''

    retr = f'''<div class="prose reveal"><p>Lucifer picks lessons with plain <strong>TF-IDF cosine similarity over words</strong>: no neural model, no download. The query is the task's spec plus its function name; each lesson is a document; stop words are dropped. Lessons scoring below <code>0.08</code> are not shown, and at most <strong>k = 3</strong> are. Ties go to the newer lesson.</p>
<p>The control reverses the ranking: Wrong notes shows the three lessons that match the task <em>least</em>. Random picks were tried first and were often relevant by luck in a small memory, which would have blurred the comparison. Simple word matching was as good as anything tried (word pairs, stemming); semantic retrieval is listed as future work.</p></div>
<div class="grid-2"><article class="card reveal"><h3>Retrieval in one function</h3>{code("def relevant(query, lessons, k=3, min_score=0.08):\n    # idf = log((n + 1) / (docs_with_word + 1)) + 1\n    # score = cosine(tfidf(query), tfidf(lesson))\n    # sort by (-score, -version); keep score >= min_score\n    return top_k_lessons")}</article><article class="card reveal"><h3>The control, in one line</h3>{code("def least_relevant(query, lessons, k=3):\n    ranked = relevant(query, lessons, k=len(lessons), min_score=-1.0)\n    return ranked[::-1][:k]   # the k worst matches")}</article></div>'''

    sandbox = '''<div class="prose reveal"><p>Model code is run by <code>SandboxExecutor</code> in a <strong>separate Python process</strong> in a throw-away folder with an empty environment, a 5-second CPU limit and a 1 MB file limit (8 seconds wall time). The candidate is compiled once, then each hidden check is executed in turn. The first failing check is reported to the model as <code>this check failed: &lt;the assert&gt; (&lt;the error&gt;)</code>, at most 400 characters. Code is taken from the first fenced block of the reply.</p>
<p>This is hygiene, <strong>not a security boundary</strong>: model code could still reach the network or files. These tasks are tiny and the run was on a throw-away CI runner. Anything at larger scale needs a container.</p></div>'''

    stats = f'''<div class="prose reveal"><p>The unit of analysis is the <strong>task</strong>, not the attempt. For each of the 18 primary tasks the first-try result is averaged over its seeds, giving one number per task and condition. The effect is the mean over tasks of (Lucifer − baseline). The interval comes from a <strong>paired bootstrap</strong>: resample the 18 task differences with replacement 10,000 times and take the 2.5th and 97.5th percentiles. Resampling tasks (not attempts) is the cautious choice: seeds of the same task are not independent evidence.</p>
<p>The result is +0.50 with a 95% interval of +0.30 to +0.70. You can <a href="proof.html#recompute">run this bootstrap in your own browser</a> on the published rows.</p></div>
<div class="grid-3">
<article class="card reveal"><h3>Gate 1 · Improvement</h3><p>Both intervals, (Lucifer − baseline) and (Lucifer − wrong notes), above zero. “Hurts” is declared if the baseline comparison sits entirely below zero.</p></article>
<article class="card reveal"><h3>Gate 2 · Retention</h3><p>Tasks the baseline solves at least 80% of the time on half of the seeds are picked; Lucifer may lose at most 5 points on them on the <em>other</em> half. Picking and measuring on the same runs fakes “forgetting” (regression to the mean), a bug the dashboard exposed.</p></article>
<article class="card reveal"><h3>Gate 3 · Auditability</h3><p>The hash chain verifies, rolling back to the middle and forward again reproduces the same history on a copy, and every lesson has provenance (task, run, seed, version).</p></article>
</div>'''

    fair = table(["Control", "How it is done", "Where it is tested"], [
        ["Same exam for all conditions", "One shuffled evaluation order per seed, shared by all three", "<code>test_every_condition_sees_the_same_tasks_in_the_same_order</code>"],
        ["Baseline never touches memory", "No store is created for it", "<code>test_baseline_never_reads_or_writes_memory</code>"],
        ["No learning from the exam", "Memory is read-only after the experience phase", "<code>test_memory_is_frozen_during_evaluation</code>"],
        ["Repeatable", "Seeds are explicit; model and tool versions are pinned", "<code>test_same_inputs_give_the_same_results</code>"],
        ["Tasks can tell right from wrong", "Every task has a reference answer that passes and a plausible naive answer that fails", "<code>test_reference_passes_and_naive_fails</code>"],
        ["Seeds can be merged safely", "Overlapping seeds, or runs of different settings, are refused", "<code>test_overlapping_seeds_are_refused</code>, <code>test_runs_of_different_experiments_are_refused</code>"],
    ], "dt", 760)

    infra = f'''<div class="prose reveal"><p>Nothing heavy runs on a laptop. The experiment is a GitHub Actions workflow (<code>experiment.yml</code>): one parallel job per seed on a CPU runner (4 vCPU, no GPU), each installing a pinned Ollama and pulling the model, then a merge job that joins the seeds, runs the report and the gates, and optionally commits the result files. The run behind this site is <a href="{REPO}/actions/runs/{RUN_ID}" rel="noopener">workflow run {RUN_ID}</a>; the published files are in commit <code>{COMMIT}</code>.</p></div>
{table(["Setting", "Value"], [["Model", f"<code>qwen2.5-coder:14b</code> (via Ollama, backend <code>{e(meta['backend'])}</code>)"], ["Temperature", "0.7"], ["Seeds", ", ".join(map(str, meta["seeds"]))], ["Lessons shown per task (k)", str(meta["k"])], ["Retries", str(meta["retries"])], ["Tasks", f"{meta['tasks']} convention tasks"], ["Task runs", str(len(rows))], ["Model generations, including retries", f"{GENS:,}"]], "dt", 420)}'''

    body = (
        block("question", "The question", "", q)
        + block("conditions", "Three ways to prepare", "Same model, same exam. The only thing that differs is what the model may remember.", cond + cond_note, True)
        + block("phases", "Four phases of a run", "Every condition and seed goes through the same four phases with a fresh memory.", ph + ph_note)
        + block("exam", "The exam", "Hidden conventions only feedback can reveal.", why + fam + fam_note, True)
        + block("solve", "One task, step by step", "What happens every time the model is asked to solve a task. This is the <code>_solve</code> function in <code>experiment.py</code>.", steps)
        + block("prompts", "The exact prompts", "", prompts, True)
        + block("retrieval", "How lessons are found", "", retr)
        + block("referee", "The referee", "How an answer is marked.", sandbox, True)
        + block("stats", "Statistics and the three gates", "", stats)
        + block("controls", "Fairness controls", "Each one is enforced by an automated test in the repository.", fair, True)
        + block("infra", "Where it ran", "", infra)
    )
    write("method", "Method", "How Lucifer Lab tests AI memory fairly: three conditions, four phases, hidden-convention tasks, exact prompts, retrieval, sandbox, paired bootstrap and the three promotion gates.", "Method",
          "How the test is built, <em>and why it is fair.</em>",
          "Three conditions, four phases and an exam built so that only learning can pass it. Everything here is taken from the code that ran, including the exact prompts.",
          [("question", "Question"), ("conditions", "Conditions"), ("phases", "Phases"), ("exam", "The exam"), ("solve", "One task"), ("prompts", "Prompts"), ("retrieval", "Retrieval"), ("referee", "Referee"), ("stats", "Statistics"), ("controls", "Controls"), ("infra", "Infrastructure")], body)


# ================================================================================================================ TASKS
FAM_TXT = {
    "ident": ("Identifiers", "KIND in capitals (first three letters), a hyphen, the number padded to five digits"),
    "price": ("Prices", "₹, thousands separators, two decimals; refunds and discounts get a leading minus"),
    "date": ("Dates", "DD-Mon-YYYY, such as 05-Mar-2026"),
    "errors": ("Error messages", "ValueError: “invalid <noun>: <input as given>”"),
    "mixed": ("Transfer (mixed)", "two or three of the above in one line, or a new prefix"),
}
SPLIT_NAME = {"exp": "Experience", "sim": "Similar", "xfer": "Transfer"}
SPLIT_PHASES = {"exp": ("experience", "replay"), "sim": ("similar",), "xfer": ("transfer",)}


def dots(cond: str, phase: str, tid: str) -> str:
    out, n1, n2, n0 = [], 0, 0, 0
    for s in seeds:
        rs = [r for r in rows if r["condition"] == cond and r["phase"] == phase and r["task_id"] == tid and r["seed"] == s]
        r = rs[0]
        if r["pass_at_1"]:
            out.append('<i class="d d1"></i>'); n1 += 1
        elif r["pass_at_2"]:
            out.append('<i class="d d2"></i>'); n2 += 1
        else:
            out.append('<i class="d d0"></i>'); n0 += 1
    label = f"{CNAME[cond]}, {phase}: {n1} first try, {n2} after retry, {n0} failed"
    return f'<span class="dotrow" role="img" aria-label="{label}">{"".join(out)}</span>'


def build_tasks() -> None:
    # overview grid
    cells = []
    for t in conv:
        if t.split == "exp":
            continue
        ph = SPLIT_PHASES[t.split][0]
        n = p1(sel("lucifer", ph, task=t.id))
        cells.append(f'<a class="cell c{n}" href="#{t.id}" title="{t.entry}: Lucifer first try on {n} of 5 seeds"><b>{t.entry}</b><small>{n}/5</small></a>')
    overview = f'''<div class="prose reveal"><p>Each tile is one evaluation task. The number is how many of the 5 seeds Lucifer solved <strong>on the first try</strong>. No memory and Wrong notes scored 0 of 5 on every one of these tiles. Click a tile to jump to the task.</p></div>
<div class="heat reveal">{"".join(cells)}</div>
<div class="heat-key reveal"><span><i class="cell c0"></i>0</span><span><i class="cell c2"></i>2</span><span><i class="cell c3"></i>3–4</span><span><i class="cell c5"></i>5 of 5</span></div>'''

    famtab = table(["Family", "The hidden convention", "Tasks"], [
        [f"<b>{FAM_TXT[f][0]}</b>", e(FAM_TXT[f][1]), ", ".join(f"<a href=\"#{t.id}\"><code>{t.entry}</code></a>" for t in conv if t.family == f)] for f in FAM_TXT
    ], "dt", 700)

    chips = '<div class="filters reveal" role="group" aria-label="Filter tasks"><div><span>Phase</span>' + "".join(f'<button type="button" class="fchip{" on" if v == "all" else ""}" data-key="split" data-val="{v}">{n}</button>' for v, n in [("all", "All"), ("exp", "Experience"), ("sim", "Similar"), ("xfer", "Transfer")]) + '</div><div><span>Convention</span>' + "".join(f'<button type="button" class="fchip{" on" if v == "all" else ""}" data-key="family" data-val="{v}">{n}</button>' for v, n in [("all", "All"), ("ident", "Identifiers"), ("price", "Prices"), ("date", "Dates"), ("errors", "Errors"), ("mixed", "Mixed")]) + '</div></div>'

    legend = '<div class="legend dotkey reveal"><span><i class="d d1"></i>passed on the first try</span><span><i class="d d2"></i>passed after the retry</span><span><i class="d d0"></i>failed both</span><span class="dim">one dot per seed, seeds 0 to 4</span></div>'

    cards = []
    for t in conv:
        outs = []
        for ph in SPLIT_PHASES[t.split]:
            outs.append(f'<div class="outgroup"><small>{ph.capitalize()} phase</small>' + "".join(f'<div class="outrow"><span>{CNAME[c]}</span>{dots(c, ph, t.id)}</div>' for c in CONDS) + "</div>")
        tests = "\n".join(t.tests)
        cards.append(f'''<article class="tcard" id="{t.id}" data-split="{t.split}" data-family="{t.family}">
  <header><code class="tid">{t.id}</code><span class="chip">{FAM_TXT[t.family][0]}</span><span class="chip chip-mid">{SPLIT_NAME[t.split]}</span></header>
  <h3><code>{t.entry}</code></h3>
  <p class="tlabel">What the model is told</p>
  <blockquote>{spec_html(t.spec)}</blockquote>
  <div class="outs">{"".join(outs)}</div>
  <details><summary>Hidden tests and the two reference answers</summary>
    <p class="tlabel">The hidden tests (not shown to the model until one fails)</p>{code(tests)}
    <div class="codepair"><div><p class="tlabel">A plain answer, which fails</p>{code(t.naive, "bad")}</div><div><p class="tlabel">The reference answer, which passes</p>{code(t.reference, "good")}</div></div>
  </details>
</article>''')

    body = (
        block("overview", "All 30 tasks at a glance", "Tasks with their convention hidden. Twelve are for experience, twelve for the similar test and six for transfer.", overview)
        + block("families", "The four conventions", "", famtab, True)
        + block("explorer", "Task explorer", "Every task as it was given: what the model was told, what the hidden tests check, a plain answer that fails and the reference that passes, and what each condition did on each of the five seeds.", chips + legend + '<div class="tgrid">' + "".join(cards) + "</div>")
    )
    write("tasks", "Tasks", "Browse all 30 hidden-convention tasks of Lucifer Lab: the spec the model sees, the hidden tests, a failing plain answer, the reference answer and the per-seed outcome for each condition.", "Tasks",
          "All thirty tasks, <em>with the answers hidden in plain sight.</em>",
          "The spec the model saw, the tests it was marked against, and what each condition did on every seed. If you doubt the exam, read the exam.",
          [("overview", "At a glance"), ("families", "Conventions"), ("explorer", "Explorer")], body)


# ================================================================================================================ MEMORY
def build_memory() -> None:
    intro = '''<div class="prose reveal"><p>Memory here is deliberately plain: <strong>a small SQLite table of lessons</strong>, each linked to the one before it by a hash. Nothing about the model changes (no weights, no training). The model simply sees a few earlier lessons in its prompt. That makes the mechanism easy to inspect, and it is why the audit can be so strict.</p></div>'''

    schema = f'''<div class="grid-2">
<article class="card reveal"><h3>What a lesson holds</h3>{code("id, version, task_id, kind, text,\nrun_id, seed, parent_hash, hash\n\nkind: 'failure' or 'fix'\nversion: 1, 2, 3 ... (one per write)")}<p class="foot">Provenance is built in: every lesson records which task, run and seed produced it.</p></article>
<article class="card reveal"><h3>When one is written</h3><p>Only in the <b>experience</b> phase, and only for Lucifer and Wrong notes. A failed first try writes a <i>failure</i> lesson. A failure that was fixed on the retry writes a second, <i>fix</i> lesson containing the code that finally passed. In the evaluation phases memory is read-only.</p></article>
</div>'''

    chain = f'''<div class="prose reveal"><p>Each lesson's hash covers the hash of the lesson before it. The first lesson links to a genesis value of 64 zeros. This is the exact function from <code>memory.py</code>:</p></div>
{code("def _hash(parent, version, task_id, kind, text):\n    return sha256('|'.join([parent, str(version), task_id, kind, text])).hexdigest()")}
<div class="prose reveal"><p>Change any earlier lesson and its hash changes, so the next lesson's stored parent no longer matches, and so on down the chain. A hash chain makes edits <em>detectable when it is verified</em>. It does not make the memory impossible to change. <code>verify_chain()</code> walks the table from version 1 and returns false at the first mismatch. The tests cover both an edited and a deleted lesson (<code>test_changing_an_old_lesson_is_detected</code>, <code>test_deleting_a_lesson_is_detected</code>).</p></div>'''

    demo = '''<div class="mem-grid">
  <div class="mem-stage reveal" id="mem-stage" tabindex="0" role="group" aria-label="3D view of a hash-chained memory. Drag, or use the arrow keys, to rotate it.">
    <div class="dial" id="dial" aria-hidden="true"></div>
    <ol class="scene" id="scene"></ol>
    <p class="hint" aria-hidden="true"><span></span> Drag to rotate</p>
    <noscript><p class="nojs">The live chain needs JavaScript.</p></noscript>
  </div>
  <div class="mem-side reveal">
    <div class="mem-status" id="mem-status" role="status" aria-live="polite"><span class="chip chip-ok" id="mem-chip">Chain verified</span><p id="mem-msg">4 lessons, every link checks out.</p></div>
    <div class="mem-actions">
      <button class="mbtn" type="button" id="m-add">Add a lesson</button>
      <button class="mbtn" type="button" id="m-tamper" aria-pressed="false">Tamper with lesson 2</button>
      <button class="mbtn" type="button" id="m-roll">Roll back last</button>
      <button class="mbtn mbtn-quiet" type="button" id="m-reset">Reset</button>
    </div>
    <p class="foot">This runs the same SHA-256 formula as the real store, in your browser, with short example lessons in place of real ones. Edit lesson 2 and every hash from there on stops matching.</p>
  </div>
</div>'''

    rollback = '''<div class="prose reveal"><p><code>rollback(version)</code> goes back to an earlier version. The later lessons are <strong>moved into an <code>archived</code> table, not deleted</strong>, together with the version they were rolled back to, so an audit can still see exactly what was undone.</p>
<p>The audit (<code>audit()</code>) makes three checks, on a <em>copy</em> so the original is never touched:</p></div>
<div class="grid-3">
<article class="card reveal"><span class="num">1</span><h3>Chain</h3><p>Every lesson's version, parent and hash recompute correctly from version 1.</p></article>
<article class="card reveal"><span class="num">2</span><h3>Rollback</h3><p>Roll a copy back to the middle: the chain still verifies, the head hash equals the earlier version's hash, and the remaining history is identical to the snapshot taken before.</p></article>
<article class="card reveal"><span class="num">3</span><h3>Provenance</h3><p>Every lesson has a task, a run and a non-negative seed.</p></article>
</div>'''

    arows = []
    for a in audits:
        arows.append([f"Seed {a['seed']}", CNAME[a["condition"]], f"{a['lessons']}", "✓" if a["chain_ok"] else "✕", "✓" if a["rollback_ok"] else "✕", "✓" if a["provenance_ok"] else "✕", "<b>pass</b>" if a["ok"] else "<b>FAIL</b>"])
    luc = [a["lessons"] for a in audits if a["condition"] == "lucifer"]
    irr = [a["lessons"] for a in audits if a["condition"] == "irrelevant"]
    t_audit = table(["Store", "Condition", "Lessons", "Chain", "Rollback", "Provenance", "Result"], arows, "dt", 640)
    audit_note = f'<div class="prose reveal"><p>All {len(audits)} stores from the run passed all three checks. These are the real audits from <code>audits.json</code>. Wrong notes wrote more lessons ({min(irr)} to {max(irr)} per store) than Lucifer ({min(luc)} to {max(luc)}) because it failed its first tries more often in the experience phase ({frac(p1(sel("irrelevant", "experience")), 60)} first-try passes, against {frac(p1(sel("lucifer", "experience")), 60)}), and every failure writes a lesson.</p></div>'

    flow = '''<div class="prose reveal"><p>A worked example of a lesson, exactly as it is written. The “failing test” text comes from the real sandbox run on a plain answer:</p></div>'''
    ex_task = BY_ID["date-1"]
    fb = SandboxExecutor().run(ex_task, ex_task.naive).feedback
    lesson = failure_lesson(ex_task, fb)
    example = flow + code(lesson) + '<div class="prose reveal"><p>Later, on a similar date task, retrieval scores this lesson highly because it shares many words with the new spec (“year”, “month”, “day”, “writes”, “date”, “text”), so it is likely put into the prompt under “Notes from earlier tasks”. The model sees the expected <code>05-Mar-2026</code> format and applies it. <a href="proof.html#follow">See what actually happened →</a></p></div>'

    notdo = '<div class="callout warn reveal"><b>What this memory does not do.</b> It does not change the model. It does not summarise or generalise: a lesson is the task, the spec and the failing test, so in the convention tasks it literally contains a correct example. The result therefore measures “can the model use a pasted correct example from an earlier task”, a modest but real form of learning. It does not yet show broad skill transfer.</div>'

    body = (
        block("what", "What memory is here", "", intro + schema)
        + block("chain", "The hash chain", "", chain, True)
        + block("play", "Try it", "Drag the chain to turn it. Edit an old lesson, roll back, or add one, and watch the check react.", demo)
        + block("rollback", "Rollback and the audit", "", rollback, True)
        + block("audit", "The real audit results", "From the published run.", t_audit + audit_note)
        + block("example", "A lesson, written out", "", example, True)
        + block("limits", "Be clear about what it is", "", notdo)
    )
    write("memory", "Memory", "How Lucifer's memory works: an append-only hash-chained SQLite store of lessons with provenance, rollback that archives instead of deleting, and an audit. Includes an interactive 3D chain.", "Memory",
          "A notebook you can audit, <em>and try to break.</em>",
          "Lessons are written after failures, chained by hash for tamper detection, and shown to the model later. The mechanism is small on purpose, so that every claim about it can be checked.",
          [("what", "What it is"), ("chain", "Hash chain"), ("play", "Try it"), ("rollback", "Rollback"), ("audit", "Audit results"), ("example", "A lesson"), ("limits", "Limits")], body)


# ================================================================================================================ PROOF
def build_proof() -> None:
    rec = f'''<div class="prose reveal"><p>The result is a calculation over <code>rows.json</code>. Press the button and your browser will download that file from this site, show its SHA-256 fingerprint, rebuild the table, and rerun the 10,000-resample bootstrap. Nothing is sent anywhere, and nothing on this block is hard-coded.</p></div>
<div class="verify reveal" id="verify">
  <div class="verify-bar">
    <button class="btn btn-light" type="button" id="v-run">Recompute from the raw rows</button>
    <span class="v-state" id="v-state">Not run yet</span>
  </div>
  <div class="v-grid">
    <div class="v-card"><small>Rows loaded</small><b id="v-rows">–</b></div>
    <div class="v-card"><small>SHA-256 of rows.json</small><b class="mono" id="v-hash">–</b></div>
    <div class="v-card"><small>Lucifer − baseline</small><b id="v-eff">–</b><span id="v-ci"></span></div>
    <div class="v-card"><small>Lucifer − wrong notes</small><b id="v-eff2">–</b><span id="v-ci2"></span></div>
  </div>
  <div class="table-wrap"><table class="dt" id="v-table" style="min-width:560px"><thead><tr><th>Phase</th><th>No memory</th><th>Lucifer</th><th>Wrong notes</th></tr></thead><tbody><tr><td colspan="4" class="dimcell">Press the button.</td></tr></tbody></table></div>
  <p class="foot v-unit"><b>What is counted.</b> 630 task runs (210 per condition; 90 per condition on the primary metric). The bootstrap resamples the <b>18 tasks</b>, not the task runs: each task's five seeds are averaged first. The first-try column counts task runs, not model generations.</p>
  <p class="foot" id="v-gate">Retention gate: not computed yet.</p>
  <p class="foot">The published values are 0%, 67%, 17%, 98% by phase and +0.50 with a 95% interval of +0.30 to +0.70. The browser uses a different random generator from the Python lab, so a rerun may move an interval end by a hair; it should land on the same two-decimal figures. To check the file is the one in the repository, compare the fingerprint with <code>shasum -a 256 results/published/qwen14b-convention/rows.json</code> on your own checkout of commit <code>{COMMIT}</code>.</p>
</div>'''

    # follow one lesson
    t4, tex = BY_ID["date-4"], BY_ID["date-1"]
    fb = SandboxExecutor().run(tex, tex.naive).feedback
    follow_rows = "".join(f'<div class="outrow"><span>{CNAME[c]}</span>{dots(c, "similar", "date-4")}<em>{p1(sel(c, "similar", task="date-4"))} first try · {p2(sel(c, "similar", task="date-4"))} after retry, of 5</em></div>' for c in CONDS)
    follow = f'''<ol class="pipe reveal">
<li><b>1 · An experience task</b><span>The model is asked for <code>{tex.entry}</code>: “{spec_html(tex.spec)}” A plain answer writes an ISO date like <code>2026-03-05</code>.</span></li>
<li><b>2 · The referee says no</b><span>This is the real message from the sandbox, produced by running the plain answer: <code class="wrapcode">{e(fb)}</code></span></li>
<li><b>3 · A lesson is written</b><span>Lucifer and Wrong notes store the lesson (see the <a href="memory.html#example">full text</a>). No memory stores nothing.</span></li>
<li><b>4 · A similar task arrives later</b><span>The model is asked for <code>{t4.entry}</code>: “{spec_html(t4.spec)}” Lucifer's retrieval puts the three most relevant lessons in its prompt (every Lucifer similar attempt in this run was shown at least one lesson). No memory is shown none; Wrong notes is shown the three least relevant.</span></li>
<li><b>5 · What happened</b><span>The real outcomes on the five seeds, from <code>rows.json</code>:<div class="outs inline">{follow_rows}</div></span></li>
</ol>
<div class="legend dotkey reveal"><span><i class="d d1"></i>passed on the first try</span><span><i class="d d2"></i>passed after the retry</span><span><i class="d d0"></i>failed both</span></div>
<div class="prose reveal"><p>Step 2 is generated by running the lab's own sandbox on the task's plain answer, so it is exactly what the model would be told. It is <em>not</em> a recording of a model's attempt (the raw model replies are not in the published files). Step 5 is recorded data. <a href="tasks.html#date-4">Open the full task →</a></p></div>'''

    ev = table(["Claim", "How to check it", "Status"], [
        ["Lucifer beats no memory on first try, +0.50 [+0.30, +0.70]", "Recompute in this page; read <code>rows.json</code>", "<span class='chip chip-ok'>Reproduced here</span>"],
        ["Wrong notes did not help on the primary metric", "Same recomputation, third column", "<span class='chip chip-ok'>Reproduced here</span>"],
        ["Memory was not edited after the fact", "Audit table: chain, rollback, provenance on all 10 stores", "<span class='chip chip-ok'>In the published audits</span>"],
        ["The tasks hide their convention and can tell right from wrong", "Read each task; the lab tests every task with a reference and a plain answer", "<span class='chip chip-ok'>Tested in the lab</span>"],
        ["The harness can tell learning from no learning", "Simulated-agent controls in <code>tests/test_controls.py</code>", "<span class='chip chip-ok'>Tested in the lab</span>"],
        ["Lucifer works on other models", "Not tested. A side run on another model pointed the same way for one seed only", "<span class='chip chip-mid'>Not shown</span>"],
        ["Lucifer works on other kinds of task", "Not tested. Held-out task families are future work", "<span class='chip chip-mid'>Not shown</span>"],
        ["Lucifer transfers to loosely related tasks", "Transfer was 17% first try", "<span class='chip chip-mid'>Weak</span>"],
    ], "dt dt-wide", 760)

    controls = f'''<div class="prose reveal"><p>A measurement is only worth trusting if it can come out negative. Before any real run, the lab was checked on <strong>simulated agents</strong> with a known truth, so we could see whether the gates tell them apart. These are automated tests in <code>tests/test_controls.py</code>:</p></div>
<div class="grid-3">
<article class="card reveal"><h3>An agent that cannot learn</h3><p>Must almost never be reported as improving. (<code>test_an_agent_that_cannot_learn_is_almost_never_reported_as_improving</code>)</p></article>
<article class="card reveal"><h3>An agent that learns</h3><p>Must be detected once the task set is large enough. (<code>test_with_about_four_times_the_tasks_a_real_effect_is_detected_and_a_null_one_is_not</code>)</p></article>
<article class="card reveal"><h3>An agent hurt by memory</h3><p>Must be reported as hurt. (<code>test_an_agent_hurt_by_memory_is_reported_as_hurt</code>)</p></article>
</div>
<div class="callout warn reveal"><b>This is also why the result is a first look.</b> The same tests show that a set with only 12 primary tasks misses a real effect (<code>test_a_set_with_only_12_primary_tasks_misses_a_real_effect_so_it_must_not_be_trusted</code>). This run had 18. See the <a href="limits.html#power">power table</a>.</div>'''

    repro = f'''<div class="grid-2">
<article class="card reveal"><h3>Run the lab and its tests</h3>{code("git clone " + REPO + "\ncd Lucifer-BenchMarks\npython -m venv .venv && .venv/bin/pip install -e .\n.venv/bin/pytest")}<p class="foot">125 tests, about four minutes.</p></article>
<article class="card reveal"><h3>Repeat the experiment on GitHub</h3>{code("# Actions → Experiment → Run workflow\nmodel     qwen2.5-coder:14b\ntaskset   convention\nseeds     5\npublish   true")}<p class="foot">One job per seed, then a merge and the three gates in the job summary. No GPU and no local model needed.</p></article>
</div>
<div class="prose reveal"><p>The files behind this site: <a href="{REPO}/tree/main/results/published/qwen14b-convention" rel="noopener">results/published/qwen14b-convention</a> (commit <code>{COMMIT}</code>), the workflow run <a href="{REPO}/actions/runs/{RUN_ID}" rel="noopener">{RUN_ID}</a>, the task set in <a href="{REPO}/blob/main/src/lucifer/tasks.py" rel="noopener"><code>src/lucifer/tasks.py</code></a>, and the plan that fixed the gates in advance, <a href="{REPO}/blob/main/docs/EXPERIMENT-PLAN.md" rel="noopener"><code>docs/EXPERIMENT-PLAN.md</code></a>.</p></div>'''

    body = (
        block("recompute", "Recompute it yourself, right here", "", rec)
        + block("follow", "Follow one lesson from failure to success", "A single convention, traced through the whole experiment.", follow, True)
        + block("controls", "The test can say no", "", controls)
        + block("ledger", "Claim, check, status", "What is proven by this evidence and what is not.", ev, True)
        + block("reproduce", "Run it yourself", "", repro)
    )
    write("proof", "Proof of concept", "Verify the Lucifer Lab result yourself: recompute the headline and the bootstrap interval in your browser from the raw rows, follow one lesson end to end, and see which claims are and are not supported.", "Proof of concept",
          "Don't trust the page. <em>Recompute it.</em>",
          "The raw rows are downloaded into your browser and the headline is calculated again, live. Then one lesson is followed from a failed attempt to a first-try pass.",
          [("recompute", "Recompute"), ("follow", "One lesson"), ("controls", "Controls"), ("ledger", "Claim and status"), ("reproduce", "Run it")], body)


# ================================================================================================================ JOURNEY
def build_journey() -> None:
    tl = [
        ("11 Nov 2026", "The lab, built", "Task set, sandbox, versioned memory with rollback, three conditions, a paired bootstrap, three gates, and simulated-agent controls to test the tester.", "d8655b1"),
        ("11 Nov", "Calibration says the exam is too easy", "Three hosted models scored 100%, 96% and 42% first try with no memory. A flawed task (<code>days_between</code> did not say its inputs were integers) was caught and its spec fixed.", "7be58d6"),
        ("11 Nov", "The power study is corrected", "An early 20-run table said 90% power at 24 tasks. That was a lucky draw; 60 runs gave 72%. The plan now asks for about 48 similar and transfer tasks.", "8868edb"),
        ("11 Nov", "Tracing and a dashboard", "Every step of every solve is recorded, with a local dashboard to click into any attempt.", "c6c090e"),
        ("11 Nov", "Harder families, and a scoring bug found", "Four harder families brought the set to 50 tasks. The dashboard exposed a bug: the retention gate picked tasks and measured them on the same runs and mistook luck for forgetting. Selection now uses half the seeds, measurement the other half.", "c7b8ee7"),
        ("11 Nov", "Hidden conventions", "Strong models saturate well-specified tasks, so memory had nothing to improve. 30 convention tasks were added whose rule can only be learned from a failing test.", "f92ccb8"),
        ("12 Nov", "Everything moves onto CI/CD", "Experiments run on GitHub Actions: one job per seed, a merge step, gates in the job summary, published results committed automatically.", "136a110"),
        ("12 Nov", "First real result", "Five seeds of <code>qwen2.5-coder:14b</code>: +0.50 first-try improvement, interval +0.30 to +0.70, published with every caveat. Version 1 closed.", "1a88d19"),
    ]
    items = "".join(
        f'<li class="reveal"><span class="t-dot{" t-on" if i == len(tl) - 1 else ""}"></span><div><small class="when">{d}</small><b>{t}</b><p>{x}</p><a class="commit" href="{REPO}/commit/{c}" rel="noopener">commit {c}</a></div></li>'
        for i, (d, t, x, c) in enumerate(tl)
    )
    timeline = f'<ol class="timeline wide">{items}</ol><div class="prose reveal"><p>Dates and commit ids come from the repository history; the links open the exact commits.</p></div>'

    cal = table(["Model (Groq, hosted)", "Mean first try", "Usable tasks (20–80%)", "Too easy", "Too hard"], [
        ["<code>qwen/qwen3.8-27b</code>", "100%", "0", "24", "0"],
        ["<code>openai/gpt-oss-20b</code>", "96%", "0", "23", "1"],
        ["<code>allam-2-7b</code>", "42%", "2", "9", "13"],
    ], "dt", 640)
    cal2 = table(["Model (GitHub runner)", "First try", "After one retry", "Time per call"], [
        ["<code>qwen2.5-coder:3b</code>", "0%", "17%", "about 10.5 s"],
        ["<code>qwen2.5-coder:7b</code>", "0%", "26%", "about 11 s"],
        ["§<code>qwen2.5-coder:14b</code>", "0%", "60%", "about 27 s"],
    ], "dt", 560)
    calnote = '<div class="prose reveal"><p>Calibration asks: <em>is there room for memory to help?</em> The first table (3 seeds, baseline only, the older fully specified tasks) found strong models at the ceiling, so no memory effect could show. The second (1 seed, convention tasks) found the opposite problem: a 3B or 7B model cannot apply a hidden convention even when told. The 14B was the first that could fix one after feedback (60%), so it became the subject of the real run.</p></div>'

    lessons = '''<div class="grid-2">
<article class="card reveal"><h3>Strong models saturate</h3><p>96–100% first-try success with no memory leaves nothing to improve. Making tasks more numerous does not help; they must hide something learnable.</p></article>
<article class="card reveal"><h3>Choosing and measuring on the same data fakes results</h3><p>The retention-gate bug was exactly this. Regression to the mean looked like forgetting until selection and measurement were split across seeds.</p></article>
<article class="card reveal"><h3>Small sets give weak verdicts</h3><p>About 26 primary tasks detect a real +20 point effect roughly half the time. The first real run has 18, so it is a first look.</p></article>
<article class="card reveal"><h3>Feedback alone fixes most conventions</h3><p>After one retry the baseline reaches 52%. Any memory gain therefore has to show up on the <em>first</em> try, which is why that is the primary metric.</p></article>
<article class="card reveal"><h3>Simple retrieval was enough</h3><p>Plain word-matching TF-IDF did as well as anything tried (word pairs, stemming). Semantic retrieval is still untested.</p></article>
<article class="card reveal"><h3>A hosted free tier is not an experiment platform</h3><p>A side run on a hosted model pointed the same way (+0.44, one seed) but its other seeds hit a daily token cap, so it is not part of the result. The real run moved onto pinned models on GitHub runners.</p></article>
</div>'''

    body = (
        block("timeline", "How it got here", "Two days, twelve commits, one question.", timeline)
        + block("calibration", "Picking a model that has room to learn", "", cal + cal2 + calnote, True)
        + block("lessons", "What was learned along the way", "", lessons)
    )
    write("journey", "Journey", "The story of Lucifer Lab Version 1: the timeline, what calibration showed, the bugs found and fixed along the way, and what each taught.", "Journey",
          "What was tried, <em>caught and fixed.</em>",
          "A result is only as good as the path to it. Here are the wrong turns: an exam that was too easy, a flawed task, a scoring bug and a power study that fooled us once.",
          [("timeline", "Timeline"), ("calibration", "Calibration"), ("lessons", "Lessons")], body)


# ================================================================================================================ LIMITS
def build_limits() -> None:
    lim = []
    pc = {c: sel(c, phases=PRIMARY) for c in CONDS}
    items = [
        ("The baseline is zero by design", f"The task descriptions leave the conventions out, so a model has to infer them or guess; No memory solved {frac(0, 210)} task runs first try. After one retry it reaches {pct(p2(pc['baseline']), 90)}. The gain is mostly skipping a failed first try, not solving something that was otherwise unsolvable.", "Report first-try and after-retry side by side (done), and add tasks where the baseline sits in the middle."),
        ("Transfer is weak", f"On similar tasks Lucifer got {pct(p1(sel('lucifer','similar')), 60)}; on tasks that combine conventions, {pct(p1(sel('lucifer','transfer')), 30)}. It helps most when a new task is close to an old one.", "A stronger transfer test with new conventions, not only combinations of seen ones."),
        ("The lesson contains the answer", "In these tasks a lesson literally includes the failing test, so the model is using a pasted correct example. Replay at 98% is memorisation. This is real but modest learning.", "Tasks where the lesson must be abstracted, not copied."),
        ("One model, 18 scored tasks", "One 14B coder model, 12 similar and 6 transfer tasks, 5 seeds, written by the author. The interval is wide for a reason.", "A second model, and at least about 48 scored tasks (see the power table)."),
        ("Retention is undecided", "Because the baseline masters no task, gate 2 has nothing to test and stays inconclusive. The overall verdict is therefore “not all gates passed”.", "Tasks the baseline already solves often, so forgetting can actually be measured."),
        ("Some tasks may be unfair", f"Lucifer never solved <code>shipment_id</code> or <code>ticket_id</code> first try (0 of 5 each), although all seeds passed after a retry. The lessons show <code>ORD</code>, <code>INV</code> and <code>CUS</code>; a model may reasonably guess <code>SHP</code> or <code>TKT</code>. This reading is untested.", "Read the traces for those tasks; fix or replace any task whose convention a lesson cannot disambiguate."),
        ("Wrong notes leak a little", f"In the experience phase, Wrong notes solved {frac(p1(sel('irrelevant','experience')), 60)} first try against 0 for No memory. Irrelevant lessons can still carry hints early on. In the primary phases it solved 0 of 90.", "Keep the control; consider a second control with lessons from a different domain."),
        ("A side run, not merged", "An earlier hosted run on another model (one seed) pointed the same way, +0.44, but its other seeds hit a free-tier daily token cap. It is not part of the result.", "Re-run on a pinned model with all seeds."),
    ]
    for i, (t, w, f) in enumerate(items, 1):
        lim.append(f'<article class="card limit reveal"><span class="num">{i}</span><h3>{t}</h3><p>{w}</p><p class="fix"><b>What would settle it</b> {f}</p></article>')
    limhtml = '<div class="limits-list">' + "".join(lim) + "</div>"

    power = table(["Similar + transfer tasks", "Gate 1 passed, real +20 pt effect", "Gate 1 passed, no effect"], [
        ["12 (first 24-task set)", "19 of 60 (32%)", "0 of 60"],
        ["24", "43 of 60 (72%)", "1 of 60"],
        ["26 (the 50-task pitfall set)", "32 of 60 (53%)", "1 of 60"],
        ["§<b>18 (this run)</b>", "not measured; between the 12 and 24 rows", "–"],
        ["48", "59 of 60 (98%)", "3 of 60"],
        ["52", "59 of 60 (98%)", "0 of 60"],
        ["72", "60 of 60", "1 of 60"],
    ], "dt", 640)
    power_note = '<div class="prose reveal"><p>Measured on simulated agents with a known +20 point effect, 5 seeds, 60 simulated experiments per row. With 18 primary tasks, a real effect of that size is detected only some of the time, so a “no effect” from a set this small would have been weak evidence, and a “yes” is a first look. Even 60 runs leave about ±6 points of noise on these percentages. Smaller true effects need more tasks; that is not measured yet.</p></div>'

    threats = table(["Threat", "How it could mislead", "Guard so far"], [
        ["Memorisation by the base model", "The model may have seen similar tasks", "A replay phase; fresh task families still needed"],
        ["Near-duplicate leakage", "A similar task may differ only by name", "Similar tasks differ in function, not just names"],
        ["Prompt length", "More text alone could change behaviour", "The Wrong notes control"],
        ["Noise", "Few seeds, temperature 0.7", "Bootstrap over tasks; intervals, not just means"],
        ["Model drift", "Hosted models change under one name", "Pinned model and tool versions on runners"],
        ["Author-written tasks", "The exam and its answer key come from the same person", "Open tasks and tests; external tasks wanted"],
        ["Code execution", "Model code runs on the runner", "Separate process with limits; not a security boundary"],
    ], "dt", 700)

    changes = '''<div class="grid-2">
<article class="card reveal"><h3>What would strengthen the claim</h3><ul class="bul"><li>The gain holds on a second, different model.</li><li>It holds on a held-out task family never seen while designing.</li><li>It holds with 48 or more scored tasks and a tighter interval.</li><li>Transfer improves with a better-built test.</li></ul></article>
<article class="card reveal"><h3>What would weaken it</h3><ul class="bul"><li>The gain disappears on a pinned larger model that already fixes conventions.</li><li>Fixing the unfair tasks removes most of the effect.</li><li>A harder control, with lessons from another domain, matches Lucifer.</li><li>The interval crosses zero as tasks are added.</li></ul></article>
</div>
<div class="prose reveal"><p>If the next run shows no effect, it gets published the same way. The gates were fixed before the run, and the code and rows are open so anyone can recompute them.</p></div>'''

    help_ = f'''<div class="prose reveal"><p>This is a small open project and the most useful help is scrutiny. Concrete ways in, each a self-contained pull request:</p></div>
<div class="grid-3">
<article class="card reveal"><h3>Add tasks</h3><p>New hidden conventions, not renamed copies. Each task needs hidden tests, a reference answer that passes and a naive answer that fails. The existing test <code>test_reference_passes_and_naive_fails</code> checks it. Work in <code>src/lucifer/tasks.py</code>.</p></article>
<article class="card reveal"><h3>Add a model</h3><p>Run the same experiment on a second model and report it unedited. Backends live in <code>src/lucifer/backends/</code>; runs go through the <code>experiment.yml</code> workflow, no GPU needed.</p></article>
<article class="card reveal"><h3>A held-out family</h3><p>Design a task family before looking at results, then evaluate it once. This tests generalisation instead of memorisation.</p></article>
<article class="card reveal"><h3>Stronger transfer</h3><p>Conventions that must be abstracted from examples rather than copied, so memory has to do more than paste a test.</p></article>
<article class="card reveal"><h3>Semantic retrieval</h3><p>Try embeddings against the TF-IDF baseline in <code>retrieval.py</code>, keeping the same control and metric.</p></article>
<article class="card reveal"><h3>Review the method</h3><p>Read the <a href="method.html">method</a> and the <a href="tasks.html">tasks</a> and tell me where they are weak. Issues with evidence are as welcome as code.</p></article>
</div>
<div class="cta-row center reveal"><a class="btn btn-light" href="{REPO}" rel="noopener">Open the repository <span aria-hidden="true">→</span></a><a class="btn btn-ghost" href="{REPO}/issues" rel="noopener">Open an issue</a></div>'''

    body = (
        block("limits", "What this result does not show", "A “no effect” result would have been published too. These are the reasons to read this one as a first look, not proof, each with what would settle it.", limhtml)
        + block("power", "Why 18 tasks is thin", "The power study, measured on simulated agents.", power + power_note, True)
        + block("threats", "Threats to validity", "Things that could make any result here misleading.", threats)
        + block("conclusions", "What would change the conclusion", "", changes, True)
        + block("help", "Help wanted", "Open source contributions that would make this stronger.", help_)
    )
    write("limits", "Limits and next steps", "What the Lucifer Lab Version 1 result does not show: the baseline, weak transfer, small sample, unfair tasks and more. Plus the power study, threats to validity and how developers can contribute.", "Limits and next steps",
          "What this does <em>not</em> show, and how to help.",
          "Every claim on this site has a limit. They are written down here with the evidence, together with the ways a developer can make the next result harder to dismiss.",
          [("limits", "Limits"), ("power", "Power"), ("threats", "Threats"), ("conclusions", "What would change it"), ("help", "Contribute")], body)


# ------------------------------------------------------------------------------------------------------------- milestones
def _anchor(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _verdict(cell: str) -> str:
    return {"Pass": '<span class="chip chip-ok">Pass</span>', "Fail": '<span class="chip chip-bad">Fail</span>'}.get(cell, e(cell))


def _href(url: str) -> str:
    return f'href="{e(url)}"' + (' rel="noopener"' if url.startswith("http") else "")


def _update_li(u: dict) -> str:
    links = "".join(f' <a {_href(l["href"])}>{e(l["label"])} →</a>' for l in u.get("links", []))
    return f'<li><span class="ms-date">{e(u["date"])}</span> {e(u["text"])}{links}</li>'


def _achievement(a: dict) -> str:
    links = ""
    if a.get("links"):
        links = '<p class="ms-links">' + " ".join(f'<a {_href(l["href"])}>{e(l["label"])} →</a>' for l in a["links"]) + "</p>"
    return f'<article class="card reveal ach"><span class="ms-date">{e(a["date"])}</span><h3>{e(a["title"])}</h3><p>{e(a["text"])}</p>{links}</article>'


def _entry(en: dict, last: bool) -> str:
    status = {"done": ("Done", "chip-ok"), "partly": ("Partly done", "chip-mid"), "blocked": ("Blocked", "chip-bad"), "planned": ("Planned", "chip-mid")}[en["status"]]
    points = "".join(f"<li>{e(x)}</li>" for x in en["points"])
    table_html = ""
    if en.get("table"):
        t = en["table"]
        rows = [[_verdict(c) if i else e(c) for i, c in enumerate(r)] for r in t["rows"]]
        table_html = table([e(h) for h in t["head"]], rows, "dt", 420)
    not_shown = ""
    if en["not_shown"]:
        not_shown = '<details class="ms-not"><summary>What this does not show</summary><ul class="bul">' + "".join(f"<li>{e(x)}</li>" for x in en["not_shown"]) + "</ul></details>"
    links = ""
    if en["links"]:
        links = '<p class="ms-links">' + " ".join(f'<a href="{e(l["href"])}">{e(l["label"])} →</a>' for l in en["links"]) + "</p>"
    updates = ""
    if en["updates"]:
        updates = '<div class="ms-updates"><b>Updates, added later</b><ul class="bul">' + "".join(_update_li(u) for u in en["updates"]) + "</ul></div>"
    return f'''      <li class="reveal ms" id="{_anchor(en["id"])}"><span class="t-dot{' t-on' if last else ''}"></span>
        <article class="card ms-card">
          <div class="ms-meta"><span class="ms-date">{e(en["date"])}</span><span class="chip">{e(en["label"])}</span><span class="chip {status[1]}">{status[0]}</span></div>
          <h3>{e(en["title"])}</h3>
          <p class="ms-sum">{e(en["summary"])}</p>
          {"<ul class='bul ms-points'>" + points + "</ul>" if points else ""}
          {table_html}
          {not_shown}
          {links}
          {updates}
        </article>
      </li>'''


def build_milestones() -> None:
    """Renders data/milestones.json, the append-only log. Refuses to build if anything published was edited or removed."""
    sys.path.insert(0, str(SITE / "tools"))
    from check_append_only import check, load_base  # noqa: E402

    log = json.loads((SITE / "data" / "milestones.json").read_text())
    problems = check(load_base("HEAD"), log)
    if problems:
        raise SystemExit("milestones.json is not append-only:\n  " + "\n  ".join(problems))
    blocks = ""
    for i, ver in enumerate(log["versions"]):
        items = [en for en in log["entries"] if en["version"] == ver["id"]]
        lis = "\n".join(_entry(en, k == len(items) - 1) for k, en in enumerate(items))
        still = ""
        if ver.get("open_items"):
            still = '<div class="callout warn reveal"><b>Still open in this version</b><ul class="bul">' + "".join(f"<li>{e(x)}</li>" for x in ver["open_items"]) + "</ul></div>"
        more = f'<p><a class="more" {_href(ver["page"])}>{e(ver.get("page_label", "The headline result of this version"))} →</a></p>' if ver.get("page") else ""
        inner = f'''<ol class="timeline wide ms-list">
{lis}
    </ol>
    {still}'''
        blocks += block(_anchor(ver["id"]), e(ver["title"]), e(ver["blurb"]) + more, inner, alt=bool(i % 2))
    rule = f'''<div class="prose reveal"><p><b>How this page works.</b> {e(log["rule"])} The page is generated from <a href="data/milestones.json">data/milestones.json</a>, and a check refuses any change that edits or removes a published entry. Later facts (for example a timestamp that finally confirms) are added as dated updates under the entry they belong to. Goals for what comes next are tracked as <a href="https://github.com/Lakshit-Startup-Ideas/Lucifer-BenchMarks/milestones" rel="noopener">GitHub milestones</a> in the Benchmarks repository.</p></div>'''
    achievements = '<div class="grid-3">' + "".join(_achievement(a) for a in log.get("achievements", [])) + "</div>"
    body = block("how", "How to read this", "", rule) + block("achievements", "Achievements", "What has been done, in plain terms. Each one links to its evidence.", achievements, alt=True) + blocks
    def chip(v: dict) -> str:
        planned_only = all(en["status"] == "planned" for en in log["entries"] if en["version"] == v["id"])
        return ("Goals · " if planned_only else "") + v["id"].replace("V", "Version ")
    toc = [("how", "How it works"), ("achievements", "Achievements")] + [(_anchor(v["id"]), chip(v)) for v in log["versions"] if v["id"] != "V1.2"] + [("v1-1-proof", "Proof of existence")] + [(_anchor(v["id"]), chip(v)) for v in log["versions"] if v["id"] == "V1.2"]
    write("milestones", "Milestones", "Every version and milestone of the Lucifer Lab research, in order: Version 1, then Version 1.1 milestones M1 to M8, with results, limits and proof hashes. Append-only.",
          "Version history", "Every version, every milestone, <em>nothing removed.</em>",
          "Achievements first, then Version 1, each Version 1.1 milestone with what it showed, what it did not and its pass or fail, and finally the goals for Version 1.2. New entries are added at the end; published ones are never edited.", toc, body)


def copy_data() -> None:
    d = SITE / "data"
    d.mkdir(exist_ok=True)
    for fn in ("rows.json", "audits.json", "meta.json", "report.txt"):
        shutil.copyfile(RUN / fn, d / fn)


if __name__ == "__main__":
    copy_data()
    build_results()
    build_method()
    build_tasks()
    build_memory()
    build_proof()
    build_journey()
    build_limits()
    build_milestones()
