# Lucifer Lab site

Static site for Lucifer Lab: the Version 1 result, method, milestones and limits.
Plain HTML, CSS and a small script. No build step, no dependencies.

Experiment code and raw results: https://github.com/Lakshit-Startup-Ideas/Lucifer-BenchMarks

## Files

| File | What it is |
|---|---|
| `index.html` | the whole page (hero, result, method, milestones, limits, reproduce, FAQ) |
| `styles.css` | all styling, design tokens at the top (`:root`) |
| `script.js` | reveal on scroll, number count-up, mobile menu (page works without it) |
| `favicon.svg`, `robots.txt` | icon, crawler rules |
| `vercel.json` | clean URLs and security headers |

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
