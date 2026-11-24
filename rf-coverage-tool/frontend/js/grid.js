/* Grid references shared by both pages: Maidenhead locators (client-side)
 * and OS National Grid references (via /api/grid, which applies the OSGB36 datum shift). */
(function () {
  "use strict";

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

  window.Grid = { toLocator, fromLocator, label: gridLabel, parse: parseGrid };
})();
