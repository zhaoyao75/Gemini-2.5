// ============================================================
//  PAINTER: style-independent drawing toolkit.
//  A style object may use any of these; brush-stroke styles use
//  strokePass(), flat/graphic styles can use fillRegions() etc.
// ============================================================
const P = (() => {
  let seed = 12345;
  const setSeed = s => { seed = s; };
  const rand = () => { seed = (seed * 16807) % 2147483647; return (seed - 1) / 2147483646; };
  const R = (a, b) => a + (b - a) * rand();
  const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const lerp = (a, b, t) => a + (b - a) * t;
  const hex = h => [parseInt(h.slice(1, 3), 16), parseInt(h.slice(3, 5), 16), parseInt(h.slice(5, 7), 16)];
  const mix = (a, b, t) => a.map((v, i) => lerp(v, b[i], t));
  const shade = (c, f) => c.map(v => clamp(v * f, 0, 255));
  const css = c => `rgb(${c[0] | 0},${c[1] | 0},${c[2] | 0})`;
  // convert an angle defined in scene units to pixel space (same here: y is in W-units)
  const ang = a => a;

  let ctx, W, H;
  function init(canvas) { ctx = canvas.getContext('2d'); W = canvas.width; H = canvas.height; return ctx; }
  const toScene = (px, py) => [px / W, py / W];
  const regionPx = (px, py) => SCENE.region(px / W, py / W);

  // strokes stop at region edges; on flowers also at each petal's edge
  const same = (a, b) => a.k === b.k && (a.k !== 'bloom' || (a.i === b.i && a.part === b.part && a.ring === b.ring && a.petal === b.petal));
  // ---- impasto brush stroke that follows a direction field and stops at region edges
  function stroke(px, py, len, wid, reg, style, opt = {}) {
    const [u, y] = toScene(px, py);
    const jit = opt.jitter ?? 14;
    const col = style.color(reg, u, y).map(v => clamp(v + R(-jit, jit), 0, 255));
    const pts = [[px, py]]; let x = px, yy = py;
    const steps = 4, step = len / steps;
    for (let s = 0; s < steps; s++) {
      const a = style.angle(SCENE.region(x / W, yy / W), x / W, yy / W);
      x += Math.cos(a) * step; yy += Math.sin(a) * step;
      if (!same(regionPx(x, yy), reg)) break;
      pts.push([x, yy]);
    }
    if (pts.length < 2) pts.push([px + R(-1, 1), py + R(-1, 1)]);
    const path = (ox, oy) => { ctx.beginPath(); ctx.moveTo(pts[0][0] + ox, pts[0][1] + oy); for (let i = 1; i < pts.length; i++) ctx.lineTo(pts[i][0] + ox, pts[i][1] + oy); };
    ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    const imp = opt.impasto ?? 1;
    if (imp > 0) { ctx.globalAlpha = 0.5 * imp; ctx.strokeStyle = css(shade(col, 0.62)); ctx.lineWidth = wid; path(wid * 0.18, wid * 0.22); ctx.stroke(); }
    ctx.globalAlpha = opt.alpha ?? 1; ctx.strokeStyle = css(col); ctx.lineWidth = wid; path(0, 0); ctx.stroke();
    if (imp > 0) { ctx.globalAlpha = 0.42 * imp; ctx.strokeStyle = css(col.map(v => clamp(v * 1.2 + 20, 0, 255))); ctx.lineWidth = wid * 0.32; path(-wid * 0.16, -wid * 0.18); ctx.stroke(); }
    ctx.globalAlpha = 1;
  }

  // one full layer of strokes; sizes are fractions of W so any resolution works
  function strokePass(style, { spacing, len, wid, keep = 1, perRegion = {}, only = null, ...opt }) {
    const sp = spacing * W, L = len * W, Wd = wid * W;
    const buckets = {};
    for (let y = 0; y < H; y += sp) for (let x = 0; x < W; x += sp) {
      if (rand() > keep) continue;
      const px = x + R(-sp, sp) * 0.6, py = y + R(-sp, sp) * 0.6;
      const reg = regionPx(px, py);
      if (only && !only.includes(reg.k)) continue;
      (buckets[reg.z] ||= []).push([px, py, reg]);
    }
    Object.keys(buckets).sort((a, b) => a - b).forEach(z => {
      const b = buckets[z];
      for (let i = b.length - 1; i > 0; i--) { const j = (rand() * (i + 1)) | 0; [b[i], b[j]] = [b[j], b[i]]; }
      b.forEach(([px, py, reg]) => {
        const m = perRegion[reg.k] || {};
        stroke(px, py, L * (m.len ?? 1) * R(0.7, 1.3), Wd * (m.wid ?? 1) * R(0.8, 1.2), reg, style, opt);
      });
    });
  }

  // ---- contour helpers (broken painterly lines), with occlusion tests
  function dash(x0, y0, x1, y1, w, col, ok) {
    if (ok && !ok((x0 + x1) / 2, (y0 + y1) / 2)) return;
    ctx.strokeStyle = col; ctx.lineWidth = w; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.moveTo(x0, y0); ctx.lineTo(x1, y1); ctx.stroke();
  }
  function vaseContour(col, w, gap = 0.15) {
    const V = SCENE.VASE, st = 0.004;
    for (let y = V.top; y < V.bottom; y += st) {
      const h1 = SCENE.vaseHalf(y), h2 = SCENE.vaseHalf(y + st); if (h1 < 0 || h2 < 0) continue;
      [-1, 1].forEach(s => { if (rand() > gap) dash((V.cx + s * h1) * W + R(-1, 1), y * W, (V.cx + s * h2) * W + R(-1, 1), (y + st) * W, w * W * R(0.8, 1.3), col, (x, yy) => regionPx(x, yy).z < 3); });
    }
    const h = SCENE.vaseHalf(V.top + 0.001);
    for (let a = 0; a < Math.PI * 2; a += 0.12) dash((V.cx + Math.cos(a) * h) * W, V.top * W + Math.sin(a) * 0.012 * W, (V.cx + Math.cos(a + 0.12) * h) * W, V.top * W + Math.sin(a + 0.12) * 0.012 * W, w * W, col, (x, yy) => regionPx(x, yy).z < 3);
  }
  function bloomContours(colFn, w, gap = 0.35) {
    SCENE.BLOOMS.forEach((b, i) => {
      const col = colFn(b), st = 0.09;
      for (let a = 0; a < Math.PI * 2; a += st) {
        if (rand() < gap) continue;
        const [u0, y0] = SCENE.bloomPoint(i, a), [u1, y1] = SCENE.bloomPoint(i, a + st);
        dash(u0 * W, y0 * W, u1 * W, y1 * W, w * W * R(0.8, 1.3), col,
             (x, yy) => { const u = x / W, y = yy / W; const q = SCENE.inBloom(u + (b.u - u) * 0.06, y + (b.y - y) * 0.06); return !q || q.i === i; });
      }
    });
  }
  // outlines of each visible petal tip (ruffled edges) + bud outlines
  function petalContours(colFn, w, gap = 0.2, maxRing = 99) {
    SCENE.BLOOMS.forEach((b, i) => {
      const col = colFn(b);
      if (b.type === 'bud') {
        for (let a = 0; a < Math.PI * 2; a += 0.2) { if (rand() < gap) continue;
          const [u0, y0] = SCENE.bloomPoint(i, a), [u1, y1] = SCENE.bloomPoint(i, a + 0.2);
          dash(u0 * W, y0 * W, u1 * W, y1 * W, w * W, col, (x, yy) => { const q = SCENE.inBloom(x / W + (b.u - x / W) * 0.08, yy / W + (b.y - yy / W) * 0.08); return q && q.i === i; }); }
        return;
      }
      SCENE.petalsOf(i).forEach(({ j, k }) => {
        if (j > maxRing) return;
        for (let s = -0.95; s < 0.95; s += 0.1) {
          if (rand() < gap) continue;
          const [u0, y0] = SCENE.petalPoint(i, j, k, s), [u1, y1] = SCENE.petalPoint(i, j, k, s + 0.1);
          const [ui, yi] = SCENE.petalPoint(i, j, k, s + 0.05, 0.92);
          const q = SCENE.inBloom(ui, yi);
          if (!q || q.i !== i || q.ring !== j || q.petal !== k) continue;   // hidden under another petal/bloom
          dash(u0 * W, y0 * W, u1 * W, y1 * W, w * W * R(0.7, 1.2) * (j === 0 ? 1.2 : 0.85), col);
        }
      });
    });
  }
  function tableLine(col, w) {
    const y = SCENE.TABLE_Y * W;
    for (let x = 0; x < W; x += W * 0.02) if (rand() < 0.92) dash(x, y + R(-1, 1) * W * 0.002, x + W * 0.022, y + R(-1, 1) * W * 0.002, w * W * R(0.8, 1.3), col, (xx, yy) => regionPx(xx, yy - W * 0.004).z < 2);
  }
  function canvasTexture(alpha = 0.022) {
    const step = Math.max(3, W / 400);
    ctx.globalAlpha = alpha;
    for (let y = 0; y < H; y += step) { ctx.fillStyle = rand() < 0.5 ? '#000' : '#fff'; ctx.fillRect(0, y, W, step / 3); }
    for (let x = 0; x < W; x += step) { ctx.fillStyle = rand() < 0.5 ? '#000' : '#fff'; ctx.fillRect(x, 0, step / 3, H); }
    ctx.globalAlpha = 1;
  }
  // blend a per-pixel layer over what is painted (fn returns [rgb, alpha] or null)
  function overlay(fn, box = [0, 0, 1, SCENE.ASPECT]) {   // box in scene units: u0, y0, u1, y1
    const img = ctx.getImageData(0, 0, W, H), d = img.data;
    const x0 = Math.max(0, Math.floor(box[0] * W)), x1 = Math.min(W, Math.ceil(box[2] * W));
    const y0 = Math.max(0, Math.floor(box[1] * W)), y1 = Math.min(H, Math.ceil(box[3] * W));
    for (let py = y0; py < y1; py++) for (let px = x0; px < x1; px++) {
      const r = fn(regionPx(px, py), px, py); if (!r) continue;
      const [c, a] = r, o = (py * W + px) * 4;
      d[o] = d[o] * (1 - a) + c[0] * a; d[o + 1] = d[o + 1] * (1 - a) + c[1] * a; d[o + 2] = d[o + 2] * (1 - a) + c[2] * a;
    }
    ctx.putImageData(img, 0, 0);
  }
  // flat fill of every pixel by region (for graphic styles / composition preview)
  function fillRegions(colorFn) {
    const img = ctx.createImageData(W, H), d = img.data;
    for (let py = 0; py < H; py++) for (let px = 0; px < W; px++) {
      const reg = regionPx(px, py), c = colorFn(reg, px / W, py / W), o = (py * W + px) * 4;
      d[o] = c[0]; d[o + 1] = c[1]; d[o + 2] = c[2]; d[o + 3] = 255;
    }
    ctx.putImageData(img, 0, 0);
  }

  return { setSeed, rand, R, clamp, lerp, hex, mix, shade, css, init, stroke, strokePass, dash, vaseContour, bloomContours, tableLine, canvasTexture, fillRegions, petalContours, overlay, get ctx() { return ctx; }, get W() { return W; }, get H() { return H; } };
})();
const STYLES = {};
