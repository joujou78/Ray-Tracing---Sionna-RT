/* Path cross-section chart: terrain on an effective-Earth curvature, clutter,
   direct ray, and 60 % / 100 % first Fresnel zones. Plain canvas, no deps. */
(function () {
  "use strict";

  /**
   * Prepare geometry for drawing.
   * @param {object} pf    /api/profile response
   * @param {object} p     {htg, hrg, fMHz}
   */
  function geometry(pf, p) {
    const d = pf.d_km, h = pf.h, n = d.length;
    const Dm = d[n - 1] * 1000;
    const Re = 6371000 * pf.k_eff;
    const lam = 299.792458 / p.fMHz;            // metres
    const txTop = h[0] + p.htg, rxTop = h[n - 1] + p.hrg;
    const g = { d, n, Dm, txTop, rxTop, terr: [], obst: [], ray: [], r1: [], clutter: !!pf.clutter };
    let worst = { ratio: Infinity, i: -1 };
    for (let i = 0; i < n; i++) {
      const x = d[i] * 1000;
      const bulge = (x * (Dm - x)) / (2 * Re);
      const t = h[i] + bulge;
      const o = t + (pf.clutter ? pf.clutter[i] : 0);
      const ray = txTop + ((rxTop - txTop) * x) / Dm;
      const r1 = Math.sqrt((lam * x * (Dm - x)) / Dm);
      g.terr.push(t); g.obst.push(o); g.ray.push(ray); g.r1.push(r1);
      if (i > 0 && i < n - 1 && r1 > 0) {
        const ratio = (ray - o) / r1;
        if (ratio < worst.ratio) worst = { ratio, i };
      }
    }
    g.worst = worst;
    g.ctrl = pf.control_points || null;
    return g;
  }

  function niceStep(range, target) {
    const raw = range / target;
    const mag = Math.pow(10, Math.floor(Math.log10(raw)));
    const f = raw / mag;
    return (f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10) * mag;
  }

  function draw(canvas, g, hoverX) {
    const dpr = window.devicePixelRatio || 1;
    const W = canvas.clientWidth, H = canvas.clientHeight;
    if (canvas.width !== Math.round(W * dpr) || canvas.height !== Math.round(H * dpr)) {
      canvas.width = Math.round(W * dpr); canvas.height = Math.round(H * dpr);
    }
    const ctx = canvas.getContext("2d");
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, W, H);
    const m = { l: 58, r: 14, t: 12, b: 30 };
    const pw = W - m.l - m.r, ph = H - m.t - m.b;
    if (pw < 50 || ph < 50) return;

    let lo = Infinity, hi = -Infinity;
    for (let i = 0; i < g.n; i++) {
      lo = Math.min(lo, g.terr[i], g.ray[i] - g.r1[i]);
      hi = Math.max(hi, g.obst[i], g.ray[i] + g.r1[i]);
    }
    hi = Math.max(hi, g.txTop, g.rxTop);
    const pad = (hi - lo) * 0.08 + 2;
    lo -= pad; hi += pad;
    const Dk = g.d[g.n - 1];
    const X = (dk) => m.l + (dk / Dk) * pw;
    const Y = (v) => m.t + (1 - (v - lo) / (hi - lo)) * ph;
    const base = Y(lo);

    // grid + axes
    ctx.font = "11px system-ui, sans-serif";
    ctx.fillStyle = "#8a99a8"; ctx.strokeStyle = "#24303b"; ctx.lineWidth = 1;
    const ys = niceStep(hi - lo, 5);
    for (let v = Math.ceil(lo / ys) * ys; v <= hi; v += ys) {
      ctx.beginPath(); ctx.moveTo(m.l, Y(v)); ctx.lineTo(W - m.r, Y(v)); ctx.stroke();
      ctx.textAlign = "right"; ctx.fillText(`${Math.round(v)} m`, m.l - 6, Y(v) + 4);
    }
    const xs = niceStep(Dk, 8);
    for (let v = 0; v <= Dk + 1e-9; v += xs) {
      ctx.beginPath(); ctx.moveTo(X(v), m.t); ctx.lineTo(X(v), base); ctx.stroke();
      ctx.textAlign = "center"; ctx.fillText(`${+v.toFixed(3)} km`, X(v), H - 10);
    }

    // clutter then terrain fill
    const fill = (arr, color) => {
      ctx.beginPath(); ctx.moveTo(X(0), base);
      for (let i = 0; i < g.n; i++) ctx.lineTo(X(g.d[i]), Y(arr[i]));
      ctx.lineTo(X(Dk), base); ctx.closePath(); ctx.fillStyle = color; ctx.fill();
    };
    if (g.clutter) fill(g.obst, "#3d7a3d");
    fill(g.terr, "#8d6e4c");

    // Fresnel zones
    const band = (k, style, dash) => {
      ctx.save(); ctx.strokeStyle = style; ctx.setLineDash(dash); ctx.lineWidth = 1.4;
      for (const s of [1, -1]) {
        ctx.beginPath();
        for (let i = 0; i < g.n; i++) {
          const y = Y(g.ray[i] + s * k * g.r1[i]);
          i ? ctx.lineTo(X(g.d[i]), y) : ctx.moveTo(X(g.d[i]), y);
        }
        ctx.stroke();
      }
      ctx.restore();
    };
    ctx.save(); ctx.beginPath();
    for (let i = 0; i < g.n; i++) ctx.lineTo(X(g.d[i]), Y(g.ray[i] + 0.6 * g.r1[i]));
    for (let i = g.n - 1; i >= 0; i--) ctx.lineTo(X(g.d[i]), Y(g.ray[i] - 0.6 * g.r1[i]));
    ctx.closePath(); ctx.fillStyle = "rgba(255,214,10,0.08)"; ctx.fill(); ctx.restore();
    band(1.0, "#64d2ff", [2, 3]);
    band(0.6, "#ffd60a", [6, 4]);

    // direct ray + masts
    ctx.strokeStyle = "#ff453a"; ctx.lineWidth = 1.8;
    ctx.beginPath(); ctx.moveTo(X(0), Y(g.txTop)); ctx.lineTo(X(Dk), Y(g.rxTop)); ctx.stroke();
    ctx.strokeStyle = "#fff"; ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(X(0), Y(g.terr[0])); ctx.lineTo(X(0), Y(g.txTop)); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(X(Dk), Y(g.terr[g.n - 1])); ctx.lineTo(X(Dk), Y(g.rxTop)); ctx.stroke();

    // obstructions of the 60 % zone
    ctx.fillStyle = "#ff453a";
    for (let i = 1; i < g.n - 1; i++) {
      if (g.obst[i] > g.ray[i] - 0.6 * g.r1[i]) ctx.fillRect(X(g.d[i]) - 1, Y(g.obst[i]) - 1, 2.5, 2.5);
    }

    // diffraction control points (Bullington construction / dominant edge)
    if (g.ctrl && g.ctrl.points) {
      ctx.save();
      const bp = g.ctrl.points.find((q) => q.kind === "Bullington point");
      if (bp) {
        ctx.strokeStyle = "#bf5af2"; ctx.setLineDash([5, 4]); ctx.lineWidth = 1.4;
        ctx.beginPath(); ctx.moveTo(X(0), Y(g.txTop)); ctx.lineTo(X(bp.d_km), Y(bp.h_m)); ctx.lineTo(X(Dk), Y(g.rxTop)); ctx.stroke();
        ctx.setLineDash([]);
      }
      for (const q of g.ctrl.points) {
        ctx.fillStyle = "#bf5af2"; ctx.strokeStyle = "#fff"; ctx.lineWidth = 1.5;
        ctx.beginPath(); ctx.arc(X(q.d_km), Y(q.h_m), 5, 0, 2 * Math.PI); ctx.fill(); ctx.stroke();
      }
      ctx.restore();
    }

    // hover crosshair
    if (hoverX != null && hoverX >= m.l && hoverX <= W - m.r) {
      const dk = ((hoverX - m.l) / pw) * Dk;
      let i = 0;
      while (i < g.n - 1 && g.d[i + 1] < dk) i++;
      ctx.strokeStyle = "rgba(255,255,255,.5)"; ctx.lineWidth = 1;
      ctx.beginPath(); ctx.moveTo(hoverX, m.t); ctx.lineTo(hoverX, base); ctx.stroke();
      const clr = g.r1[i] > 0 ? (g.ray[i] - g.obst[i]) / g.r1[i] : NaN;
      const txt = [`${g.d[i].toFixed(3)} km`, `ground ${(g.terr[i]).toFixed(1)} m*`,
        `clearance ${(g.ray[i] - g.obst[i]).toFixed(1)} m`, isFinite(clr) ? `${Math.round(clr * 100)} % F1` : ""];
      const bx = Math.min(hoverX + 8, W - m.r - 150);
      ctx.fillStyle = "rgba(15,20,25,.9)"; ctx.fillRect(bx, m.t + 4, 145, 62);
      ctx.fillStyle = "#dce3ea"; ctx.textAlign = "left";
      txt.forEach((t, k) => ctx.fillText(t, bx + 6, m.t + 19 + k * 14));
    }
    ctx.fillStyle = "#8a99a8"; ctx.textAlign = "left";
    ctx.fillText("* heights include effective-Earth bulge", m.l + 4, m.t + ph - 4);
  }

  window.ProfileChart = { geometry, draw };
})();
