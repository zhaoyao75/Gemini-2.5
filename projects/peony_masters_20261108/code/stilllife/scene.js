// ============================================================
//  SCENE: shared composition for every artist style.
//  "Peonies in a vase" still life, 3:4 portrait.
//  Units:  u = x / W (0..1),  y = py / W (0..ASPECT)  -> circles stay round.
//  A style never changes the geometry, only how regions are painted.
// ============================================================
const SCENE = (() => {
  const ASPECT = 4 / 3;
  const TABLE_Y = 0.93;            // wall/table horizon (W-units)
  const VASE = { cx: 0.5, top: 0.665, bottom: 1.175 };
  const LIGHT = [-0.6, -0.8];      // light from the upper left

  // ---- Chinese blue-and-white porcelain vase (赏瓶 / 玉壶春瓶) ----
  // flared lip, long slender neck, pear-shaped hanging belly, ring foot.
  // [t (0 = lip, 1 = foot), half-width in W-units]
  const PROFILE = [[0, 0.062], [0.035, 0.051], [0.09, 0.039], [0.22, 0.037], [0.33, 0.042], [0.42, 0.062],
                   [0.52, 0.098], [0.62, 0.130], [0.72, 0.143], [0.80, 0.136], [0.87, 0.112], [0.925, 0.082],
                   [0.94, 0.074], [0.955, 0.079], [1.0, 0.082]];
  function vaseHalf(y) {
    if (y < VASE.top || y > VASE.bottom) return -1;
    const t = (y - VASE.top) / (VASE.bottom - VASE.top);
    for (let i = 0; i < PROFILE.length - 1; i++) {
      const [t0, w0] = PROFILE[i], [t1, w1] = PROFILE[i + 1];
      if (t <= t1) { const f = (t - t0) / (t1 - t0), s = f * f * (3 - 2 * f); return w0 + (w1 - w0) * s; }
    }
    return PROFILE[PROFILE.length - 1][1];
  }
  PROFILE.forEach(p => { p[1] *= 1.3; });   // overall vase size relative to the bouquet
  // Decoration zones, top to bottom (traditional blue-and-white layout)
  const ZONES = [
    ['lip', 0, 0.045], ['neck', 0.045, 0.36], ['shoulder', 0.36, 0.50],
    ['belly', 0.50, 0.85], ['lotus', 0.85, 0.935], ['foot', 0.935, 1.0],
  ];
  const frac = x => x - Math.floor(x);
  const near = (x, c, w) => Math.abs(x - c) < w;
  // cobalt amount on the surface: 0 = white porcelain, ~0.4 = pale wash, 1 = deep cobalt
  // th = angle around the vase (-pi/2..pi/2 visible), t = height (0..1)
  function vaseDecor(th, t, hw) {
    const zone = ZONES.find(z => t >= z[1] && t < z[2]) || ZONES[5];
    const band = (a, b = 0.004) => near(t, a, b);
    let c = 0;
    switch (zone[0]) {
      case 'lip': if (band(0.03, 0.006)) c = 1; break;
      case 'neck': { // banana leaves (蕉叶纹) pointing up
        if (band(0.05) || band(0.355)) { c = 1; break; }
        const p = frac(th * 5 / Math.PI + 0.5) - 0.5, h = (t - 0.07) / 0.27;
        if (h < 0 || h > 1) break;
        const w = 0.46 * Math.pow(h, 0.7);
        if (Math.abs(p) < w) c = (Math.abs(Math.abs(p) - w) < 0.1 || Math.abs(p) < 0.04) ? 1 : 0.45;
        break;
      }
      case 'shoulder': { // ruyi cloud collar (如意云头) hanging from the neck
        if (band(0.365, 0.005)) { c = 1; break; }
        const p = frac(th * 5 / Math.PI) - 0.5;
        const lobe = 0.6 + 0.4 * Math.cos(2 * Math.PI * p) - 0.16 * Math.cos(6 * Math.PI * p);
        const lim = 0.37 + 0.12 * lobe;
        if (t < lim) c = (t > 0.37 + 0.12 * lobe * 0.72 && t < lim - 0.012) ? 0 : 0.95;  // white inner outline
        break;
      }
      case 'belly': { // scrolling peony (缠枝牡丹纹)
        if (band(0.505) || band(0.517, 0.002) || band(0.84) || band(0.828, 0.002)) { c = 1; break; }
        const sx = hw / (VASE.bottom - VASE.top);        // radians -> t-units on the surface
        const vine = t - (0.675 + 0.075 * Math.sin(th * 3.0));
        if (Math.abs(vine) < 0.006) c = 1;
        for (let k = -2; k <= 1; k++) {
          const xc = (k + 0.5) * Math.PI / 3.0, tc = 0.675 + 0.075 * Math.sin(xc * 3.0);
          const dx = (th - xc) * sx, dt = t - tc, d = Math.hypot(dx, dt), a = Math.atan2(dt, dx);
          const Rf = 0.085 * (0.86 + 0.14 * Math.abs(Math.sin(a * 3.5)));
          if (d < Rf) {   // peony head: solid cobalt with white petal lines and a dark heart
            const line = Math.abs(d - Rf * 0.66) < 0.005 || Math.abs(d - Rf * 0.36) < 0.005 || (d > Rf * 0.38 && Math.abs(Math.sin(a * 5)) < 0.08);
            c = line ? 0.05 : (d < Rf * 0.2 ? 1 : 0.88); break;
          }
          for (const s2 of [-1, 1]) {   // a pair of leaves beside each flower
            const lx = (th - xc) * sx - s2 * 0.11, lt = dt + 0.03 * s2, la = s2 * 0.6;
            const qx = lx * Math.cos(la) + lt * Math.sin(la), qy = -lx * Math.sin(la) + lt * Math.cos(la);
            if ((qx / 0.055) ** 2 + (qy / 0.02) ** 2 < 1) c = Math.max(c, Math.abs(qy) < 0.003 ? 0.15 : 0.85);
          }
        }
        break;
      }
      case 'lotus': { // lotus-petal panels (莲瓣纹)
        if (band(0.855)) { c = 1; break; }
        const p = frac(th * 9 / Math.PI) - 0.5, h = (t - 0.865) / 0.065;
        const top = 0.08 + 0.92 * Math.pow(Math.abs(p) * 2, 1.6);   // pointed arch
        if (h > top) c = (h < top + 0.18 || Math.abs(Math.abs(p) - 0.5) < 0.05) ? 1 : 0.35;
        break;
      }
      case 'foot': if (band(0.95, 0.006) || t > 0.985) c = 1; break;
    }
    return { zone: zone[0], c };
  }

  // ---- Blooms -------------------------------------------------
  // role a/b/c = primary / secondary / light colour (mapped by each style)
  // sq   = foreshortening (1 = facing viewer, >1 = tilted away / profile)
  // rot  = rotation of the foreshortened ellipse
  // face = where the heart sits inside the bloom, in fractions of r (3/4 views)
  // Array order = painting order: later entries overlap earlier ones.
  // Five large blooms + three buds (layout from the reference painting), fitted above the slender-necked vase.
  const BLOOMS = [
    { u: 0.50, y: 0.116, r: 0.040, role: 'b', sq: 1.25, rot: 0.1, face: [0, 0], bud: true },        // bud, top centre
    { u: 0.128, y: 0.43, r: 0.046, role: 'b', sq: 1.25, rot: -0.4, face: [0, 0], bud: true },       // bud, far left
    { u: 0.79, y: 0.675, r: 0.045, role: 'b', sq: 1.25, rot: 0.5, face: [0, 0], bud: true },         // bud, lower right
    { u: 0.31, y: 0.288, r: 0.187, role: 'b', sq: 1.15, rot: -0.25, face: [-0.10, -0.08], type: 'double' }, // red, top left
    { u: 0.687, y: 0.27, r: 0.19, role: 'c', sq: 1.20, rot: 0.25, face: [0.12, -0.08], type: 'double' },  // white, top right
    { u: 0.828, y: 0.49, r: 0.11, role: 'b', sq: 1.35, rot: 0.45, face: [0.20, 0.0], type: 'double' },    // small red, right
    { u: 0.256, y: 0.578, r: 0.18, role: 'c', sq: 1.25, rot: -0.20, face: [-0.12, 0.10], type: 'semi' },   // white, lower left
    { u: 0.546, y: 0.49, r: 0.225, role: 'a', sq: 1.10, rot: 0.05, face: [0.03, 0.06], type: 'semi' },     // FOCAL pink, centre
    { u: 0.24, y: 1.215, r: 0.078, role: 'b', sq: 2.1, rot: -0.12, face: [0.0, -0.30], fallen: true, type: 'semi' }, // lying on the table
    // loose petals scattered on the table
    { u: 0.35, y: 1.262, r: 0.036, role: 'b', sq: 1.55, rot: 0.45, face: [0, 0], fallen: true, type: 'petal' },
    { u: 0.69, y: 1.232, r: 0.040, role: 'a', sq: 1.55, rot: -2.6, face: [0, 0], fallen: true, type: 'petal' },
    { u: 0.79, y: 1.285, r: 0.033, role: 'c', sq: 1.55, rot: 2.2, face: [0, 0], fallen: true, type: 'petal' },
  ];

  // ---- Peony petal model ---------------------------------------
  // Each open bloom = concentric rings of broad, ruffled petals radiating
  // from the (possibly off-centre) heart. Inner rings lie on top.
  // 'semi'  : semi-double, golden stamens visible in the centre
  // 'double': fully double, centre filled with small crumpled petals
  // 'bud'   : round closed bud hugged by green sepals
  const RINGS = [
    { rf: 1.00, n: 6, w: 1.55 },   // outer guard petals: broad, spread flat, finely notched, NOT rolled
    { rf: 0.78, n: 7, w: 1.40 },
    { rf: 0.64, n: 7, w: 1.35 },
    { rf: 0.47, n: 8, w: 1.30 },
    { rf: 0.30, n: 9, w: 1.30 },   // double blooms only
  ];
  const STAMEN = 0.21;
  BLOOMS.forEach((b, i) => { if (!b.type) b.type = b.bud ? 'bud' : (b.fallen || [3, 8, 10].includes(i)) ? 'semi' : 'double'; });
  const nRings = b => b.type === 'double' ? 5 : 4;
  // Every open bloom has stamens, varying in size and in how much the inner
  // petals veil them: [stamen radius (fraction of bloom), veil 0 = fully shown .. 1 = hidden]
  const STAMENS = { 3: [0.15, 0.45], 4: [0.15, 0.5], 5: [0.13, 0.6], 6: [0.17, 0], 7: [0.22, 0], 8: [0.16, 0] };
  BLOOMS.forEach((b, i) => { const st = STAMENS[i]; if (st) { b.stamen = st[0]; b.veil = st[1]; } });
  const stamenHit = (b, dn) => ({ part: dn / b.stamen < 0.32 ? 'pistil' : 'stamen', dn, along: dn / b.stamen, s: 0, grain: Math.random() });

  function toLocal(b, u, y) {
    const dx = u - b.u, dy = y - b.y, c = Math.cos(-b.rot), s = Math.sin(-b.rot);
    return [dx * c - dy * s, (dx * s + dy * c) * b.sq];
  }
  function toScene(b, lx, ly) {
    const c = Math.cos(b.rot), s = Math.sin(b.rot), yy = ly / b.sq;
    return [b.u + lx * c - yy * s, b.y + lx * s + yy * c];
  }
  function heart(i) { const b = BLOOMS[i]; return toScene(b, b.face[0] * b.r, b.face[1] * b.r); }
  // distance from the heart to the bloom's circle along local direction (dx,dy)
  function reach(b, dx, dy) {
    const hx = b.face[0] * b.r, hy = b.face[1] * b.r, hd = hx * dx + hy * dy;
    return -hd + Math.sqrt(Math.max(0, hd * hd - (hx * hx + hy * hy) + b.r * b.r));
  }
  // ruffled, rounded petal tip profile across the petal (s = -1..1)
  const tip = (s, k, j) => 1 - 0.30 * s * s + 0.05 * Math.sin(s * 7.5 + k * 1.9 + j) + 0.025 * Math.sin(s * 17 + k);
  // INCURVED petals: the tip rolls over towards the heart. Seen from the front the
  // petal's outline is the smooth rounded crest of the roll; the ruffled tip edge
  // lies further in, on top of the petal itself, casting a shadow beneath it.
  const crestT = (s, k, j) => 1 - 0.28 * s * s + 0.012 * Math.sin(s * 9 + k + j);
  const curlOf = (b, j) => j === 0 ? 0 : (0.1 + 0.085 * j) * (b.type === 'semi' ? 0.85 : 1);   // guard ring flat; inner rings roll over more
  const guardT = (s, k) => 1 - 0.14 * s * s + 0.03 * Math.sin(s * 7.5 + k * 1.9) + 0.018 * Math.abs(Math.sin(s * 19 + k)) - 0.02;
  const outline = (s, k, j) => j === 0 ? guardT(s, k) : crestT(s, k, j);   // guard petals: round with fine notches
  const LIGHT_ANG = Math.atan2(-0.8, -0.6);
  const P_clamp = x => Math.max(0, Math.min(1, x));
  const ringPhase = (i, j, n) => i * 0.7 + j * Math.PI / n;
  function dirToScene(b, th) { const dx = Math.cos(th), dy = Math.sin(th) / b.sq, c = Math.cos(b.rot), s = Math.sin(b.rot); return Math.atan2(dx * s + dy * c, dx * c - dy * s); }

  function bloomHit(b, i, lx, ly) {
    if (b.type === 'petal') {   // one broad petal: narrow base at (-r, 0), ruffled tip towards +x
      const px = lx + b.r, py = ly, rho = Math.hypot(px, py), phi = Math.atan2(py, px), hw = 0.9;
      const sp = phi / hw; if (Math.abs(sp) >= 1 || px <= 0) return null;
      const lim = 2 * b.r * tip(sp, i, 0); if (rho >= lim) return null;
      return { part: 'petal', ring: 0, petal: 0, s: sp, along: rho / lim, th: 0, dn: rho / lim, nr: 1 };
    }
    if (b.type === 'bud') {
      if (lx * lx + ly * ly >= b.r * b.r) return null;
      const sep = ly > b.r * (0.22 + 0.14 * Math.cos(lx / b.r * 9.4));
      return { part: sep ? 'sepal' : 'bud', dn: Math.hypot(lx, ly) / b.r, s: lx / b.r, along: (ly / b.r + 1) / 2 };
    }
    if (lx * lx + ly * ly > b.r * b.r * 1.1) return null;
    const hx = b.face[0] * b.r, hy = b.face[1] * b.r, px = lx - hx, py = ly - hy, rho = Math.hypot(px, py) || 1e-9;
    const phi = Math.atan2(py, px), dn = rho / reach(b, px / rho, py / rho);
    const sR = b.stamen ?? STAMEN;
    if (b.type === 'semi' && dn < sR) return stamenHit({ stamen: sR }, dn);
    for (let j = nRings(b) - 1; j >= 0; j--) {
      // on double blooms the stamens sit just under the innermost ring, whose petals
      // are spread apart (by the veil amount) so the stamens peek through the gaps
      if (b.type === 'double' && j === nRings(b) - 2 && dn < sR) return stamenHit({ stamen: sR }, dn);
      const g = RINGS[j], ph = ringPhase(i, j, g.n);
      const hw = Math.PI / g.n * (b.type === 'double' && j === nRings(b) - 1 ? (0.42 + 0.5 * (b.veil ?? 1)) : g.w);   // innermost ring coverage 42%..92%
      let best = null;
      for (let k = 0; k < g.n; k++) {
        const th = ph + k * 2 * Math.PI / g.n;
        let dphi = phi - th; dphi = Math.atan2(Math.sin(dphi), Math.cos(dphi));
        const s = dphi / hw; if (Math.abs(s) >= 1) continue;
        const crest = g.rf * outline(s, k, j); if (dn >= crest) continue;
        if (!best || s < best.s) best = { part: 'petal', ring: j, petal: k, s, th, crest };
      }
      if (best) {
        const { s, crest, petal: k } = best;
        const cu = curlOf(b, j) * (1 - 0.35 * s * s);
        const edge = crest * (1 - cu) + crest * 0.6 * cu * (tip(s, k, j) - 1 + 0.3 * s * s);   // ruffled tip edge, folded inward
        const pang = dirToScene(b, best.th), lightC = Math.cos(pang - LIGHT_ANG);
        let face, along, lum, under = 0, roll = 0;
        if (dn > edge) {   // the rolled-over tip: we see its back, a convex crest catching the light
          face = -1; roll = (dn - edge) / Math.max(1e-6, crest - edge);
          along = 0.8 + 0.2 * Math.sin(Math.PI * Math.min(1, roll * 1.05));
          lum = 0.45 + 0.4 * Math.sin(Math.PI * roll) * (0.7 + 0.3 * lightC);
        } else {           // the concave inner face, shaded just under the rolled tip
          face = 1; along = j === 0 ? dn / edge : dn / edge * 0.86;
          under = cu > 0 ? P_clamp(1 - (edge - dn) / 0.07) : 0;
          lum = 0.5 - 0.25 * lightC;
        }
        // shadow cast by the petals of the ring above, just outside their crest
        let occ = under * 0.85;
        if (j + 1 < nRings(b)) {
          const gU = RINGS[j + 1], hwU = Math.PI / gU.n * gU.w, phU = ringPhase(i, j + 1, gU.n);
          for (let kk = 0; kk < gU.n; kk++) {
            let dp = phi - (phU + kk * 2 * Math.PI / gU.n); dp = Math.atan2(Math.sin(dp), Math.cos(dp));
            const sU = dp / hwU; if (Math.abs(sU) >= 1) continue;
            const gap = dn - gU.rf * crestT(sU, kk, j + 1);
            if (gap > 0 && gap < 0.08) occ = Math.max(occ, 1 - gap / 0.08);
          }
        }
        return { ...best, dn, nr: nRings(b), along, face, lum, occ, roll, under };
      }
    }
    return null;
  }
  function inBloom(u, y) {
    for (let i = BLOOMS.length - 1; i >= 0; i--) {
      const b = BLOOMS[i], [lx, ly] = toLocal(b, u, y);
      const h = bloomHit(b, i, lx, ly);
      if (!h) continue;
      const [hu, hv] = heart(i);
      return { i, b, ...h, d: h.dn, ang: Math.atan2(y - hv, u - hu), la: Math.atan2(ly, lx), pang: h.th !== undefined ? dirToScene(b, h.th) : Math.atan2(y - hv, u - hu) };
    }
    return null;
  }
  // outline helpers for contour drawing
  function bloomPoint(i, a) { const b = BLOOMS[i]; return toScene(b, Math.cos(a) * b.r, Math.sin(a) * b.r); }
  function bloomEdge() { return 1; }
  function petalsOf(i) { const b = BLOOMS[i], out = []; if (b.type === 'bud') return out; if (b.type === 'petal') return [{ j: 0, k: 0 }]; for (let j = 0; j < nRings(b); j++) for (let k = 0; k < RINGS[j].n; k++) out.push({ j, k }); return out; }
  function petalPoint(i, j, k, s, frac = 1) {
    if (BLOOMS[i].type === 'petal') {
      const b = BLOOMS[i], th = s * 0.9, rho = 2 * b.r * tip(s, i, 0) * frac;
      return toScene(b, -b.r + Math.cos(th) * rho, Math.sin(th) * rho);
    }
    const b = BLOOMS[i], g = RINGS[j], hw = Math.PI / g.n * g.w, th = ringPhase(i, j, g.n) + k * 2 * Math.PI / g.n + s * hw;
    const dx = Math.cos(th), dy = Math.sin(th), rho = reach(b, dx, dy) * g.rf * outline(s, k, j) * frac;
    return toScene(b, b.face[0] * b.r + dx * rho, b.face[1] * b.r + dy * rho);
  }

  // ---- Stems: curved (quadratic) from the vase mouth -------------
  const STEMS = BLOOMS.map((b, i) => ({ b, i })).filter(o => !o.b.fallen).map(({ b, i }) => {
    const x0 = VASE.cx + (b.u - VASE.cx) * 0.07, y0 = VASE.top + 0.012;
    const cx = x0 + (b.u - x0) * 0.25, cy = y0 + (b.y - y0) * 0.75;   // rise first, then bend
    const pts = [];
    for (let k = 0; k <= 14; k++) { const t = k / 14; pts.push([(1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t * t * b.u, (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t * t * b.y]); }
    return { i, pts, w: 0.0045 + b.r * 0.035 };
  });
  function inStem(u, y) {
    for (const s of STEMS) for (let k = 0; k < s.pts.length - 1; k++) {
      const [x0, y0] = s.pts[k], [x1, y1] = s.pts[k + 1], dx = x1 - x0, dy = y1 - y0;
      const t = ((u - x0) * dx + (y - y0) * dy) / (dx * dx + dy * dy);
      if (t < 0 || t > 1) continue;
      const qx = x0 + dx * t, qy = y0 + dy * t, dist = Math.hypot(u - qx, y - qy);
      if (dist < s.w) return { s, t: (k + t) / (s.pts.length - 1), a: Math.atan2(dy, dx), side: ((u - qx) * -dy + (y - qy) * dx) / Math.hypot(dx, dy) / s.w };
    }
    return null;
  }

  // ---- Leaves: grow from the stems, irregular sizes/angles --------
  const LEAVES = [];
  (() => {
    let k = 4242; const rr = () => { k = (k * 16807) % 2147483647; return (k - 1) / 2147483646; };
    STEMS.forEach(s => {
      const n = 2;
      for (let j = 0; j < n; j++) {
        const t = 0.4 + rr() * 0.45, idx = Math.round(t * (s.pts.length - 1));
        const [x, y] = s.pts[idx], [xa, ya] = s.pts[Math.max(0, idx - 1)];
        const ta = Math.atan2(y - ya, x - xa), side = (j + s.i) % 2 ? 1 : -1;
        const big = rr();
        LEAVES.push({ u: x, y, a: ta + side * (0.7 + rr() * 0.5), len: 0.075 + big * 0.06, w: 0.024 + big * 0.014, curl: (rr() - 0.5) * 0.6 });
      }
    });
    // leaves reaching out from the edge of the bouquet (breaks up the silhouette)
    [[0.10, 0.52, 2.85, 0.12], [0.93, 0.40, 0.05, 0.11], [0.43, 0.13, -2.1, 0.10], [0.58, 0.12, -1.0, 0.10],
     [0.12, 0.70, 2.45, 0.11], [0.78, 0.63, 0.55, 0.11], [0.40, 0.70, 2.3, 0.10], [0.68, 0.68, 0.8, 0.10]]
      .forEach(([u, y, a, len], j) => LEAVES.push({ u, y, a, len, w: 0.028, curl: j % 2 ? -0.35 : 0.35 }));
    // a few leaves spilling over the vase rim
    LEAVES.push({ u: 0.47, y: 0.675, a: 2.55, len: 0.12, w: 0.03, curl: 0.4 });
    LEAVES.push({ u: 0.54, y: 0.68, a: 0.55, len: 0.10, w: 0.026, curl: -0.3 });
    LEAVES.push({ u: 0.51, y: 0.672, a: 1.25, len: 0.075, w: 0.022, curl: 0.2 });
  })();
  // Peony foliage: compound leaf = petiole + 3 leaflets, each cut into 3 pointed lobes
  function lobeHit(u, y, x0, y0, a, len, wf) {
    const dx = u - x0, dy = y - y0, ca = Math.cos(-a), sa = Math.sin(-a);
    const lx = dx * ca - dy * sa; if (lx < 0 || lx > len) return null;
    const ly = dx * sa + dy * ca, t = lx / len, half = len * wf * Math.sin(Math.PI * Math.pow(t, 0.6));
    return Math.abs(ly) < half ? { t, s: ly / half } : null;
  }
  const LEAFLETS = [[-0.85, 0.62], [0.85, 0.62], [0, 0.80]];
  const LOBES = [[-0.45, 0.66], [0.45, 0.66], [0, 1]];
  function inLeaf(u, y) {
    for (let i = LEAVES.length - 1; i >= 0; i--) {
      const L = LEAVES[i], pl = L.len * 0.26;
      const px = L.u + Math.cos(L.a) * pl, py = L.y + Math.sin(L.a) * pl;
      for (const [da, lm] of LEAFLETS) {
        const la = L.a + da + L.curl * 0.3, ll = L.len * lm;
        const bx = px + Math.cos(la) * ll * 0.1, by = py + Math.sin(la) * ll * 0.1;
        for (const [db, m] of LOBES) {
          const h = lobeHit(u, y, bx, by, la + db * (1 + L.curl * 0.2), ll * m, 0.17);
          if (h) return { i, L, part: 'lobe', a: la + db, t: h.t, s: h.s };
        }
      }
      const dx = px - L.u, dy = py - L.y, t = ((u - L.u) * dx + (y - L.y) * dy) / (dx * dx + dy * dy);
      if (t >= 0 && t <= 1 && Math.hypot(u - (L.u + dx * t), y - (L.y + dy * t)) < 0.0035) return { i, L, part: 'petiole', a: L.a, t, s: 0 };
    }
    return null;
  }

  function shadow(u, y) {
    if (y < TABLE_Y) return 0;
    const sx = u - (VASE.cx + 0.11), sy = (y - (VASE.bottom - 0.01)) / 0.035;
    let sh = Math.exp(-Math.pow(sx / 0.13, 2) - sy * sy);
    // soft contact shadows under the fallen bloom and loose petals
    BLOOMS.forEach(b => { if (!b.fallen) return;
      const dx = (u - b.u - b.r * 0.25) / (b.r * 1.15), dy = (y - b.y - b.r * 0.18) / (b.r * 0.6);
      sh = Math.max(sh, 0.55 * Math.exp(-(dx * dx + dy * dy))); });
    return sh;
  }

  // Topmost region at (u, y). k: 'wall' | 'table' | 'vase' | 'stem' | 'leaf' | 'bloom'
  function region(u, y) {
    const bl = inBloom(u, y); if (bl) return { k: 'bloom', z: 4, ...bl };
    const lf = inLeaf(u, y); if (lf) return { k: 'leaf', z: 3, ...lf };
    const st = inStem(u, y); if (st) return { k: 'stem', z: 2.5, ...st };
    const hw = vaseHalf(y);
    if (hw > 0 && Math.abs(u - VASE.cx) < hw) { const dx = (u - VASE.cx) / hw, t = (y - VASE.top) / (VASE.bottom - VASE.top), th = Math.asin(Math.max(-1, Math.min(1, dx))); return { k: 'vase', z: 2, dx, t, th, hw, ...vaseDecor(th, t, hw) }; }
    if (y > TABLE_Y) return { k: 'table', z: 1, sh: shadow(u, y), t: (y - TABLE_Y) / (ASPECT - TABLE_Y) };
    return { k: 'wall', z: 0, t: y / TABLE_Y };
  }

  return { build() {}, ASPECT, TABLE_Y, VASE, ZONES, vaseDecor, LIGHT, BLOOMS, LEAVES, STEMS, RINGS, vaseHalf, bloomEdge, bloomPoint, petalsOf, petalPoint, heart, inBloom, inLeaf, inStem, region };
})();
