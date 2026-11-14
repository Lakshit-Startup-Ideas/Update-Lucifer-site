# Lucifer Lab site

Static site for Lucifer Lab: the Version 1 result, method, milestones and limits.
Plain HTML, CSS and a small script. No build step, no dependencies.

Experiment code and raw results: https://github.com/Lakshit-Startup-Ideas/Lucifer-BenchMarks

## Files

| File | What it is |
|---|---|
| `index.html` | the short version: hero, result, method, memory, milestones, limits, reproduce, FAQ, and links to the detail pages |
| `results.html`, `method.html`, `tasks.html`, `memory.html`, `proof.html`, `journey.html`, `limits.html` | the detail pages. **Generated** by `tools/build.py` from the published run; do not edit by hand |
| `milestones.html` | the version history: Version 1, then each Version 1.1 milestone. **Generated** from `data/milestones.json`; entries are append-only |
| `data/milestones.json` | the append-only milestone log (never edit or remove an entry; add a dated item to its `updates` list instead) |
| `data/proof/` | the proof-of-existence manifests and OpenTimestamps stamps (hashes only), linked from the Milestones page |
| `tools/check_append_only.py` | fails if any published milestone entry was edited or removed (`python3 tools/test_check_append_only.py`-style tests in `tools/`) |
| `data/` | the published run (`rows.json`, `audits.json`, `meta.json`, `report.txt`), served so the Proof page can recompute the result in the browser |
| `tools/build.py` | regenerates the detail pages and `data/` from a checkout of Lucifer-BenchMarks |
| `styles.css` | all styling, design tokens at the top (`:root`) |
| `script.js` | reveal on scroll, count-ups, hero depth and tilt, live demo, the 3D memory chain, chart replay, mobile menu (the page reads fine without it) |
| `favicon.svg`, `robots.txt` | icon, crawler rules |
| `vercel.json` | clean URLs and security headers |

## Motion and interactivity

No libraries, no build step: CSS 3D transforms plus one small script.

- Hero: words blur in, glass orbs and the sky shift with the pointer, the app card tilts back and flattens on scroll, and its log types out a short illustration of one lesson being written and reused.
- Result: the chart replays on demand (Replay button), bars show their counts on hover, and the +0.50 counts up.
- Memory (`#memory`): a 3D chain of example lessons. Drag or use the arrow keys to turn it; add a lesson, tamper with lesson 2 (the check fails from that point on), roll back (archived, not erased) or reset. The fingerprint is a toy hash for illustration, and the lessons are examples, not real data.
- Cards lean toward the pointer on devices with a mouse. With `prefers-reduced-motion`, everything is static and nothing is hidden.

## Updating the numbers

The detail pages are static HTML, generated so that no figure is typed by hand. After a new run is published in the Lucifer-BenchMarks repository:

```bash
python3 tools/build.py ../lucifer-lab   # path to your Lucifer-BenchMarks checkout
```

This rewrites the seven detail pages and `data/`, reading the task text from `src/lucifer/tasks.py` and the figures from `results/published/qwen14b-convention/`. If the run folder name changes, edit `RUN` and the run id and commit at the top of `tools/build.py`. The home page (`index.html`) is hand-written: update the figures listed below there.

## Adding a milestone (append-only)

1. Append a new object to `entries` in `data/milestones.json` (and a new block to `versions` if it starts a new version). Never edit or delete an existing entry; to record a later fact, append `{"date": ..., "text": ...}` to that entry's `updates`.
2. `python3 tools/check_append_only.py` compares the file with the last commit and fails on any edit or removal. `python3 tools/build.py ../lucifer-lab` runs the same check before writing `milestones.html`, so a bad edit cannot be published by accident.
3. Commit the JSON and the regenerated page together.

## Run it locally

```bash
python3 -m http.server 5188
```

Then open http://127.0.0.1:5188.

## Deploy on Vercel

1. Import this repository in Vercel.
2. Framework preset: **Other**. Leave build command and output directory empty (the site is served from the repository root).
3. Deploy.

## Where the numbers come from

Every figure on the page is copied from `results/published/qwen14b-convention/report.txt` in the Lucifer-BenchMarks repository (run `qwen14b-convention`, 5 seeds, 630 attempts). When a newer run is published, update the figures in `index.html`:

- result chart bars (`--h` values) and their labels
- the +0.50 gain, the interval, and the axis positions
- the after-one-retry, tokens-per-task and per-seed cards
- the stats band and the limits text

Keep the limits section honest: if a number changes, re-read what it says.
