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
    var POOL = ["Errors start with ERR_", "Dates are ISO-8601, in UTC", "IDs carry a type prefix, like usr_", "Money is stored as whole cents", "Lists are sorted by id", "Names are trimmed and lowercased"];
    var START = 4, MAXN = 6, EDIT = "Dates are local time, any format";
    var chainL = [], archived = [], nextIdx = START, tampered = false;
    var fp = function (s) {
      var x = 0x811c9dc5;
      for (var i = 0; i < s.length; i++) { x ^= s.charCodeAt(i); x = Math.imul(x, 0x01000193) >>> 0; }
      return ("00000000" + x.toString(16)).slice(-8);
    };
    var mkBlock = function (text, prev) { return { text: text, shown: text, prev: prev, hash: fp(prev + "|" + text), el: null, y: 0, slot: 0 }; };
    var verify = function () {
      for (var i = 0; i < chainL.length; i++) {
        var b = chainL[i], re = fp(b.prev + "|" + b.shown);
        if (re !== b.hash) return { at: i, re: re };
        if (i > 0 && b.prev !== chainL[i - 1].hash) return { at: i, re: re };
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
      el.querySelector(".pv").textContent = "prev " + b.prev + " → ";
      el.querySelector(".hv").textContent = "hash " + b.hash;
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
        msg.textContent = "Lesson " + (bad.at + 1) + " was edited. Its stored fingerprint is " + chainL[bad.at].hash + " but it now computes to " + bad.re + (bad.at < n - 1 ? ". Everything after it can no longer be trusted." : ".");
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
      var prev = "00000000";
      for (var i = 0; i < START; i++) { var b = mkBlock(POOL[i], prev); chainL.push(b); prev = b.hash; }
      paint();
    };
    bAdd.addEventListener("click", function () {
      var last = chainL[chainL.length - 1];
      chainL.push(mkBlock(POOL[nextIdx++ % POOL.length], last.hash));
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
