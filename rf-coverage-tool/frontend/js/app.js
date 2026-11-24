/* RF Coverage Mapper - frontend controller.
 *
 * The backend returns basic transmission loss Lb (dB) on a Web-Mercator raster.
 * Received power is formed here, so link-budget, antenna pattern and colour
 * changes re-render instantly without a new propagation run:
 *
 *   Prx = Ptx + Gtx - Lftx + Gpattern(azimuth) - Lb + Grx - Lfrx      [dBm]
 */
(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const num = (id) => parseFloat($(id).value);
  const MERC_R = 6378137;
  const DEG = Math.PI / 180;

  // ------------------------------------------------------------------ state
  const state = {
    tx: { lat: 52.9548, lon: -1.1581 },
    mode: null,               // "tx" | "probe" | null
    result: null,             // {lb, W, H, bounds, az, meta, inputs}
    overlay: null,
    probes: [],               // {id, lat, lon, marker, data}
    nextProbe: 1,
    profileProbe: null,
  };

  // -------------------------------------------------------------------- map
  const map = L.map("map", { zoomControl: true, preferCanvas: false }).setView([state.tx.lat, state.tx.lon], 11);
  const base = {
    "OpenStreetMap": L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19, crossOrigin: "anonymous",
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }),
    "OpenTopoMap": L.tileLayer("https://{s}.tile.opentopomap.org/{z}/{x}/{y}.png", {
      maxZoom: 17, crossOrigin: "anonymous",
      attribution: 'Map data &copy; OpenStreetMap contributors, SRTM | Style &copy; <a href="https://opentopomap.org">OpenTopoMap</a> (CC-BY-SA)',
    }),
    "Esri World Imagery": L.tileLayer("https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}", {
      maxZoom: 19, crossOrigin: "anonymous", attribution: "Tiles &copy; Esri",
    }),
  };
  base["OpenStreetMap"].addTo(map);
  L.control.layers(base, null, { position: "topright" }).addTo(map);
  L.control.scale({ imperial: false }).addTo(map);

  const txMarker = L.marker([state.tx.lat, state.tx.lon], {
    draggable: true, zIndexOffset: 1000,
    icon: L.divIcon({ className: "", html: '<div class="tx-icon"></div>', iconSize: [22, 22], iconAnchor: [11, 11] }),
  }).addTo(map).bindTooltip("TX", { direction: "top", offset: [0, -10] });

  txMarker.on("dragend", () => {
    const ll = txMarker.getLatLng();
    setTx(ll.lat, ll.lng);
  });

  // Legend control
  const Legend = L.Control.extend({
    options: { position: "bottomright" },
    onAdd() {
      const div = L.DomUtil.create("div", "legend");
      div.innerHTML = '<div><b>Received power (dBm)</b></div><canvas id="legend-canvas" width="230" height="44"></canvas>';
      L.DomEvent.disableClickPropagation(div);
      return div;
    },
  });
  new Legend().addTo(map);

  // Cursor read-out control
  const Readout = L.Control.extend({
    options: { position: "topright" },
    onAdd() {
      const div = L.DomUtil.create("div", "readout");
      div.id = "readout";
      div.innerHTML = "Move over the map";
      return div;
    },
  });
  new Readout().addTo(map);

  // ------------------------------------------------------------ geo helpers
  function distBearing(lat1, lon1, lat2, lon2) {
    const p1 = lat1 * DEG, p2 = lat2 * DEG, dl = (lon2 - lon1) * DEG;
    const a = Math.sin((p2 - p1) / 2) ** 2 + Math.cos(p1) * Math.cos(p2) * Math.sin(dl / 2) ** 2;
    const d = 2 * 6371008.8 * Math.asin(Math.min(1, Math.sqrt(a)));
    const y = Math.sin(dl) * Math.cos(p2);
    const x = Math.cos(p1) * Math.sin(p2) - Math.sin(p1) * Math.cos(p2) * Math.cos(dl);
    return { d, brg: ((Math.atan2(y, x) / DEG) + 360) % 360 };
  }
  const mercY = (lat) => MERC_R * Math.log(Math.tan(Math.PI / 4 + (lat * DEG) / 2));
  const mercX = (lon) => MERC_R * lon * DEG;
  const invMercY = (y) => (2 * Math.atan(Math.exp(y / MERC_R)) - Math.PI / 2) / DEG;

  // ------------------------------------------------------------ link budget
  function linkParams() {
    return {
      ptx: num("tx-p"), gtx: num("tx-g"), lftx: num("tx-l"),
      grx: num("rx-g"), lfrx: num("rx-l"),
      pattern: $("pattern").value, az: num("az"), bw: Math.max(num("bw"), 1), fb: num("fb"),
    };
  }
  /** Relative pattern gain (dB): parabolic main lobe limited by front-to-back ratio. */
  function patternGain(brg, lp) {
    if (lp.pattern !== "dir") return 0;
    let a = ((brg - lp.az + 540) % 360) - 180;
    return -Math.min(12 * (a / lp.bw) ** 2, lp.fb);
  }
  function rxPower(lb, brg, lp, rx = { g: lp.grx, l: lp.lfrx }) {
    return lp.ptx + lp.gtx - lp.lftx + patternGain(brg, lp) - lb + rx.g - rx.l;
  }

  // ---------------------------------------------------------------- inputs
  function setTx(lat, lon, pan = false) {
    state.tx = { lat: +lat, lon: +lon };
    $("tx-lat").value = state.tx.lat.toFixed(5);
    $("tx-lon").value = state.tx.lon.toFixed(5);
    txMarker.setLatLng([state.tx.lat, state.tx.lon]);
    if (pan) map.panTo([state.tx.lat, state.tx.lon]);
    fetchGround();
    markStale();
    refreshProbes();
  }

  let groundTimer = null;
  function fetchGround() {
    clearTimeout(groundTimer);
    groundTimer = setTimeout(async () => {
      try {
        const r = await fetch(`/api/elevation?lat=${state.tx.lat}&lon=${state.tx.lon}&terrain=${$("terrain").value}`);
        const j = await r.json();
        $("tx-ground").value = `${j.elevation_m.toFixed(1)} m`;
      } catch (e) { $("tx-ground").value = "n/a"; }
    }, 250);
  }

  function computeInputs() {
    const k = parseFloat($("kfac").value);
    const req = {
      lat: state.tx.lat, lon: state.tx.lon,
      freq_mhz: num("freq"), tx_height: num("tx-h"), rx_height: num("rx-h"),
      model: $("model").value, area: $("area").value, radius_km: num("radius"),
      resolution: $("res").value, time_pct: num("time-pct"), loc_pct: num("loc-pct"),
      sigma_loc: num("sigma-l"), polarization: $("pol").value,
      k_factor: isFinite(k) ? k : null, terrain: $("terrain").value, clutter: $("clutter").checked,
    };
    if (req.area === "view") {
      const b = map.getBounds();
      req.bbox = [b.getSouth(), b.getWest(), b.getNorth(), b.getEast()];
    }
    return req;
  }

  function markStale() {
    if (!state.result) return;
    const now = computeInputs(), then = state.result.inputs;
    const keys = ["lat", "lon", "freq_mhz", "tx_height", "rx_height", "model", "time_pct", "loc_pct",
      "sigma_loc", "polarization", "k_factor", "terrain", "clutter"];
    $("stale").hidden = keys.every((k) => now[k] === then[k]);
  }

  function updateEirp() {
    const lp = linkParams();
    const eirp = lp.ptx + lp.gtx - lp.lftx;
    $("eirp").value = `${eirp.toFixed(1)} dBm (${(10 ** ((eirp - 30) / 10)).toPrecision(3)} W)`;
  }

  // ---------------------------------------------------------------- compute
  async function compute() {
    const req = computeInputs();
    const btn = $("btn-compute");
    btn.disabled = true;
    setBusy(true, `Computing ${req.model.toUpperCase()} (${req.resolution})…`);
    setStatus("");
    const t0 = performance.now();
    try {
      const r = await fetch("/api/coverage", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(req),
      });
      if (!r.ok) throw new Error((await r.json()).detail || r.statusText);
      const j = await r.json();
      const bin = atob(j.lb_b64);
      const buf = new ArrayBuffer(bin.length);
      const u8 = new Uint8Array(buf);
      for (let i = 0; i < bin.length; i++) u8[i] = bin.charCodeAt(i);
      const lb = new Float32Array(buf);
      state.result = { lb, W: j.width, H: j.height, bounds: j.bounds, meta: j.meta, inputs: req, az: bearingsFor(j) };
      $("tx-ground").value = `${j.meta.tx_ground_amsl.toFixed(1)} m`;
      render();
      showMeta(j.meta, (performance.now() - t0) / 1000);
      $("stale").hidden = true;
      refreshProbes();
    } catch (e) {
      setStatus(String(e.message || e), true);
    } finally {
      btn.disabled = false;
      setBusy(false);
    }
  }

  /** Bearing from TX to every pixel centre (for the azimuth pattern). */
  function bearingsFor(j) {
    const [s, w, n, e] = j.bounds;
    const x0 = mercX(w), x1 = mercX(e), y0 = mercY(s), y1 = mercY(n);
    const W = j.width, H = j.height;
    const az = new Float32Array(W * H);
    const lons = new Float64Array(W);
    for (let c = 0; c < W; c++) lons[c] = (x0 + ((c + 0.5) * (x1 - x0)) / W) / MERC_R / DEG;
    for (let r = 0; r < H; r++) {
      const lat = invMercY(y1 - ((r + 0.5) * (y1 - y0)) / H);
      for (let c = 0; c < W; c++) az[r * W + c] = distBearing(j.tx.lat, j.tx.lon, lat, lons[c]).brg;
    }
    return az;
  }

  function showMeta(m, wall) {
    const ituNote = m.itu_maps ? "ITU maps" : "fallback (run scripts/fetch_itu_maps.py)";
    $("meta").innerHTML =
      `Model <b>${m.model}</b> · ${m.n_radials} radials × ${m.n_range} pts @ ${m.ds_m.toFixed(0)} m<br>` +
      `Terrain: ${m.terrain}${m.terrain_zoom != null ? " z" + m.terrain_zoom : ""} (${m.terrain_s}s) · propagation ${m.propagation_s}s · total ${wall.toFixed(1)}s<br>` +
      `ΔN ${m.dn.toFixed(1)}, N₀ ${m.n0.toFixed(1)} (${ituNote})${m.clutter ? " · clutter on" : ""}`;
  }

  // ---------------------------------------------------------------- render
  function displayParams() {
    return {
      vmin: num("vmin"), vmax: num("vmax"), bands: Math.max(0, num("bands") || 0),
      cmap: $("cmap").value, opacity: num("opacity") / 100,
      contours: $("contours").checked, below: $("show-below").checked,
    };
  }

  function render() {
    drawLegend();
    const res = state.result;
    if (!res) return;
    const { W, H, lb, az } = res;
    const dp = displayParams(), lp = linkParams();
    const lut = Colormaps.lut(dp.cmap);
    const span = Math.max(dp.vmax - dp.vmin, 1e-6);
    const cv = document.createElement("canvas");
    cv.width = W; cv.height = H;
    const ctx = cv.getContext("2d");
    const img = ctx.createImageData(W, H);
    const px = img.data;
    const band = new Int16Array(W * H).fill(-32768);
    const base = lp.ptx + lp.gtx - lp.lftx + lp.grx - lp.lfrx;

    for (let i = 0; i < W * H; i++) {
      const l = lb[i];
      if (!(l === l)) continue;                         // NaN: outside area
      let v = base - l + patternGain(az[i], lp);
      if (v < dp.vmin) {
        if (dp.below) { px[i * 4] = 90; px[i * 4 + 1] = 90; px[i * 4 + 2] = 90; px[i * 4 + 3] = 110; }
        band[i] = -1;
        continue;
      }
      let t;
      if (dp.bands > 0) {
        const k = Math.floor((v - dp.vmin) / dp.bands);
        band[i] = k;
        const nb = Math.max(1, Math.ceil(span / dp.bands));
        t = nb > 1 ? Math.min(k, nb - 1) / (nb - 1) : 1;
      } else {
        t = Math.min(1, (v - dp.vmin) / span);
      }
      const c = Math.round(t * 255) * 3;
      px[i * 4] = lut[c]; px[i * 4 + 1] = lut[c + 1]; px[i * 4 + 2] = lut[c + 2]; px[i * 4 + 3] = 255;
    }
    if (dp.contours && dp.bands > 0) {
      for (let r = 0; r < H - 1; r++) {
        for (let c = 0; c < W - 1; c++) {
          const i = r * W + c, b = band[i];
          if (b === -32768) continue;
          const br = band[i + 1], bd = band[i + W];
          if ((br !== -32768 && br !== b) || (bd !== -32768 && bd !== b)) {
            px[i * 4] = 20; px[i * 4 + 1] = 20; px[i * 4 + 2] = 20; px[i * 4 + 3] = 255;
          }
        }
      }
    }
    ctx.putImageData(img, 0, 0);
    const [s, w, n, e] = res.bounds;
    const url = cv.toDataURL("image/png");
    if (state.overlay) {
      state.overlay.setUrl(url);
      state.overlay.setBounds(L.latLngBounds([s, w], [n, e]));
      state.overlay.setOpacity(dp.opacity);
    } else {
      state.overlay = L.imageOverlay(url, [[s, w], [n, e]], { opacity: dp.opacity, interactive: false }).addTo(map);
      state.overlay.getElement().style.imageRendering = "pixelated";
    }
  }

  function drawLegend() {
    const cv = $("legend-canvas");
    if (!cv) return;
    const dp = displayParams();
    const ctx = cv.getContext("2d");
    const W = cv.width, lut = Colormaps.lut(dp.cmap);
    ctx.clearRect(0, 0, W, cv.height);
    const bw = W - 10, span = dp.vmax - dp.vmin;
    const nb = dp.bands > 0 ? Math.max(1, Math.ceil(span / dp.bands)) : 0;
    for (let x = 0; x < bw; x++) {
      let t = x / (bw - 1);
      if (nb > 0) { const k = Math.min(Math.floor(t * nb), nb - 1); t = nb > 1 ? k / (nb - 1) : 1; }
      const c = Math.round(t * 255) * 3;
      ctx.fillStyle = `rgb(${lut[c]},${lut[c + 1]},${lut[c + 2]})`;
      ctx.fillRect(5 + x, 4, 1, 16);
    }
    ctx.fillStyle = "#dce3ea"; ctx.font = "11px system-ui, sans-serif"; ctx.textAlign = "center";
    const step = nb > 0 && nb <= 8 ? dp.bands : niceStep(span, 5);
    for (let v = dp.vmin; v <= dp.vmax + 1e-9; v += step) {
      const x = 5 + ((v - dp.vmin) / span) * (bw - 1);
      ctx.fillRect(x, 20, 1, 4);
      ctx.fillText(Math.round(v), Math.min(Math.max(x, 10), W - 12), 37);
    }
  }
  function niceStep(range, target) {
    const raw = range / target, mag = Math.pow(10, Math.floor(Math.log10(raw))), f = raw / mag;
    return (f < 1.5 ? 1 : f < 3 ? 2 : f < 7 ? 5 : 10) * mag;
  }

  /** Lb at a lat/lon from the raster (nearest pixel), or null. */
  function lbAt(lat, lon) {
    const res = state.result;
    if (!res) return null;
    const [s, w, n, e] = res.bounds;
    if (lat < s || lat > n || lon < w || lon > e) return null;
    const c = Math.floor(((mercX(lon) - mercX(w)) / (mercX(e) - mercX(w))) * res.W);
    const r = Math.floor(((mercY(n) - mercY(lat)) / (mercY(n) - mercY(s))) * res.H);
    if (c < 0 || r < 0 || c >= res.W || r >= res.H) return null;
    const v = res.lb[r * res.W + c];
    return v === v ? v : null;
  }

  // ---------------------------------------------------------------- probes
  function addProbe(lat, lon) {
    const id = state.nextProbe++;
    const marker = L.marker([lat, lon], {
      draggable: true,
      icon: L.divIcon({ className: "", html: '<div class="probe-icon"></div>', iconSize: [14, 14], iconAnchor: [7, 7] }),
    }).addTo(map);
    marker.bindTooltip(`P${id}`, { permanent: true, direction: "right", offset: [8, 0], className: "probe-label" });
    const probe = { id, lat, lon, marker, data: null };
    marker.on("click", () => showProfile(probe));
    marker.on("dragend", () => {
      const ll = marker.getLatLng();
      probe.lat = ll.lat; probe.lon = ll.lng;
      runProbe(probe);
    });
    state.probes.push(probe);
    runProbe(probe).then(() => showProfile(probe));
  }

  function profileRequest(probe) {
    const k = parseFloat($("kfac").value);
    return {
      tx_lat: state.tx.lat, tx_lon: state.tx.lon, rx_lat: probe.lat, rx_lon: probe.lon,
      freq_mhz: num("freq"), tx_height: num("tx-h"), rx_height: num("pr-h"),
      model: $("model").value, time_pct: num("time-pct"), loc_pct: num("loc-pct"),
      sigma_loc: num("sigma-l"), polarization: $("pol").value,
      k_factor: isFinite(k) ? k : null, terrain: $("terrain").value, clutter: $("clutter").checked,
    };
  }

  async function runProbe(probe) {
    probe.data = null;
    renderProbeList();
    const req = profileRequest(probe);
    try {
      const r = await fetch("/api/profile", {
        method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(req),
      });
      if (!r.ok) throw new Error((await r.json()).detail || r.statusText);
      probe.data = await r.json();
      probe.req = req;
      probe.error = null;
    } catch (e) {
      probe.error = String(e.message || e);
    }
    renderProbeList();
    if (state.profileProbe === probe) showProfile(probe);
  }

  function probePower(probe) {
    if (!probe.data) return null;
    const lp = linkParams();
    return rxPower(probe.data.lb, probe.data.bearing_deg, lp, { g: num("pr-g"), l: num("pr-l") });
  }

  function renderProbeList() {
    const ol = $("probe-list");
    ol.innerHTML = "";
    for (const p of state.probes) {
      const li = document.createElement("li");
      const pw = probePower(p);
      const val = p.error ? "error" : pw == null ? "…" : `${pw.toFixed(1)} dBm`;
      li.innerHTML = `P${p.id} <span class="rm" title="Remove">✕</span><span class="val">${val}</span>` +
        (p.data ? `<br><small>${(p.data.distance_m / 1000).toFixed(2)} km · ${p.data.bearing_deg.toFixed(1)}° · Lb ${p.data.lb.toFixed(1)} dB</small>` : "");
      li.onclick = (ev) => {
        if (ev.target.classList.contains("rm")) { removeProbe(p); return; }
        showProfile(p);
      };
      ol.appendChild(li);
      if (pw != null) p.marker.setTooltipContent(`P${p.id}: ${pw.toFixed(1)} dBm`);
    }
  }

  function removeProbe(p) {
    map.removeLayer(p.marker);
    state.probes = state.probes.filter((q) => q !== p);
    if (state.profileProbe === p) closeProfile();
    renderProbeList();
  }

  let probeTimer = null;
  function refreshProbes() {
    clearTimeout(probeTimer);
    probeTimer = setTimeout(() => state.probes.forEach(runProbe), 400);
  }

  // --------------------------------------------------------------- profile
  let pfGeom = null, pfHover = null;
  function showProfile(probe) {
    state.profileProbe = probe;
    $("profile").hidden = false;
    document.querySelector(".mapwrap").classList.add("pf-open");
    $("pf-title").textContent = `Path cross-section: TX → P${probe.id}`;
    if (!probe.data) {
      $("pf-info").textContent = probe.error ? `Error: ${probe.error}` : "Computing…";
      pfGeom = null; clearCanvas(); return;
    }
    const d = probe.data, req = probe.req;
    pfGeom = ProfileChart.geometry(d, { htg: req.tx_height, hrg: req.rx_height, fMHz: req.freq_mhz });
    const pw = probePower(probe);
    $("pf-info").textContent =
      `${(d.distance_m / 1000).toFixed(3)} km · bearing ${d.bearing_deg.toFixed(1)}° · Lb ${d.lb.toFixed(1)} dB · Prx ${pw.toFixed(1)} dBm`;
    const det = d.details || {};
    const rows = [
      ["Model", req.model], ["Path type", det.trans_horizon == null ? "-" : det.trans_horizon ? "Trans-horizon" : "Line of sight"],
      ["Free space Lbfs", fmt(det.Lbfs, " dB")], ["Diffraction Ld", fmt(det.Ld, " dB")],
      ["Troposcatter Lbs", fmt(det.Lbs, " dB")], ["Ducting Lba", fmt(det.Lba, " dB")],
      ["Basic loss Lb", fmt(d.lb, " dB")], ["Worst clearance", pfGeom.worst.i > 0 ? `${Math.round(pfGeom.worst.ratio * 100)} % F1 @ ${d.d_km[pfGeom.worst.i].toFixed(2)} km` : "-"],
      ["TX / RX ground", `${d.tx_ground.toFixed(1)} / ${d.rx_ground.toFixed(1)} m`],
      ["k (effective)", d.k_eff.toFixed(3)], ["ΔN / N₀", `${d.dn.toFixed(1)} / ${d.n0.toFixed(1)}`],
      ["Profile points", d.d_km.length], ["Terrain zoom", d.terrain_zoom ?? "local"],
    ];
    $("pf-side").innerHTML = "<table>" + rows.map(([k, v]) => `<tr><td>${k}</td><td>${v}</td></tr>`).join("") + "</table>";
    ProfileChart.draw($("pf-canvas"), pfGeom, pfHover);
  }
  const fmt = (v, u) => (v == null || !isFinite(v) ? "-" : v.toFixed(1) + u);
  function clearCanvas() { const c = $("pf-canvas"); c.getContext("2d").clearRect(0, 0, c.width, c.height); }
  function closeProfile() {
    $("profile").hidden = true; state.profileProbe = null;
    document.querySelector(".mapwrap").classList.remove("pf-open");
  }
  $("pf-close").onclick = closeProfile;
  $("pf-canvas").addEventListener("mousemove", (e) => {
    pfHover = e.offsetX;
    if (pfGeom) ProfileChart.draw($("pf-canvas"), pfGeom, pfHover);
  });
  $("pf-canvas").addEventListener("mouseleave", () => { pfHover = null; if (pfGeom) ProfileChart.draw($("pf-canvas"), pfGeom, null); });
  window.addEventListener("resize", () => { if (pfGeom) ProfileChart.draw($("pf-canvas"), pfGeom, pfHover); });

  // ------------------------------------------------------------ map events
  function setMode(m) {
    state.mode = state.mode === m ? null : m;
    $("btn-place-tx").classList.toggle("active", state.mode === "tx");
    $("btn-place-probe").classList.toggle("active", state.mode === "probe");
    map.getContainer().classList.toggle("placing", !!state.mode);
  }

  map.on("click", (e) => {
    const { lat, lng } = e.latlng;
    if (state.mode === "tx") { setTx(lat, lng); setMode("tx"); return; }
    if (state.mode === "probe") { addProbe(lat, lng); return; }
    const lb = lbAt(lat, lng);
    if (lb == null) return;
    const db = distBearing(state.tx.lat, state.tx.lon, lat, lng);
    const pw = rxPower(lb, db.brg, linkParams());
    L.popup().setLatLng(e.latlng).setContent(
      `<b>${pw.toFixed(1)} dBm</b><br>Lb ${lb.toFixed(1)} dB<br>${(db.d / 1000).toFixed(2)} km, ${db.brg.toFixed(1)}°` +
      `<br><a href="#" id="pop-probe">Add probe here</a>`).openOn(map);
    setTimeout(() => {
      const a = document.getElementById("pop-probe");
      if (a) a.onclick = (ev) => { ev.preventDefault(); map.closePopup(); addProbe(lat, lng); };
    }, 0);
  });

  map.on("mousemove", (e) => {
    const { lat, lng } = e.latlng;
    const db = distBearing(state.tx.lat, state.tx.lon, lat, lng);
    const lb = lbAt(lat, lng);
    let html = `${lat.toFixed(5)}, ${lng.toFixed(5)}<br>${(db.d / 1000).toFixed(2)} km @ ${db.brg.toFixed(1)}°`;
    if (lb != null) html += `<br><b>${rxPower(lb, db.brg, linkParams()).toFixed(1)} dBm</b> · Lb ${lb.toFixed(1)} dB`;
    $("readout").innerHTML = html;
  });

  // ------------------------------------------------------------- save/load
  const FIELDS = ["freq", "tx-h", "tx-p", "tx-g", "tx-l", "pattern", "az", "bw", "fb", "area", "res", "radius",
    "rx-h", "model", "time-pct", "loc-pct", "sigma-l", "pol", "kfac", "terrain", "clutter", "rx-g", "rx-l",
    "vmin", "vmax", "bands", "cmap", "opacity", "contours", "show-below", "pr-h", "pr-g", "pr-l"];

  function snapshot() {
    const inputs = {};
    for (const f of FIELDS) inputs[f] = $(f).type === "checkbox" ? $(f).checked : $(f).value;
    const c = map.getCenter();
    return {
      app: "rf-coverage-tool", version: 1, saved: new Date().toISOString(),
      tx: state.tx, inputs, view: { lat: c.lat, lon: c.lng, zoom: map.getZoom() },
      probes: state.probes.map((p) => ({ lat: p.lat, lon: p.lon })),
    };
  }

  function restore(cfg) {
    if (!cfg || cfg.app !== "rf-coverage-tool") throw new Error("Not an rf-coverage-tool config file");
    for (const [k, v] of Object.entries(cfg.inputs || {})) {
      if (!$(k)) continue;
      if ($(k).type === "checkbox") $(k).checked = !!v; else $(k).value = v;
    }
    $("dir-fields").hidden = $("pattern").value !== "dir";
    $("op-val").value = `${$("opacity").value}%`;
    if (cfg.view) map.setView([cfg.view.lat, cfg.view.lon], cfg.view.zoom);
    state.probes.slice().forEach(removeProbe);
    setTx(cfg.tx.lat, cfg.tx.lon);
    (cfg.probes || []).forEach((p) => addProbe(p.lat, p.lon));
    updateEirp(); render();
  }

  function download(blob, name) {
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = name; a.click();
    setTimeout(() => URL.revokeObjectURL(a.href), 2000);
  }

  $("btn-save").onclick = () => download(new Blob([JSON.stringify(snapshot(), null, 2)], { type: "application/json" }), "coverage-config.json");
  $("file-load").onchange = async (e) => {
    const f = e.target.files[0];
    if (!f) return;
    try { restore(JSON.parse(await f.text())); setStatus("Config loaded. Press Compute."); }
    catch (err) { setStatus(`Load failed: ${err.message}`, true); }
    e.target.value = "";
  };

  // ------------------------------------------------------------ PNG export
  async function exportPng() {
    const el = map.getContainer(), rect = el.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    const cv = document.createElement("canvas");
    cv.width = rect.width * dpr; cv.height = rect.height * dpr;
    const ctx = cv.getContext("2d");
    ctx.scale(dpr, dpr);
    ctx.fillStyle = "#0b0f13"; ctx.fillRect(0, 0, rect.width, rect.height);
    const drawEl = (img, alpha = 1) => {
      const r = img.getBoundingClientRect();
      ctx.globalAlpha = alpha;
      ctx.drawImage(img, r.left - rect.left, r.top - rect.top, r.width, r.height);
      ctx.globalAlpha = 1;
    };
    el.querySelectorAll(".leaflet-tile-pane img.leaflet-tile-loaded").forEach((img) => drawEl(img));
    if (state.overlay) drawEl(state.overlay.getElement(), displayParams().opacity);

    const pt = (lat, lon) => map.latLngToContainerPoint([lat, lon]);
    const tp = pt(state.tx.lat, state.tx.lon);
    ctx.fillStyle = "#ff3b30"; ctx.strokeStyle = "#fff"; ctx.lineWidth = 3;
    ctx.beginPath(); ctx.arc(tp.x, tp.y, 9, 0, 2 * Math.PI); ctx.fill(); ctx.stroke();
    ctx.font = "bold 12px system-ui, sans-serif";
    for (const p of state.probes) {
      const q = pt(p.lat, p.lon);
      ctx.fillStyle = "#ffd60a"; ctx.strokeStyle = "#111"; ctx.lineWidth = 2;
      ctx.beginPath(); ctx.arc(q.x, q.y, 6, 0, 2 * Math.PI); ctx.fill(); ctx.stroke();
      const pw = probePower(p);
      const label = `P${p.id}${pw != null ? ": " + pw.toFixed(1) + " dBm" : ""}`;
      ctx.fillStyle = "rgba(15,20,25,.9)"; ctx.fillRect(q.x + 9, q.y - 9, ctx.measureText(label).width + 8, 18);
      ctx.fillStyle = "#fff"; ctx.fillText(label, q.x + 13, q.y + 4);
    }
    // legend + caption
    const lg = $("legend-canvas");
    const lx = rect.width - lg.width - 20, ly = rect.height - lg.height - 50;
    ctx.fillStyle = "rgba(15,20,25,.88)"; ctx.fillRect(lx - 8, ly - 22, lg.width + 16, lg.height + 30);
    ctx.fillStyle = "#fff"; ctx.font = "bold 12px system-ui, sans-serif"; ctx.fillText("Received power (dBm)", lx, ly - 6);
    ctx.drawImage(lg, lx, ly);
    const m = state.result ? state.result.inputs : computeInputs();
    const cap = `TX ${state.tx.lat.toFixed(5)}, ${state.tx.lon.toFixed(5)} · ${m.freq_mhz} MHz · ${m.tx_height} m AGL · ` +
      `EIRP ${$("eirp").value.split(" (")[0]} · RX ${m.rx_height} m · ${m.model} · p ${m.time_pct}% · pL ${m.loc_pct}%`;
    ctx.font = "12px system-ui, sans-serif";
    ctx.fillStyle = "rgba(15,20,25,.88)"; ctx.fillRect(8, 8, ctx.measureText(cap).width + 14, 22);
    ctx.fillStyle = "#fff"; ctx.fillText(cap, 15, 23);
    ctx.fillStyle = "rgba(255,255,255,.85)"; ctx.font = "10px system-ui, sans-serif";
    ctx.fillText("© OpenStreetMap contributors · Terrain: AWS Terrain Tiles / local DTM", 10, rect.height - 8);
    try {
      cv.toBlob((b) => download(b, "coverage.png"), "image/png");
    } catch (err) {
      setStatus("PNG export blocked by base-map CORS; switch base layer and retry.", true);
    }
  }
  $("btn-png").onclick = exportPng;

  // ------------------------------------------------------------------ demo
  $("btn-demo").onclick = () => {
    restore({
      app: "rf-coverage-tool", tx: { lat: 53.5336, lon: -1.8578 },
      view: { lat: 53.5336, lon: -1.8578, zoom: 10 },
      inputs: { freq: 700, "tx-h": 100, "tx-p": 50, "tx-g": 12, "tx-l": 2, pattern: "omni", area: "radius",
        radius: 30, res: "draft", model: "p1812", "rx-h": 1.5, vmin: -110, vmax: -40, bands: 10 },
      probes: [{ lat: 53.38, lon: -1.47 }, { lat: 53.48, lon: -2.24 }],
    });
    compute();
  };

  // ---------------------------------------------------------------- wiring
  function setStatus(msg, err = false) { $("status").textContent = msg; $("status").classList.toggle("err", err); }
  function setBusy(on, msg) { $("busy").hidden = !on; if (msg) $("busy-text").textContent = msg; }

  $("btn-compute").onclick = compute;
  $("btn-place-tx").onclick = () => setMode("tx");
  $("btn-place-probe").onclick = () => setMode("probe");
  $("btn-clear-probes").onclick = () => state.probes.slice().forEach(removeProbe);
  $("btn-clear").onclick = () => {
    if (state.overlay) map.removeLayer(state.overlay);
    state.overlay = null; state.result = null; $("meta").innerHTML = ""; $("stale").hidden = true;
  };
  $("pattern").onchange = () => { $("dir-fields").hidden = $("pattern").value !== "dir"; render(); renderProbeList(); };
  $("tx-lat").onchange = $("tx-lon").onchange = () => setTx(num("tx-lat"), num("tx-lon"), true);
  $("opacity").oninput = () => {
    $("op-val").value = `${$("opacity").value}%`;
    if (state.overlay) state.overlay.setOpacity(num("opacity") / 100);
  };

  // Link-budget and display inputs re-render instantly
  ["tx-p", "tx-g", "tx-l", "az", "bw", "fb", "rx-g", "rx-l", "vmin", "vmax", "bands", "cmap", "contours", "show-below"]
    .forEach((id) => $(id).addEventListener("input", () => { updateEirp(); render(); renderProbeList(); if (state.profileProbe) showProfile(state.profileProbe); }));
  ["pr-g", "pr-l"].forEach((id) => $(id).addEventListener("input", () => { renderProbeList(); if (state.profileProbe) showProfile(state.profileProbe); }));
  // Propagation inputs mark the map stale and refresh probes
  document.querySelectorAll("[data-recompute]").forEach((el) => el.addEventListener("change", () => { markStale(); refreshProbes(); }));
  $("pr-h").addEventListener("change", refreshProbes);
  map.on("moveend", () => { if ($("area").value === "view") markStale(); });

  // init
  setTx(state.tx.lat, state.tx.lon);
  updateEirp();
  drawLegend();
  fetch("/api/health").then((r) => r.json()).then((h) => {
    if (!h.itu_maps) setStatus("ITU ΔN/N₀ maps not installed: using UK fallback values.");
  }).catch(() => setStatus("Backend not reachable.", true));
})();
