/* Drive-test overlay: load a CSV of measurements, plot them, and compare with
 * the current coverage prediction (nearest raster pixel + live link budget).
 * Statistics are recomputed whenever the coverage re-renders. */
(function () {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const MAX_DRAWN = 25000;                 // points drawn (stats always use all rows)
  const dt = { header: [], rows: [], layer: null, renderer: L.canvas({ padding: 0.3 }), cmp: [] };

  /** Minimal CSV/TSV/semicolon parser with quoted fields. */
  function parseCsv(text) {
    const first = text.slice(0, text.indexOf("\n") + 1 || text.length);
    const delim = [",", ";", "\t"].reduce((a, b) => (first.split(b).length > first.split(a).length ? b : a));
    const rows = [];
    let row = [], field = "", q = false;
    for (let i = 0; i < text.length; i++) {
      const c = text[i];
      if (q) {
        if (c === '"' && text[i + 1] === '"') { field += '"'; i++; }
        else if (c === '"') q = false;
        else field += c;
      } else if (c === '"') q = true;
      else if (c === delim) { row.push(field); field = ""; }
      else if (c === "\n" || c === "\r") {
        if (c === "\r" && text[i + 1] === "\n") i++;
        row.push(field); field = "";
        if (row.length > 1 || row[0] !== "") rows.push(row);
        row = [];
      } else field += c;
    }
    if (field !== "" || row.length) { row.push(field); rows.push(row); }
    return rows;
  }

  /** Guess a column index by name patterns. */
  function guess(header, patterns) {
    const h = header.map((x) => x.trim().toLowerCase());
    for (const p of patterns) {
      const i = h.findIndex((x) => p.test(x));
      if (i >= 0) return i;
    }
    return -1;
  }

  function fillSelect(id, header, idx) {
    const sel = $(id);
    sel.innerHTML = header.map((h, i) => `<option value="${i}">${h.replace(/</g, "&lt;")}</option>`).join("");
    if (idx >= 0) sel.value = String(idx);
  }

  /** Ofcom drive-test files start with "Key: value ,,,," lines before the table. */
  function splitMeta(rows) {
    const meta = {};
    let k = 0;
    for (; k < rows.length; k++) {
      const r = rows[k];
      const rest = r.slice(1).every((x) => x.trim() === "");
      const m = /^\s*([^:]+):\s*(.*?)\s*$/.exec(r[0]);
      if (!(rest && m)) break;
      meta[m[1].trim().toLowerCase()] = m[2];
    }
    return { meta, table: rows.slice(k) };
  }

  /** Map Ofcom metadata to tool inputs. Returns null if the file has none. */
  function siteFromMeta(meta) {
    const f = (key) => { const v = parseFloat(meta[key]); return isFinite(v) ? v : null; };
    const lat = f("site latitude"), lon = f("site longitude");
    if (lat == null || lon == null) return null;
    const rxLoss = (f("rx cable loss (db)") || 0) + (f("rx splitter loss (db)") || 0)
      + (f("rx band pass filter loss (db)") || 0) - (f("rx lna gain (db)") || 0);
    return {
      name: (meta["site name"] || "").trim(), lat, lon,
      inputs: {
        freq: f("frequency (mhz)"), "tx-h": f("tx antenna height (m)"), "tx-p": f("tx amplifier power (dbm)"),
        "tx-l": f("tx cable loss (db)"), "tx-g": f("tx antenna gain (dbi)"), "rx-h": f("rx antenna height (m)"),
        "rx-g": f("rx antenna gain (dbi)"), "rx-l": +rxLoss.toFixed(2),
      },
    };
  }

  async function load(file) {
    const { meta, table: rows } = splitMeta(parseCsv(await file.text()));
    if (rows.length < 2) throw new Error("CSV has no data rows");
    dt.header = rows[0].map((h) => h.trim());
    dt.rows = rows.slice(1);
    dt.site = siteFromMeta(meta);
    const btn = $("dt-apply");
    btn.hidden = !dt.site;
    if (dt.site) {
      const i = dt.site.inputs;
      btn.textContent = `Use site setup from file${dt.site.name ? ` (${dt.site.name})` : ""}`;
      btn.title = `TX ${dt.site.lat}, ${dt.site.lon} · ${i.freq} MHz · ${i["tx-h"]} m · ${i["tx-p"]} dBm, ` +
        `TX loss ${i["tx-l"]} dB, gain ${i["tx-g"]} dBi · RX ${i["rx-h"]} m, gain ${i["rx-g"]} dBi, chain loss ${i["rx-l"]} dB`;
    }
    fillSelect("dt-lat", dt.header, guess(dt.header, [/^lat/, /latitude/]));
    fillSelect("dt-lon", dt.header, guess(dt.header, [/^lon/, /^lng/, /longitude/]));
    fillSelect("dt-val", dt.header, guess(dt.header,
      [/rsrp/, /rssi/, /dbm/, /rx.?lev/, /level/, /power/, /signal/, /measured/, /value/]));
    $("dt-cols").hidden = false;
    update(true);
  }

  function points() {
    const iLat = +$("dt-lat").value, iLon = +$("dt-lon").value, iVal = +$("dt-val").value;
    const out = [];
    for (const r of dt.rows) {
      const lat = parseFloat(r[iLat]), lon = parseFloat(r[iLon]), v = parseFloat(r[iVal]);
      if (isFinite(lat) && isFinite(lon) && isFinite(v) && Math.abs(lat) <= 90 && Math.abs(lon) <= 180) out.push({ lat, lon, v });
    }
    return out;
  }

  function colour(t, lut) {
    const c = Math.round(Math.max(0, Math.min(1, t)) * 255) * 3;
    return `rgb(${lut[c]},${lut[c + 1]},${lut[c + 2]})`;
  }

  function update(fit = false) {
    if (!dt.rows.length) return;
    const pts = points();
    const map = window.App.map;
    if (dt.layer) map.removeLayer(dt.layer);
    dt.layer = L.layerGroup().addTo(map);

    // Comparison
    dt.cmp = pts.map((p) => {
      const pred = window.App.predictAt(p.lat, p.lon);
      return { ...p, pred, err: pred == null ? null : pred - p.v };
    });
    const e = dt.cmp.filter((c) => c.err != null);
    stats(pts.length, e);

    // Drawing (decimated for very large files)
    const dp = window.App.display(), lut = window.App.colormap();
    const byErr = $("dt-show-err").checked;
    const step = Math.max(1, Math.ceil(dt.cmp.length / MAX_DRAWN));
    for (let i = 0; i < dt.cmp.length; i += step) {
      const c = dt.cmp[i];
      let fill;
      if (byErr) {
        fill = c.err == null ? "#8a99a8" : c.err > 0 ? `rgba(255,69,58,${Math.min(1, 0.25 + Math.abs(c.err) / 15)})`
                              : `rgba(10,132,255,${Math.min(1, 0.25 + Math.abs(c.err) / 15)})`;
      } else {
        fill = colour((c.v - dp.vmin) / Math.max(dp.vmax - dp.vmin, 1e-6), lut);
      }
      const outside = c.pred == null;
      L.circleMarker([c.lat, c.lon], outside
        ? { renderer: dt.renderer, radius: 2, stroke: false, fillColor: "#8a99a8", fillOpacity: 0.35 }
        : { renderer: dt.renderer, radius: 3, weight: 0.4, color: "#111", fillColor: fill, fillOpacity: 1 })
        .bindTooltip(() => `meas ${c.v.toFixed(1)} dBm` + (c.pred != null ? `<br>pred ${c.pred.toFixed(1)} dBm<br>err ${c.err >= 0 ? "+" : ""}${c.err.toFixed(1)} dB` : "<br>outside coverage"))
        .addTo(dt.layer);
    }
    if (fit && pts.length) map.fitBounds(L.latLngBounds(pts.map((p) => [p.lat, p.lon])), { padding: [30, 30] });
    $("dt-export").disabled = !e.length;
  }

  function stats(n, e) {
    const el = $("dt-stats");
    if (!window.App.hasCoverage()) {
      el.innerHTML = `${n} points loaded. Compute coverage over them to get error statistics.`;
      return;
    }
    if (!e.length) { el.innerHTML = `${n} points loaded; none fall inside the computed coverage.`; return; }
    const m = e.length;
    const mean = e.reduce((a, c) => a + c.err, 0) / m;
    const sd = Math.sqrt(e.reduce((a, c) => a + (c.err - mean) ** 2, 0) / Math.max(m - 1, 1));
    const rmse = Math.sqrt(e.reduce((a, c) => a + c.err ** 2, 0) / m);
    const mae = e.reduce((a, c) => a + Math.abs(c.err), 0) / m;
    const mp = e.reduce((a, c) => a + c.pred, 0) / m, mv = e.reduce((a, c) => a + c.v, 0) / m;
    let sxy = 0, sxx = 0, syy = 0;
    for (const c of e) { sxy += (c.pred - mp) * (c.v - mv); sxx += (c.pred - mp) ** 2; syy += (c.v - mv) ** 2; }
    const r = sxy / Math.sqrt(sxx * syy);
    el.innerHTML =
      `<b>${m}</b> of ${n} points inside coverage<br>` +
      `Mean error (pred − meas) <b>${mean >= 0 ? "+" : ""}${mean.toFixed(2)} dB</b> · σ <b>${sd.toFixed(2)} dB</b><br>` +
      `RMSE <b>${rmse.toFixed(2)} dB</b> · MAE ${mae.toFixed(2)} dB · r ${isFinite(r) ? r.toFixed(3) : "-"}`;
  }

  function exportCsv() {
    const lines = ["lat,lon,measured_dbm,predicted_dbm,error_db"];
    for (const c of dt.cmp) {
      lines.push([c.lat, c.lon, c.v, c.pred == null ? "" : c.pred.toFixed(2), c.err == null ? "" : c.err.toFixed(2)].join(","));
    }
    const a = document.createElement("a");
    a.href = URL.createObjectURL(new Blob([lines.join("\n")], { type: "text/csv" }));
    a.download = "drive-test-comparison.csv"; a.click();
  }

  $("dt-file").onchange = async (ev) => {
    const f = ev.target.files[0];
    if (!f) return;
    try { await load(f); } catch (err) { window.App.setStatus(`Drive test: ${err.message}`, true); }
    ev.target.value = "";
  };
  ["dt-lat", "dt-lon", "dt-val"].forEach((id) => $(id).addEventListener("change", () => update(true)));
  $("dt-show-err").addEventListener("change", () => update());
  $("dt-export").onclick = exportCsv;
  $("dt-apply").onclick = () => {
    if (!dt.site) return;
    window.App.applySetup(dt.site.lat, dt.site.lon, dt.site.inputs);
    window.App.setStatus(`Applied site setup from file (RX chain loss ${dt.site.inputs["rx-l"]} dB = cable + splitter + filter − LNA). Press Compute coverage.`);
  };
  $("dt-clear").onclick = () => {
    if (dt.layer) window.App.map.removeLayer(dt.layer);
    dt.layer = null; dt.rows = []; dt.cmp = [];
    $("dt-cols").hidden = true; $("dt-stats").innerHTML = ""; $("dt-export").disabled = true;
    $("dt-apply").hidden = true; dt.site = null;
  };
  // Re-evaluate whenever the coverage is re-rendered (new run, gains, pattern...)
  let t = null;
  window.addEventListener("coverage-render", () => { clearTimeout(t); t = setTimeout(() => update(), 150); });
})();
