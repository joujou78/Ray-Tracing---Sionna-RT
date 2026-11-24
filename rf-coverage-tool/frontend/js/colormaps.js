/* Colour maps as linear-interpolated stops. Each returns a 256-entry RGB LUT. */
(function () {
  "use strict";

  const STOPS = {
    // Low = blue, high = red (classic coverage "rainbow")
    rainbow: ["#2c3bc9", "#1f8ff0", "#19d3e0", "#3ddc6a", "#d8e83a", "#ffb02e", "#ff5a1f", "#d7191c"],
    viridis: ["#440154", "#482878", "#3e4989", "#31688e", "#26828e", "#1f9e89", "#35b779", "#6ece58", "#b5de2b", "#fde725"],
    rdgn: ["#d73027", "#f46d43", "#fdae61", "#fee08b", "#d9ef8b", "#a6d96a", "#66bd63", "#1a9850"],
    blue: ["#deebf7", "#9ecae1", "#6baed6", "#3182bd", "#08519c", "#08306b"],
  };

  function hex(c) {
    const n = parseInt(c.slice(1), 16);
    return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  }

  const cache = {};
  function lut(name) {
    if (cache[name]) return cache[name];
    const stops = (STOPS[name] || STOPS.rainbow).map(hex);
    const out = new Uint8ClampedArray(256 * 3);
    for (let i = 0; i < 256; i++) {
      const t = (i / 255) * (stops.length - 1);
      const k = Math.min(Math.floor(t), stops.length - 2);
      const f = t - k;
      for (let c = 0; c < 3; c++) out[i * 3 + c] = stops[k][c] + (stops[k + 1][c] - stops[k][c]) * f;
    }
    cache[name] = out;
    return out;
  }

  window.Colormaps = { lut, names: Object.keys(STOPS) };
})();
