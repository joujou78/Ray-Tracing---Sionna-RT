/* RF Pathloss Calculator: point-to-point path with terrain cross-section.
 * Uses POST /api/profile (same engine as the coverage map's probes). */
(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const num = (id) => parseFloat($(id).value);
  const DEG = Math.PI / 180;

  const state = { tx: null, rx: null, mode: null, result: null, req: null, geom: null, hover: null, auto: false };

  // ------------------------------------------------------------------- map
  const map = L.map("map").setView([54.5, -3.5], 6);
  const base = {
    "OpenStreetMap": L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19, attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' }),
    "OpenTopoMap": L.tileLayer("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", {
      maxZoom: 17, attribution: "Map data &copy; OpenStreetMap contributors, SRTM | Style &copy; OpenTopoMap (CC-BY-SA)" }),
  };
  base["OpenStreetMap"].addTo(map);
  L.control.layers(base, null, { position: "topright" }).addTo(map);
  L.control.scale({ imperial: false }).addTo(map);

  const icons = {
    tx: L.divIcon({ className: "", html: '<div class="tx-icon"></div>', iconSize: [22, 22], iconAnchor: [11, 11] }),
    rx: L.divIcon({ className: "", html: '<div class="rx-icon"></div>', iconSize: [18, 18], iconAnchor: [9, 9] }),
  };
  const markers = { tx: null, rx: null };
  const line = L.polyline([], { color: "#ff453a", weight: 2, dashArray: "6 5" }).addTo(map);
  const ctrlLayer = L.layerGroup().addTo(map);

  // ------------------------------------------------------- grid references
  /** Maidenhead locator (6 chars) from lat/lon. */
  function toLocator(lat, lon) {
    const A = "ABCDEFGHIJKLMNOPQRSTUVWX";
    let x = lon + 180, y = lat + 90;
    const f1 = A[Math.floor(x / 20)], f2 = A[Math.floor(y / 10)];
    x %= 20; y %= 10;
    const s1 = Math.floor(x / 2), s2 = Math.floor(y);
    x = (x % 2) * 12; y = (y % 1) * 24;
    return f1 + f2 + s1 + s2 + A[Math.floor(x)] + A[Math.floor(y)];
  }
  /** Centre of a 4/6/8-character Maidenhead locator, or null. */
  function fromLocator(s) {
    const m = /^([A-R]{2})(\d{2})(?:([A-X]{2})(\d{2})?)?$/i.exec(s.replace(/\s+/g, ""));
    if (!m) return null;
    const u = m[1].toUpperCase();
    let lon = (u.charCodeAt(0) - 65) * 20 - 180 + (+m[2][0]) * 2;
    let lat = (u.charCodeAt(1) - 65) * 10 - 90 + (+m[2][1]);
    let w = 2, h = 1;
    if (m[3]) {
      const sub = m[3].toUpperCase();
      lon += (sub.charCodeAt(0) - 65) * (2 / 24); lat += (sub.charCodeAt(1) - 65) * (1 / 24);
      w = 2 / 24; h = 1 / 24;
      if (m[4]) { lon += (+m[4][0]) * (w / 10); lat += (+m[4][1]) * (h / 10); w /= 10; h /= 10; }
    }
    return { lat: lat + h / 2, lon: lon + w / 2 };
  }
  async function gridLabel(lat, lon) {
    try {
      const j = await (await fetch(`/api/grid?lat=${lat}&lon=${lon}`)).json();
      if (j.osgb) return `${j.osgb.replace(/^(\S+) (\d{3})\d* (\d{3})\d*$/, "$1 $2 $3")}  ·  ${toLocator(lat, lon)}`;
    } catch (e) { /* fall through */ }
    return toLocator(lat, lon);
  }
  /** OS National Grid reference first (GB), then Maidenhead locator. */
  async function parseGrid(text) {
    const t = text.split("·")[0].trim();
    if (!t) return null;
    if (/^[HJNOST][A-HJ-Z](\d{2})*$/i.test(t.replace(/\s+/g, ""))) {
      const r = await fetch(`/api/grid?ref=${encodeURIComponent(t)}`);
      if (r.ok) { const j = await r.json(); return { lat: j.lat, lon: j.lon }; }
    }
    return fromLocator(t);
  }

  // ----------------------------------------------------------------- sites
  async function setSite(which, lat, lon, opts = {}) {
    state[which] = { lat: +lat, lon: +lon };
    $(`${which}-lat`).value = state[which].lat.toFixed(5);
    $(`${which}-lon`).value = state[which].lon.toFixed(5);
    if (!markers[which]) {
      markers[which] = L.marker([lat, lon], { draggable: true, icon: icons[which], zIndexOffset: which === "tx" ? 1000 : 900 })
        .addTo(map).bindTooltip(which.toUpperCase(), { direction: "top", offset: [0, -10] });
      markers[which].on("dragend", () => { const ll = markers[which].getLatLng(); setSite(which, ll.lat, ll.lng); });
    } else {
      markers[which].setLatLng([lat, lon]);
    }
    updateLine();
    const label = await gridLabel(lat, lon);
    $(`${which}-grid`).value = label;
    $(`${which}-grid`).dataset.auto = label;   // programmatic value: not a user edit
    fetch(`/api/elevation?lat=${lat}&lon=${lon}`).then((r) => r.json())
      .then((j) => { $(`${which}-ground`).value = `${j.elevation_m.toFixed(1)} m`; })
      .catch(() => { $(`${which}-ground`).value = "n/a"; });
    if (!opts.noCalc) autoCalc();
  }

  function updateLine() {
    if (state.tx && state.rx) {
      line.setLatLngs([[state.tx.lat, state.tx.lon], [state.rx.lat, state.rx.lon]]);
    } else line.setLatLngs([]);
  }

  function setMode(m) {
    state.mode = state.mode === m ? null : m;
    $("btn-place-tx").classList.toggle("active", state.mode === "tx");
    $("btn-place-rx").classList.toggle("active", state.mode === "rx");
    map.getContainer().classList.toggle("placing", !!state.mode);
  }

  map.on("click", (e) => {
    if (!state.mode) return;
    const which = state.mode;
    setMode(which);
    setSite(which, e.latlng.lat, e.latlng.lng);
    if (which === "tx" && !state.rx) setMode("rx");   // natural next step
  });

  // ------------------------------------------------------------- calculate
  function request() {
    const k = num("kfac"), s = $("samples").value;
    return {
      tx_lat: state.tx.lat, tx_lon: state.tx.lon, rx_lat: state.rx.lat, rx_lon: state.rx.lon,
      freq_mhz: num("freq"), tx_height: num("tx-h"), rx_height: num("rx-h"), model: $("model").value,
      time_pct: num("time-pct"), loc_pct: num("loc-pct"), polarization: $("pol").value,
      k_factor: isFinite(k) ? k : null, clutter: $("clutter").checked, samples: s ? +s : null,
    };
  }

  let calcTimer = null;
  function autoCalc() {
    if (!state.auto) return;
    clearTimeout(calcTimer);
    calcTimer = setTimeout(calculate, 300);
  }

  async function calculate() {
    if (!state.tx || !state.rx) { status("Place TX and RX on the map, then calculate.", true); return; }
    const req = request();
    $("btn-calc").disabled = true; $("busy").hidden = false;
    try {
      const r = await fetch("/api/profile", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(req) });
      if (!r.ok) throw new Error((await r.json()).detail || r.statusText);
      state.result = await r.json(); state.req = req; state.auto = true;
      showResults();
      status("");
    } catch (e) {
      status(String(e.message || e), true);
    } finally {
      $("btn-calc").disabled = false; $("busy").hidden = true;
    }
  }

  function status(msg, err = false) { $("status").textContent = msg; $("status").style.color = err ? "var(--danger)" : ""; }
  const dB = (v) => (v == null || !isFinite(v) ? "-" : `${v.toFixed(1)} dB`);

  function showResults() {
    const d = state.result, req = state.req, det = d.details || {};
    const gt = num("tx-g"), gr = num("rx-g");
    const back = (d.bearing_deg + 180) % 360;   // approximate reverse azimuth
    const rev = reverseBearing(state.tx, state.rx);
    $("r-dist").textContent = `${(d.distance_m / 1000).toFixed(3)} km`;
    $("r-brg").textContent = `${d.bearing_deg.toFixed(1)}° / ${(isFinite(rev) ? rev : back).toFixed(1)}°`;
    $("r-fsl").textContent = dB(det.Lbfs);
    $("r-ld").textContent = req.model === "fspl" ? "0.0 dB" : dB(det.Ld);
    $("r-lb").textContent = dB(d.lb);
    $("r-net").textContent = dB(d.lb - gt - gr);
    const prx = num("tx-p") - num("tx-l") + gt - d.lb + gr - num("rx-l");
    $("r-prx").textContent = isFinite(prx) ? `${prx.toFixed(1)} dBm` : "-";

    state.geom = ProfileChart.geometry(d, { htg: req.tx_height, hrg: req.rx_height, fMHz: req.freq_mhz });
    const w = state.geom.worst, los = d.control_points ? d.control_points.los : w.ratio > 0;
    const el = $("r-los");
    if (!los) { el.textContent = "Obstructed (beyond LOS)"; el.className = "bad"; }
    else if (w.ratio >= 0.6) { el.textContent = `LOS, ${Math.round(w.ratio * 100)} % F1 clear`; el.className = "ok"; }
    else { el.textContent = `LOS, ${Math.round(w.ratio * 100)} % F1 clear`; el.className = "mid"; }

    const extra = [];
    if (det.trans_horizon != null) extra.push(det.trans_horizon ? "Path type (P.1812 §4): trans-horizon" : "Path type (P.1812 §4): line of sight");
    if (req.model === "p1812") extra.push(`Lbs ${dB(det.Lbs)} · Lba ${dB(det.Lba)} · ΔN ${d.dn.toFixed(1)} · N₀ ${d.n0.toFixed(1)} · p ${req.time_pct}% · pL ${req.loc_pct}%`);
    extra.push(`k used ${d.k_eff.toFixed(3)} · ${d.n_points} samples @ ${d.sample_m.toFixed(1)} m · TX/RX ground ${d.tx_ground.toFixed(1)} / ${d.rx_ground.toFixed(1)} m`);
    if (d.control_points) {
      for (const p of d.control_points.points) {
        extra.push(`◆ ${p.kind}: ${p.d_km.toFixed(3)} km, ${p.h_m.toFixed(1)} m${p.nu != null ? `, ν = ${p.nu.toFixed(2)}` : ""}`);
      }
    }
    $("r-extra").innerHTML = extra.join("<br>");
    $("xs-info").textContent = `${(d.distance_m / 1000).toFixed(3)} km · Lb ${d.lb.toFixed(1)} dB · ${req.model} · ${req.freq_mhz} MHz`;

    // control points on the map
    ctrlLayer.clearLayers();
    for (const p of (d.control_points ? d.control_points.points : [])) {
      if (p.kind === "Bullington point") continue;   // virtual edge, not a ground location
      const ll = along(state.tx, d.bearing_deg, p.d_km * 1000);
      L.circleMarker(ll, { radius: 6, color: "#fff", weight: 1.5, fillColor: "#bf5af2", fillOpacity: 1 })
        .bindTooltip(`${p.kind} · ${p.d_km.toFixed(2)} km`).addTo(ctrlLayer);
    }
    draw();
  }

  function along(o, brg, dist) {
    const R = 6371008.8, p1 = o.lat * DEG, l1 = o.lon * DEG, th = brg * DEG, dl = dist / R;
    const p2 = Math.asin(Math.sin(p1) * Math.cos(dl) + Math.cos(p1) * Math.sin(dl) * Math.cos(th));
    const l2 = l1 + Math.atan2(Math.sin(th) * Math.sin(dl) * Math.cos(p1), Math.cos(dl) - Math.sin(p1) * Math.sin(p2));
    return [p2 / DEG, l2 / DEG];
  }
  function reverseBearing(a, b) {
    const p1 = b.lat * DEG, p2 = a.lat * DEG, dl = (a.lon - b.lon) * DEG;
    const y = Math.sin(dl) * Math.cos(p2), x = Math.cos(p1) * Math.sin(p2) - Math.sin(p1) * Math.cos(p2) * Math.cos(dl);
    return (Math.atan2(y, x) / DEG + 360) % 360;
  }

  function draw() {
    if (state.geom && !$("xs").hidden) ProfileChart.draw($("pf-canvas"), state.geom, state.hover);
  }
  $("pf-canvas").addEventListener("mousemove", (e) => { state.hover = e.offsetX; draw(); });
  $("pf-canvas").addEventListener("mouseleave", () => { state.hover = null; draw(); });
  window.addEventListener("resize", draw);

  // ---------------------------------------------------------------- inputs
  function modelUi() {
    const p1812 = $("model").value === "p1812";
    $("p1812-fields").hidden = !p1812;
    $("k-note").hidden = !p1812;
    $("kfac").disabled = p1812 || $("model").value === "fspl";
  }
  $("model").addEventListener("change", () => { modelUi(); autoCalc(); });
  ["freq", "kfac", "samples", "pol", "time-pct", "loc-pct", "clutter", "tx-h", "rx-h"]
    .forEach((id) => $(id).addEventListener("change", autoCalc));
  ["tx-g", "rx-g", "tx-p", "tx-l", "rx-l"].forEach((id) => $(id).addEventListener("input", () => { if (state.result) showResults(); }));
  $("show-xs").addEventListener("change", () => {
    $("xs").hidden = !$("show-xs").checked; map.invalidateSize(); draw();
  });
  for (const w of ["tx", "rx"]) {
    $(`${w}-lat`).addEventListener("change", () => isFinite(num(`${w}-lat`)) && isFinite(num(`${w}-lon`)) && setSite(w, num(`${w}-lat`), num(`${w}-lon`)));
    $(`${w}-lon`).addEventListener("change", () => isFinite(num(`${w}-lat`)) && isFinite(num(`${w}-lon`)) && setSite(w, num(`${w}-lat`), num(`${w}-lon`)));
    $(`${w}-grid`).addEventListener("change", async () => {
      const el = $(`${w}-grid`);
      if (el.value === el.dataset.auto) return;   // blur after a programmatic update
      const p = await parseGrid(el.value);
      if (p) { await setSite(w, p.lat, p.lon); fitPath(); }
      else status(`Could not read grid reference "${$(`${w}-grid`).value}".`, true);
    });
  }
  function fitPath() {
    const pts = [state.tx, state.rx].filter(Boolean).map((p) => [p.lat, p.lon]);
    if (pts.length === 2) map.fitBounds(pts, { padding: [40, 40] });
    else if (pts.length === 1) map.setView(pts[0], 12);
  }

  $("btn-place-tx").onclick = () => setMode("tx");
  $("btn-place-rx").onclick = () => setMode("rx");
  $("btn-calc").onclick = calculate;
  $("btn-notes").onclick = () => $("notes").showModal();
  $("btn-swap").onclick = async () => {
    if (!state.tx || !state.rx) return;
    const t = state.tx, r = state.rx;
    const th = $("tx-h").value, tg = $("tx-g").value;
    $("tx-h").value = $("rx-h").value; $("tx-g").value = $("rx-g").value;
    $("rx-h").value = th; $("rx-g").value = tg;
    await setSite("tx", r.lat, r.lon, { noCalc: true });
    await setSite("rx", t.lat, t.lon);
  };
  $("btn-clear").onclick = () => {
    for (const w of ["tx", "rx"]) {
      if (markers[w]) map.removeLayer(markers[w]);
      markers[w] = null; state[w] = null;
      ["lat", "lon", "grid"].forEach((f) => { $(`${w}-${f}`).value = ""; });
      $(`${w}-ground`).value = "-";
    }
    state.result = null; state.geom = null; state.auto = false;
    line.setLatLngs([]); ctrlLayer.clearLayers();
    document.querySelectorAll("#results b").forEach((b) => { b.textContent = "-"; b.className = ""; });
    $("r-extra").innerHTML = ""; $("xs-info").textContent = "No path calculated";
    const c = $("pf-canvas"); c.getContext("2d").clearRect(0, 0, c.width, c.height);
    status("Place TX and RX on the map, then calculate.");
  };

  // ------------------------------------------------------------- save/load
  const FIELDS = ["freq", "kfac", "samples", "pol", "model", "time-pct", "loc-pct", "clutter", "show-xs",
    "tx-h", "tx-g", "rx-h", "rx-g", "tx-p", "tx-l", "rx-l"];
  $("btn-save").onclick = () => {
    const inputs = {};
    for (const f of FIELDS) inputs[f] = $(f).type === "checkbox" ? $(f).checked : $(f).value;
    const cfg = { app: "rf-pathloss", version: 1, saved: new Date().toISOString(), tx: state.tx, rx: state.rx, inputs };
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([JSON.stringify(cfg, null, 2)], { type: "application/json" }));
    a.download = "path-config.json"; a.click();
  };
  $("file-load").onchange = async (e) => {
    const f = e.target.files[0];
    if (!f) return;
    try {
      const cfg = JSON.parse(await f.text());
      if (cfg.app !== "rf-pathloss") throw new Error("Not a path calculator config file");
      for (const [k, v] of Object.entries(cfg.inputs || {})) {
        if (!$(k)) continue;
        if ($(k).type === "checkbox") $(k).checked = !!v; else $(k).value = v;
      }
      modelUi();
      $("xs").hidden = !$("show-xs").checked;
      if (cfg.tx) await setSite("tx", cfg.tx.lat, cfg.tx.lon, { noCalc: true });
      if (cfg.rx) await setSite("rx", cfg.rx.lat, cfg.rx.lon, { noCalc: true });
      fitPath();
      if (cfg.tx && cfg.rx) calculate();
    } catch (err) { status(`Load failed: ${err.message}`, true); }
    e.target.value = "";
  };

  modelUi();
  // Deep link: ?tx=lat,lon&rx=lat,lon calculates immediately
  const q = new URLSearchParams(location.search);
  if (q.get("tx") && q.get("rx")) {
    const [a, b] = q.get("tx").split(",").map(Number), [c, d] = q.get("rx").split(",").map(Number);
    Promise.all([setSite("tx", a, b, { noCalc: true }), setSite("rx", c, d, { noCalc: true })]).then(() => { fitPath(); calculate(); });
  }
})();
