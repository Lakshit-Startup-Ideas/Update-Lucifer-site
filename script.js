(function () {
  var root = document.documentElement;
  var reduce = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // Reveal-on-scroll. Without JS (or with reduced motion) everything is simply visible.
  // A scroll check (not IntersectionObserver) so elements skipped by an anchor jump are never stuck hidden.
  if (!reduce) {
    root.classList.add("js");
    var pending = Array.prototype.slice.call(document.querySelectorAll(".reveal"));
    var queued = false;
    var check = function () {
      queued = false;
      var line = window.innerHeight * 0.92;
      pending = pending.filter(function (el) {
        if (el.getBoundingClientRect().top < line) { el.classList.add("in"); return false; }
        return true;
      });
      if (!pending.length) {
        window.removeEventListener("scroll", onScroll);
        window.removeEventListener("resize", onScroll);
      }
    };
    var onScroll = function () { if (!queued) { queued = true; requestAnimationFrame(check); } };
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    window.addEventListener("hashchange", onScroll);
    window.addEventListener("load", function () { check(); setTimeout(check, 400); });
    check();
  }

  // Count-up for the headline numbers.
  var counters = document.querySelectorAll("[data-count]");
  if (!reduce && "IntersectionObserver" in window) {
    var co = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (!e.isIntersecting) return;
        var el = e.target, end = parseInt(el.getAttribute("data-count"), 10), t0 = null, dur = 1100;
        co.unobserve(el);
        function tick(ts) {
          if (t0 === null) t0 = ts;
          var p = Math.min((ts - t0) / dur, 1);
          el.textContent = Math.round(end * (1 - Math.pow(1 - p, 3)));
          if (p < 1) requestAnimationFrame(tick);
        }
        el.textContent = "0";
        requestAnimationFrame(tick);
      });
    }, { threshold: 0.6 });
    counters.forEach(function (el) { co.observe(el); });
  }

  var fine = !!(window.matchMedia && window.matchMedia("(hover: hover) and (pointer: fine)").matches);
  var clamp = function (v, a, b) { return Math.min(b, Math.max(a, v)); };

  // Headline: words blur in one by one (CSS does the animation; without JS the heading is plain text).
  var h1 = document.querySelector("h1[data-split]");
  if (h1 && !reduce) {
    var wi = 0;
    var split = function (node) {
      Array.prototype.slice.call(node.childNodes).forEach(function (n) {
        if (n.nodeType === 3) {
          var frag = document.createDocumentFragment();
          n.textContent.split(/(\s+)/).forEach(function (part) {
            if (!part) return;
            if (/^\s+$/.test(part)) { frag.appendChild(document.createTextNode(" ")); return; }
            var s = document.createElement("span");
            s.className = "w"; s.style.setProperty("--i", wi++); s.textContent = part;
            frag.appendChild(s);
          });
          node.replaceChild(frag, n);
        } else if (n.nodeType === 1) { split(n); }
      });
    };
    split(h1);
    h1.classList.add("split");
  }

  // Scroll progress, hero parallax, hero card tilt and the rotating dial: one rAF-batched frame.
  var progress = document.querySelector(".progress");
  var stage = document.querySelector("[data-stage]");
  var app = stage && stage.querySelector(".app");
  var layers = Array.prototype.slice.call(document.querySelectorAll("[data-depth]"));
  var dial = document.getElementById("dial");
  var memory = document.getElementById("memory");
  var hero = document.querySelector(".hero");
  var ptr = { x: 0, y: 0 };
  var tilt = { x: 0, y: 0 };
  var framed = false;
  function frame() {
    framed = false;
    var y = window.pageYOffset;
    var max = document.documentElement.scrollHeight - window.innerHeight;
    if (progress) progress.style.setProperty("--p", max > 0 ? (y / max).toFixed(4) : "0");
    if (reduce) return;
    layers.forEach(function (el) {
      var d = parseFloat(el.getAttribute("data-depth")) || 0;
      el.style.translate = (ptr.x * d).toFixed(1) + "px " + (ptr.y * d * 0.6 + y * d * 0.003).toFixed(1) + "px";
    });
    if (stage) {
      var p = clamp(y / 380, 0, 1);
      stage.style.transform = "perspective(1400px) rotateX(" + (15 * (1 - p) - tilt.y * 4).toFixed(2) + "deg) rotateY(" + (tilt.x * 5).toFixed(2) + "deg) scale(" + (0.94 + 0.06 * p).toFixed(3) + ")";
    }
    if (memory && dial) {
      var r = memory.getBoundingClientRect();
      if (r.bottom > 0 && r.top < window.innerHeight) dial.style.setProperty("--dr", (-r.top * 0.07).toFixed(1) + "deg");
    }
  }
  function request() { if (!framed) { framed = true; requestAnimationFrame(frame); } }
  window.addEventListener("scroll", request, { passive: true });
  window.addEventListener("resize", request);
  frame();

  if (fine && !reduce) {
    if (hero) {
      hero.addEventListener("pointermove", function (e) {
        var r = hero.getBoundingClientRect();
        ptr.x = clamp((e.clientX - r.left) / r.width - 0.5, -0.5, 0.5);
        ptr.y = clamp((e.clientY - r.top) / window.innerHeight - 0.5, -0.6, 0.6);
        request();
      });
      hero.addEventListener("pointerleave", function () { ptr.x = 0; ptr.y = 0; request(); });
    }
    if (app) {
      app.addEventListener("pointermove", function (e) {
        var r = app.getBoundingClientRect();
        var px = (e.clientX - r.left) / r.width, py = (e.clientY - r.top) / r.height;
        tilt.x = px - 0.5; tilt.y = py - 0.5;
        app.style.setProperty("--mx", (px * 100).toFixed(1) + "%");
        app.style.setProperty("--my", (py * 100).toFixed(1) + "%");
        app.style.setProperty("--glare", "1");
        request();
      });
      app.addEventListener("pointerleave", function () { tilt.x = 0; tilt.y = 0; app.style.setProperty("--glare", "0"); request(); });
    }
    // Cards lean toward the pointer and catch a soft highlight.
    Array.prototype.forEach.call(document.querySelectorAll(".card, .step"), function (el) {
      el.addEventListener("pointermove", function (e) {
        var r = el.getBoundingClientRect();
        var px = (e.clientX - r.left) / r.width, py = (e.clientY - r.top) / r.height;
        el.style.setProperty("--mx", (px * 100).toFixed(1) + "%");
        el.style.setProperty("--my", (py * 100).toFixed(1) + "%");
        if (el.classList.contains("reveal") && !el.classList.contains("in")) return;
        el.style.transition = "transform .12s ease-out, opacity .7s ease";
        el.style.transform = "perspective(900px) rotateX(" + ((0.5 - py) * 5).toFixed(2) + "deg) rotateY(" + ((px - 0.5) * 6).toFixed(2) + "deg)";
      });
      el.addEventListener("pointerleave", function () {
        el.style.transition = "transform .5s ease, opacity .7s ease";
        el.style.transform = "";
      });
    });
  }

  // Decimal count-up (the +0.50), and the chart's Replay button.
  function countNum(el, dur) {
    var raw = el.getAttribute("data-num"), end = parseFloat(raw), pre = el.getAttribute("data-prefix") || "";
    var dec = (raw.split(".")[1] || "").length, t0 = null;
    function tick(ts) {
      if (t0 === null) t0 = ts;
      var p = Math.min((ts - t0) / dur, 1);
      el.textContent = pre + (end * (1 - Math.pow(1 - p, 3))).toFixed(dec);
      if (p < 1) requestAnimationFrame(tick);
    }
    el.textContent = pre + (0).toFixed(dec);
    requestAnimationFrame(tick);
  }
  var nums = document.querySelectorAll("[data-num]");
  if (!reduce && "IntersectionObserver" in window) {
    var no = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) { no.unobserve(e.target); countNum(e.target, 1100); } });
    }, { threshold: 0.6 });
    Array.prototype.forEach.call(nums, function (el) { no.observe(el); });
  }
  var replay = document.getElementById("replay");
  var chart = document.querySelector(".chart");
  if (replay && chart) {
    replay.addEventListener("click", function () {
      chart.classList.add("reset");
      void chart.offsetWidth;
      requestAnimationFrame(function () { chart.classList.remove("reset"); });
      if (!reduce && nums[0]) countNum(nums[0], 1100);
    });
  }

  // Hero card: an illustration of one lesson being written, then reused.
  var log = document.getElementById("live-log");
  if (log) {
    var steps = [
      ["task 14 · first try", "✗ expected ERR_QUOTA, got “Quota exceeded”", "bad"],
      ["lesson written", "error messages start with ERR_", "mem"],
      ["task 31 · similar", "recalled 3 lessons from memory", ""],
      ["result", "✓ passed on the first try", "good"]
    ];
    var chainBlk = document.querySelectorAll(".app-chain .blk");
    var timers = [];
    var later = function (fn, ms) { timers.push(setTimeout(fn, ms)); };
    var stop = function () { timers.forEach(clearTimeout); timers = []; };
    var makeLine = function (s, text) {
      var li = document.createElement("li");
      var k = document.createElement("span"); k.className = "k"; k.textContent = s[0];
      var v = document.createElement("span"); v.className = "v " + s[2]; v.textContent = text;
      li.appendChild(k); li.appendChild(v);
      return li;
    };
    var flash = function (on) { if (chainBlk[2]) chainBlk[2].classList.toggle("flash", on); };
    var play = function () {
      stop(); log.innerHTML = ""; flash(false);
      var k = 0;
      (function next() {
        if (k >= steps.length) { later(play, 4200); return; }
        var s = steps[k++], li = makeLine(s, ""), v = li.lastChild, n = 0;
        v.classList.add("caret"); log.appendChild(li);
        (function type() {
          n++; v.textContent = s[1].slice(0, n);
          if (n < s[1].length) { later(type, 22); return; }
          v.classList.remove("caret");
          if (s[2] === "mem") { flash(true); later(function () { flash(false); }, 1600); }
          later(next, 650);
        })();
      })();
    };
    if (reduce || !("IntersectionObserver" in window)) {
      steps.forEach(function (s) { log.appendChild(makeLine(s, s[1])); });
    } else {
      var lo = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) { if (e.isIntersecting) play(); else stop(); });
      }, { threshold: 0.2 });
      lo.observe(log);
      document.addEventListener("visibilitychange", function () { if (document.hidden) stop(); });
    }
  }

  // Memory chain: a small live illustration of a hash-chained store (toy fingerprint, example lessons).
  var mstage = document.getElementById("mem-stage");
  var scene = document.getElementById("scene");
  if (mstage && scene) {
    // Same formula as the real store (memory.py): sha256(parent | version | task_id | kind | text), with short example lesson texts.
    var POOL = [
      { t: "errors-1", k: "failure", x: "Error messages read invalid age: abc" },
      { t: "date-1", k: "failure", x: "Dates are written 05-Mar-2026" },
      { t: "ident-1", k: "failure", x: "Order ids look like ORD-00007" },
      { t: "price-1", k: "failure", x: "Prices show as ₹1,234.56" },
      { t: "price-2", k: "failure", x: "Refunds start with a minus, -₹25.00" },
      { t: "date-2", k: "failure", x: "Birth dates use 04-Jul-1990 too" }
    ];
    var START = 4, MAXN = 6, EDIT = "Dates are written 2026-03-05", GENESIS = new Array(65).join("0");
    var chainL = [], archived = [], nextIdx = START, tampered = false;
    var fp = function (parent, version, task, kind, text) { return sha256([parent, String(version), task, kind, text].join("|")); };
    var mkBlock = function (item, prev, version) {
      return { task: item.t, kind: item.k, version: version, text: item.x, shown: item.x, prev: prev, hash: fp(prev, version, item.t, item.k, item.x), el: null, y: 0, slot: 0 };
    };
    var verify = function () {
      var parent = GENESIS;
      for (var i = 0; i < chainL.length; i++) {
        var b = chainL[i], re = fp(b.prev, b.version, b.task, b.kind, b.shown);
        if (b.prev !== parent || re !== b.hash) return { at: i, re: re };
        parent = b.hash;
      }
      return null;
    };
    var $ = function (id) { return document.getElementById(id); };
    var chip = $("mem-chip"), msg = $("mem-msg"), box = $("mem-status");
    var bAdd = $("m-add"), bTam = $("m-tamper"), bRoll = $("m-roll"), bReset = $("m-reset");
    var build = function (b) {
      var li = document.createElement("li");
      li.innerHTML = '<span class="p-n"></span><div class="p-t"><b></b><code><span class="pv"></span><span class="hv"></span></code></div><span class="p-s"></span>';
      scene.appendChild(li);
      b.el = li;
    };
    var fill = function (b, cls, idx, y, mark, label) {
      if (!b.el) build(b);
      var el = b.el;
      el.className = "plate " + cls;
      el.style.setProperty("--i", idx);
      el.style.setProperty("--y", y);
      el.querySelector(".p-n").textContent = label;
      el.querySelector("b").textContent = b.shown;
      el.querySelector(".pv").textContent = "prev " + b.prev.slice(0, 8) + " → ";
      el.querySelector(".hv").textContent = "hash " + b.hash.slice(0, 8);
      el.querySelector(".p-s").textContent = mark;
    };
    var paint = function () {
      var bad = verify(), n = chainL.length;
      chainL.forEach(function (b, i) {
        var st = "ok", mark = "✓";
        if (bad) { if (i === bad.at) { st = "bad"; mark = "✕"; } else if (i > bad.at) { st = "unver"; mark = "?"; } }
        b.y = ((i - (n - 1) / 2) * 80).toFixed(0); b.slot = i;
        fill(b, st, i, b.y, mark, i + 1);
      });
      archived.forEach(function (b, k) { fill(b, "archived", k, (((n - 1) / 2 + 1 + k) * 80).toFixed(0), "⊘", b.slot + 1); });
      var s = n === 1 ? "" : "s";
      if (bad) {
        chip.textContent = "Chain broken"; chip.className = "chip chip-bad"; box.classList.add("bad");
        msg.textContent = "Lesson " + (bad.at + 1) + " was edited. Its stored hash is " + chainL[bad.at].hash.slice(0, 8) + "… but it now computes to " + bad.re.slice(0, 8) + "…" + (bad.at < n - 1 ? " Everything after it can no longer be trusted." : "");
      } else {
        chip.textContent = "Chain verified"; chip.className = "chip chip-ok"; box.classList.remove("bad");
        msg.textContent = n + " lesson" + s + ", every link checks out." + (archived.length ? " " + archived.length + " archived, not erased." : "");
      }
      bAdd.disabled = n >= MAXN;
      bRoll.disabled = n <= 1;
      bTam.disabled = n < 2;
      bTam.setAttribute("aria-pressed", tampered ? "true" : "false");
      bTam.textContent = tampered ? "Undo the edit" : "Tamper with lesson 2";
    };
    var init = function () {
      scene.innerHTML = ""; chainL = []; archived = []; nextIdx = START; tampered = false;
      var prev = GENESIS;
      for (var i = 0; i < START; i++) { var b = mkBlock(POOL[i], prev, i + 1); chainL.push(b); prev = b.hash; }
      paint();
    };
    bAdd.addEventListener("click", function () {
      var last = chainL[chainL.length - 1];
      chainL.push(mkBlock(POOL[nextIdx++ % POOL.length], last.hash, chainL.length + 1));
      paint();
    });
    bTam.addEventListener("click", function () {
      if (chainL.length < 2) return;
      tampered = !tampered;
      chainL[1].shown = tampered ? EDIT : chainL[1].text;
      paint();
    });
    bRoll.addEventListener("click", function () {
      if (chainL.length <= 1) return;
      var b = chainL.pop();
      if (tampered && chainL.length < 2) { b.shown = b.text; tampered = false; }
      archived.push(b);
      paint();
    });
    bReset.addEventListener("click", init);
    init();

    // 3D rotation: drag (or arrow keys) to turn it; it eases toward the target and drifts gently when idle.
    var rot = { rx: 16, ry: -24, trx: 16, try: -24 }, base = { rx: 16, ry: -24 };
    var drag = false, lx = 0, ly = 0, raf = 0, shown = false;
    var apply = function (idleX, idleY) {
      scene.style.setProperty("--rx", (rot.rx + idleX).toFixed(2) + "deg");
      scene.style.setProperty("--ry", (rot.ry + idleY).toFixed(2) + "deg");
    };
    var loop = function (ts) {
      rot.rx += (rot.trx - rot.rx) * 0.12;
      rot.ry += (rot.try - rot.ry) * 0.12;
      apply(Math.cos(ts / 3100) * 2.5, Math.sin(ts / 2400) * 4);
      raf = requestAnimationFrame(loop);
    };
    var setTarget = function () { rot.trx = base.rx; rot.try = base.ry; if (reduce) { rot.rx = base.rx; rot.ry = base.ry; apply(0, 0); } };
    apply(0, 0);
    mstage.addEventListener("pointerdown", function (e) {
      if (e.target.closest && e.target.closest("button")) return;
      drag = true; lx = e.clientX; ly = e.clientY;
      mstage.classList.add("drag", "touched");
      try { mstage.setPointerCapture(e.pointerId); } catch (err) {}
    });
    mstage.addEventListener("pointermove", function (e) {
      if (drag) {
        base.ry += (e.clientX - lx) * 0.45;
        base.rx = clamp(base.rx - (e.clientY - ly) * 0.3, -30, 55);
        lx = e.clientX; ly = e.clientY;
        setTarget();
      } else if (fine && !reduce) {
        var r = mstage.getBoundingClientRect();
        rot.try = base.ry + ((e.clientX - r.left) / r.width - 0.5) * 28;
        rot.trx = base.rx + (0.5 - (e.clientY - r.top) / r.height) * 18;
      }
    });
    var endDrag = function () { drag = false; mstage.classList.remove("drag"); setTarget(); };
    mstage.addEventListener("pointerup", endDrag);
    mstage.addEventListener("pointercancel", endDrag);
    mstage.addEventListener("pointerleave", function () { if (!drag) setTarget(); });
    mstage.addEventListener("keydown", function (e) {
      var k = e.key, hit = true;
      if (k === "ArrowLeft") base.ry -= 12; else if (k === "ArrowRight") base.ry += 12;
      else if (k === "ArrowUp") base.rx = clamp(base.rx + 8, -30, 55); else if (k === "ArrowDown") base.rx = clamp(base.rx - 8, -30, 55);
      else hit = false;
      if (hit) { e.preventDefault(); mstage.classList.add("touched"); setTarget(); }
    });
    if (!reduce && "IntersectionObserver" in window) {
      var mo = new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          shown = e.isIntersecting;
          if (shown && !raf) raf = requestAnimationFrame(loop);
          if (!shown && raf) { cancelAnimationFrame(raf); raf = 0; }
        });
      }, { threshold: 0.05 });
      mo.observe(mstage);
    }
  }

  // Synchronous SHA-256 of a string (UTF-8). Verified against Python's hashlib; used by the memory demo.
  function sha256(str) {
    var enc = new TextEncoder().encode(str), l = enc.length, bl = l * 8;
    var n = ((l + 9 + 63) >> 6) << 6, m = new Uint8Array(n);
    m.set(enc); m[l] = 0x80;
    var dv = new DataView(m.buffer);
    dv.setUint32(n - 8, Math.floor(bl / 4294967296)); dv.setUint32(n - 4, bl >>> 0);
    var K = [], h = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19], p = 2, c = 0;
    var isP = function (x) { for (var i = 2; i * i <= x; i++) if (x % i === 0) return false; return true; };
    while (c < 64) { if (isP(p)) K[c++] = Math.floor((Math.pow(p, 1 / 3) % 1) * 4294967296) >>> 0; p++; }
    var w = new Array(64);
    for (var o = 0; o < n; o += 64) {
      var i;
      for (i = 0; i < 16; i++) w[i] = dv.getUint32(o + i * 4);
      for (i = 16; i < 64; i++) {
        var a = w[i - 15], b = w[i - 2];
        var s0 = ((a >>> 7) | (a << 25)) ^ ((a >>> 18) | (a << 14)) ^ (a >>> 3);
        var s1 = ((b >>> 17) | (b << 15)) ^ ((b >>> 19) | (b << 13)) ^ (b >>> 10);
        w[i] = (w[i - 16] + s0 + w[i - 7] + s1) >>> 0;
      }
      var A = h[0], B = h[1], C = h[2], D = h[3], E = h[4], F = h[5], G = h[6], H = h[7];
      for (i = 0; i < 64; i++) {
        var S1 = ((E >>> 6) | (E << 26)) ^ ((E >>> 11) | (E << 21)) ^ ((E >>> 25) | (E << 7));
        var t1 = (H + S1 + ((E & F) ^ (~E & G)) + K[i] + w[i]) >>> 0;
        var S0 = ((A >>> 2) | (A << 30)) ^ ((A >>> 13) | (A << 19)) ^ ((A >>> 22) | (A << 10));
        var t2 = (S0 + ((A & B) ^ (A & C) ^ (B & C))) >>> 0;
        H = G; G = F; F = E; E = (D + t1) >>> 0; D = C; C = B; B = A; A = (t1 + t2) >>> 0;
      }
      h[0] = (h[0] + A) >>> 0; h[1] = (h[1] + B) >>> 0; h[2] = (h[2] + C) >>> 0; h[3] = (h[3] + D) >>> 0;
      h[4] = (h[4] + E) >>> 0; h[5] = (h[5] + F) >>> 0; h[6] = (h[6] + G) >>> 0; h[7] = (h[7] + H) >>> 0;
    }
    return h.map(function (x) { return ("00000000" + x.toString(16)).slice(-8); }).join("");
  }

  // Task explorer: filter the task cards by phase and by convention.
  var tgrid = document.querySelector(".tgrid");
  if (tgrid) {
    var fstate = { split: "all", family: "all" };
    var cards = Array.prototype.slice.call(tgrid.querySelectorAll(".tcard"));
    var refilter = function () {
      cards.forEach(function (cd) {
        var ok = (fstate.split === "all" || cd.getAttribute("data-split") === fstate.split) && (fstate.family === "all" || cd.getAttribute("data-family") === fstate.family);
        cd.hidden = !ok;
      });
    };
    Array.prototype.forEach.call(document.querySelectorAll(".fchip"), function (btn) {
      btn.addEventListener("click", function () {
        var key = btn.getAttribute("data-key");
        fstate[key] = btn.getAttribute("data-val");
        Array.prototype.forEach.call(document.querySelectorAll('.fchip[data-key="' + key + '"]'), function (o) { o.classList.toggle("on", o === btn); });
        refilter();
      });
    });
    // Opening a card from a heat tile must show it even if a filter hides it.
    var showHidden = function () {
      var id = location.hash.slice(1), el = id && document.getElementById(id);
      if (el && el.hidden) {
        fstate.split = "all"; fstate.family = "all";
        Array.prototype.forEach.call(document.querySelectorAll(".fchip"), function (o) { o.classList.toggle("on", o.getAttribute("data-val") === "all"); });
        refilter(); el.scrollIntoView();
      }
    };
    window.addEventListener("hashchange", showHidden);
  }

  // Proof page: download rows.json, fingerprint it, rebuild the table and rerun the paired bootstrap, all in the browser.
  var vrun = document.getElementById("v-run");
  if (vrun) {
    var vstate = document.getElementById("v-state");
    var setState = function (t, cls) { vstate.textContent = t; vstate.className = "v-state " + (cls || ""); };
    var fmt = function (x) { return (x >= 0 ? "+" : "−") + Math.abs(x).toFixed(2); };
    var rng = function (a) { return function () { a |= 0; a = a + 0x6D2B79F5 | 0; var t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; };
    var taskMeans = function (rows, cond) {
      var m = {}, o = {};
      rows.forEach(function (r) { if (r.condition === cond && (r.phase === "similar" || r.phase === "transfer")) (m[r.task_id] = m[r.task_id] || []).push(r.pass_at_1 ? 1 : 0); });
      Object.keys(m).forEach(function (k) { o[k] = m[k].reduce(function (x, y) { return x + y; }, 0) / m[k].length; });
      return o;
    };
    var boot = function (a, b, N, seed) {
      var t = Object.keys(a).filter(function (k) { return k in b; }).sort();
      var d = t.map(function (k) { return b[k] - a[k]; }), r = rng(seed), ms = [];
      for (var i = 0; i < N; i++) { var sum = 0; for (var j = 0; j < d.length; j++) sum += d[(r() * d.length) | 0]; ms.push(sum / d.length); }
      ms.sort(function (x, y) { return x - y; });
      return [d.reduce(function (x, y) { return x + y; }, 0) / d.length, ms[Math.floor(0.025 * N)], ms[Math.floor(0.975 * N) - 1], d.length];
    };
    vrun.addEventListener("click", function () {
      vrun.disabled = true; setState("Downloading rows.json…", "busy");
      fetch("data/rows.json").then(function (res) { if (!res.ok) throw new Error("HTTP " + res.status); return res.arrayBuffer(); }).then(function (buf) {
        var rows = JSON.parse(new TextDecoder().decode(buf));
        var hashP = window.crypto && crypto.subtle
          ? crypto.subtle.digest("SHA-256", buf).then(function (d) { return Array.prototype.map.call(new Uint8Array(d), function (x) { return ("0" + x.toString(16)).slice(-2); }).join(""); })
          : Promise.resolve("(needs https or localhost)");
        return hashP.then(function (hash) { return { rows: rows, hash: hash }; });
      }).then(function (res) {
        var rows = res.rows;
        document.getElementById("v-rows").textContent = rows.length;
        document.getElementById("v-hash").textContent = res.hash;
        var body = ["experience", "similar", "transfer", "replay"].map(function (ph) {
          var cells = ["baseline", "lucifer", "irrelevant"].map(function (c) {
            var rs = rows.filter(function (r) { return r.condition === c && r.phase === ph; });
            var n = rs.filter(function (r) { return r.pass_at_1; }).length;
            return "<td>" + n + " of " + rs.length + " (" + Math.round(100 * n / rs.length) + "%)</td>";
          });
          return "<tr><td><b>" + ph.charAt(0).toUpperCase() + ph.slice(1) + "</b></td>" + cells.join("") + "</tr>";
        }).join("");
        document.querySelector("#v-table tbody").innerHTML = body;
        setState("Running 10,000 bootstrap resamples…", "busy");
        setTimeout(function () {
          var B = taskMeans(rows, "baseline"), L = taskMeans(rows, "lucifer"), I = taskMeans(rows, "irrelevant");
          var r1 = boot(B, L, 10000, 1), r2 = boot(I, L, 10000, 1);
          document.getElementById("v-eff").textContent = fmt(r1[0]);
          document.getElementById("v-ci").textContent = "95% interval " + fmt(r1[1]) + " to " + fmt(r1[2]) + " · " + r1[3] + " tasks";
          document.getElementById("v-eff2").textContent = fmt(r2[0]);
          document.getElementById("v-ci2").textContent = "95% interval " + fmt(r2[1]) + " to " + fmt(r2[2]) + " · " + r2[3] + " tasks";
          var seedsU = rows.map(function (r) { return r.seed; }).filter(function (v, i, a) { return a.indexOf(v) === i; }).sort();
          var pick = seedsU.filter(function (v, i) { return i % 2 === 0; });
          var byTask = {};
          rows.forEach(function (r) { if (r.condition === "baseline" && r.phase !== "experience" && pick.indexOf(r.seed) > -1) (byTask[r.task_id] = byTask[r.task_id] || []).push(r.pass_at_1 ? 1 : 0); });
          var mastered = Object.keys(byTask).filter(function (k) { return byTask[k].reduce(function (x, y) { return x + y; }, 0) / byTask[k].length >= 0.8; }).length;
          document.getElementById("v-gate").textContent = mastered === 0
            ? "Retention gate: inconclusive. The baseline masters 0 tasks (at least 80% first try on half the seeds), so there is nothing to lose."
            : "Retention gate: the baseline masters " + mastered + " task(s); see the published report for the verdict.";
          var match = fmt(r1[0]) === "+0.50" && fmt(r1[1]) === "+0.30" && fmt(r1[2]) === "+0.70";
          setState(match ? "Done · matches the published +0.50 [+0.30, +0.70]" : "Done · differs from the published figures, see the numbers above", match ? "ok" : "err");
          vrun.disabled = false; vrun.textContent = "Run it again";
        }, 30);
      }).catch(function (err) { setState("Could not load the data: " + err.message, "err"); vrun.disabled = false; });
    });
  }

  // Mobile menu.
  var btn = document.querySelector(".menu-btn");
  var links = document.getElementById("nav-links");
  if (btn && links) {
    function setOpen(open) {
      btn.setAttribute("aria-expanded", open ? "true" : "false");
      btn.setAttribute("aria-label", open ? "Close menu" : "Open menu");
      links.classList.toggle("open", open);
    }
    btn.addEventListener("click", function () { setOpen(btn.getAttribute("aria-expanded") !== "true"); });
    links.addEventListener("click", function (e) { if (e.target.closest("a")) setOpen(false); });
    document.addEventListener("keydown", function (e) { if (e.key === "Escape") setOpen(false); });
  }
})();
