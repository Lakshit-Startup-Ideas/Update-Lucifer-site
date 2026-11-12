# Lucifer Lab site

Static site for Lucifer Lab: the Version 1 result, method, milestones and limits.
Plain HTML, CSS and a small script. No build step, no dependencies.

Experiment code and raw results: https://github.com/Lakshit-Startup-Ideas/Lucifer-BenchMarks

## Files

| File | What it is |
|---|---|
| `index.html` | the whole page (hero, result, method, milestones, limits, reproduce, FAQ) |
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
