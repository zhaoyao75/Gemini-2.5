// Vincent van Gogh – "Sunflowers" (1888/89) style:
// chrome-yellow monochrome palette, hatched background, ochre table,
// thick impasto, blue/ochre broken contours.
STYLES.vangogh_sunflowers = {
  name: '梵高 · 向日葵',
  pal: {
    wall: ['#ecd067', '#f3df84', '#dcbc4c', '#d4cb6c'],
    table: ['#d99a2b', '#e8b548', '#bf7a1e', '#f2cc62'],
    porcelain: ['#f6f1e2', '#ece3c6', '#fffbef', '#dfe6d8'], cobalt: ['#1d3a8f', '#2a4fa8', '#14296e'], wash: '#7f9bd2',
    leaf: ['#6f7d2a', '#a3a845', '#4c5620', '#c2b54a'],
    // peony colours against the chrome-yellow world (complementary contrast)
    bloom: {
      a: { base: '#a82a5a', mid: '#e8779f', tip: '#fbd0de' },   // peony pink
      b: { base: '#5e0a22', mid: '#c0213f', tip: '#f2737a' },   // deep red / magenta
      c: { base: '#d6849f', mid: '#f3d0da', tip: '#fff6f2', blotch: '#7a1f4f', cool: '#b9a8d2' }, // white with a purple blotch (紫斑)
    },
    stamen: ['#f3c63a', '#e8a52a', '#fff0a0', '#c97a1c'],
    pistil: ['#d8e3a0', '#c4d47e', '#eaa8b8'],
    stem: ['#5f7a2a', '#8a9a3a'], sepal: ['#5c7a2c', '#86a040'],
  },
  color(reg, u, y) {
    const H = P.hex, pal = this.pal, pick = arr => H(arr[(P.rand() * arr.length) | 0]);
    switch (reg.k) {
      case 'wall': {
        let c = P.mix(H(pal.wall[0]), H(pal.wall[1]), 0.5 + 0.5 * Math.sin(u * 11 + y * 7));
        if (P.rand() < 0.25) c = P.mix(c, pick(pal.wall), 0.7);
        return c;
      }
      case 'table': {
        let c = P.mix(H(pal.table[0]), H(pal.table[1]), 0.5 + 0.5 * Math.sin(u * 13 + y * 30));
        if (P.rand() < 0.2) c = P.mix(c, pick(pal.table), 0.7);
        return P.mix(c, H('#8a6a2a'), P.clamp(reg.sh * 0.7));
      }
      case 'vase': { // blue-and-white porcelain: cool white glaze with warm reflections, cobalt pattern
        let c = P.mix(pick(pal.porcelain), H('#f2d978'), P.clamp(reg.dx * 0.6) * 0.45);   // yellow wall reflected on the right
        if (reg.c > 0.6) c = P.mix(pick(pal.cobalt), c, 0.08);
        else if (reg.c > 0.2) c = P.mix(c, H(pal.wash), 0.7);
        const hi = Math.exp(-Math.pow((reg.dx + 0.45) / 0.14, 2));                          // glaze highlight
        c = P.mix(c, [255, 255, 255], hi * 0.5 * (reg.c > 0.6 ? 0.4 : 1));
        return P.shade(c, 1 - Math.pow(Math.abs(reg.dx), 2.5) * 0.32);
      }
      case 'stem': return P.mix(H(pal.stem[0]), H(pal.stem[1]), P.clamp(0.5 - reg.side * 0.5));
      case 'leaf': {
        if (reg.part === 'petiole') return H(pal.stem[0]);
        let c = P.mix(H(pal.leaf[0]), H(pal.leaf[1]), P.clamp(0.5 - reg.s * 0.5));
        if (Math.abs(reg.s) < 0.12) c = P.mix(c, H(pal.leaf[3]), 0.6);
        return P.mix(c, H(pal.leaf[2]), P.clamp((Math.abs(reg.s) - 0.65) * 2));
      }
      case 'bloom': {
        const B = pal.bloom[reg.b.role];
        if (reg.part === 'pistil') return pick(pal.pistil);
        if (reg.part === 'stamen') return P.mix(H(pal.stamen[0]), H(pal.stamen[3]), reg.grain ?? P.rand());
        if (reg.part === 'sepal') return P.mix(H(pal.sepal[0]), H(pal.sepal[1]), P.rand());
        if (reg.part === 'bud') return P.mix(H(B.base), H(B.mid), 0.45 + 0.4 * (1 - reg.dn) * (reg.s < 0 ? 1 : 0.6));
        // petal: 3-D cup shading (inside of the bowl dark, lit silky rim, shadow of nearer petals)
        let c = P.mix(H(B.base), H(B.mid), P.clamp(0.1 + reg.along * 1.4));
        c = P.mix(c, H(B.tip), P.clamp((reg.along - 0.55) / 0.45) * 0.8);
        if (B.blotch && reg.along < 0.2 && reg.face > 0) c = P.mix(c, H(B.blotch), 0.6);
        if (reg.face > 0) c = P.mix(c, P.shade(H(B.base), 0.75), P.clamp(1 - reg.along / 0.4) * 0.5);
        else c = P.mix(c, H(B.base), 0.15);
        c = P.shade(c, 0.86 + 0.24 * (reg.lum ?? 0.5));
        if (B.cool) c = P.mix(c, H(B.cool), P.clamp(0.45 - (reg.lum ?? 0.5)) * 0.6);   // lavender shadow on white
        c = P.mix(c, P.shade(H(B.cool || B.base), 0.82), (reg.occ || 0) * 0.45);
        return c;
      }
    }
  },
  angle(reg, u, y) {
    switch (reg.k) {
      case 'wall': { // basket-weave hatching in small patches, like the Sunflowers background
        const cell = ((u * 9) | 0) + ((y * 9) | 0);
        return (cell % 2 ? 1.15 : 1.95) + 0.25 * Math.sin(u * 23 + y * 17);
      }
      case 'table': return 0.05 * Math.sin(u * 20);
      case 'vase': return Math.atan(reg.dx * 0.4) * 0.9;
      case 'leaf': return reg.a + reg.s * 0.3;
      case 'stem': return reg.a;
      case 'bloom': {
        if (reg.part === 'pistil') return P.R(0, Math.PI * 2);
        if (reg.part === 'stamen') return reg.ang + P.R(-0.3, 0.3);         // filaments radiate from the heart
        if (reg.part === 'bud' || reg.part === 'sepal') return reg.ang + Math.PI / 2;
        // along the petal from base to tip, curling across the ruffled edge
        return reg.along > 0.94 ? reg.pang + Math.PI / 2 : reg.pang + reg.s * 0.55;   // base -> tip, fanning with the petal
      }
    }
  },
  paint() {
    const ctx = P.ctx;
    ctx.fillStyle = '#e3c15a'; ctx.fillRect(0, 0, P.W, P.H);
    const per = { bloom_center: {}, vase: { len: 0.6, wid: 0.65 }, stem: { len: 1.2, wid: 0.6 }, leaf: { len: 0.7, wid: 0.7 }, bloom: { len: 0.55, wid: 0.62 }, table: { len: 1.4 }, wall: { len: 0.8 } };
    P.strokePass(this, { spacing: 0.0125, len: 0.04, wid: 0.0125, perRegion: per });
    P.strokePass(this, { spacing: 0.0085, len: 0.028, wid: 0.0085, perRegion: per });
    P.strokePass(this, { spacing: 0.006, len: 0.02, wid: 0.006, perRegion: per });
    // a finer pass on the flowers keeps individual petals readable
    P.strokePass(this, { spacing: 0.0042, len: 0.012, wid: 0.0042, only: ['bloom'], impasto: 0.7 });
    // cobalt motifs brushed on with a fine brush so they stay legible
    const cob = P.hex(this.pal.cobalt[0]), wash = P.hex(this.pal.wash);
    P.overlay((reg, px, py) => {
      if (reg.k !== 'vase' || reg.c < 0.2) return null;
      const n = 0.85 + 0.15 * Math.sin(px * 0.9 + py * 0.35) * Math.sin(py * 0.7);  // brushy unevenness
      const shadeF = 1 - Math.pow(Math.abs(reg.dx), 2.5) * 0.3;
      return reg.c > 0.6 ? [P.shade(cob, shadeF * (1.05 - 0.15 * n)), 0.88 * n] : [P.shade(wash, shadeF), 0.55 * n];
    }, [SCENE.VASE.cx - 0.2, SCENE.VASE.top, SCENE.VASE.cx + 0.2, SCENE.VASE.bottom]);
    P.strokePass(this, { spacing: 0.006, len: 0.012, wid: 0.004, keep: 0.12, only: ['vase'], impasto: 0.6, alpha: 0.6 });
    P.vaseContour('#2f4c96', 0.0035);
    P.tableLine('#3b5ba8', 0.004);
    P.petalContours(b => b.role === 'b' ? '#4a0a1c' : b.role === 'a' ? '#9a3058' : '#9a6088', 0.0016, 0.4, 2);   // outer petals only, broken
    P.strokePass(this, { spacing: 0.011, len: 0.016, wid: 0.0045, keep: 0.15, perRegion: per });
    P.canvasTexture(0.02);
  },
};
