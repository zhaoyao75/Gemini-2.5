// Vincent van Gogh – "Sunflowers"-style still life (after the reference painting):
// golden ochre wall in broad swirling strokes, burnt-orange table, thick
// palette-knife impasto; peonies built from short curved strokes that follow
// each petal's rim, with cream highlight ridges and crimson hollows.
STYLES.vangogh_sunflowers = {
  name: '梵高 · 向日葵',
  pal: {
    wall: ['#e8a62a', '#f2bd3c', '#d68e1c', '#f7cf5a', '#c97f16'],
    table: ['#b8561c', '#cf6e26', '#9a4214', '#e08a3a'],
    porcelain: ['#f3ead2', '#e8dcbc', '#fbf5e6', '#efe2c4'], cobalt: ['#26489a', '#1e3a86', '#33559f'], wash: '#7d95cf',
    leaf: ['#2e5a2c', '#4d7b34', '#1f4022', '#9db054'],
    stem: ['#4a6e2c', '#6a8a36'], sepal: ['#4f7a2e', '#7a9a3c'],
    bloom: {
      a: { base: '#6a1016', mid: '#cc3f34', tip: '#ec7c62', rim: '#ffcfb4' },   // coral red
      b: { base: '#4a0810', mid: '#a5222e', tip: '#d8565a', rim: '#f2a49a' },   // deep red
      c: { base: '#b8461a', mid: '#f0943e', tip: '#fbcf8c', rim: '#fff1d4' },   // peach / apricot
    },
    stamen: ['#f2b21e', '#e08a10', '#ffd860', '#b8680c'],
    pistil: ['#e4d08a', '#c9b45a', '#e89a7a'],
  },
  color(reg, u, y) {
    const H = P.hex, pal = this.pal, pick = arr => H(arr[(P.rand() * arr.length) | 0]);
    switch (reg.k) {
      case 'wall': {
        let c = P.mix(H(pal.wall[0]), H(pal.wall[1]), 0.5 + 0.5 * Math.sin(u * 6 + y * 4 + Math.sin(y * 9)));
        if (P.rand() < 0.35) c = P.mix(c, pick(pal.wall), 0.75);
        return c;
      }
      case 'table': {
        let c = P.mix(H(pal.table[0]), H(pal.table[1]), 0.5 + 0.5 * Math.sin(u * 9 + y * 40));
        if (P.rand() < 0.25) c = P.mix(c, pick(pal.table), 0.7);
        return P.mix(c, H('#6a2a10'), P.clamp(reg.sh * 0.75));
      }
      case 'vase': {
        let c = P.mix(pick(pal.porcelain), H('#f2c860'), P.clamp(reg.dx * 0.6) * 0.3);   // warm wall reflected on the right
        if (reg.c > 0.6) c = P.mix(pick(pal.cobalt), c, 0.06);
        else if (reg.c > 0.2) c = P.mix(c, H(pal.wash), 0.65);
        const hi = Math.exp(-Math.pow((reg.dx + 0.45) / 0.14, 2));
        c = P.mix(c, [255, 252, 240], hi * 0.45 * (reg.c > 0.6 ? 0.4 : 1));
        return P.shade(c, 1 - Math.pow(Math.abs(reg.dx), 2.5) * 0.35);
      }
      case 'stem': return P.mix(H(pal.stem[0]), H(pal.stem[1]), P.clamp(0.5 - reg.side * 0.5));
      case 'leaf': {
        if (reg.part === 'petiole') return H(pal.stem[0]);
        let c = P.mix(H(pal.leaf[0]), H(pal.leaf[1]), P.clamp(0.5 - reg.s * 0.6));
        if (Math.abs(reg.s) < 0.1) c = P.mix(c, H(pal.leaf[3]), 0.55);                  // light midrib
        if (P.rand() < 0.12) c = P.mix(c, H(pal.leaf[3]), 0.4);
        return P.mix(c, H(pal.leaf[2]), P.clamp((Math.abs(reg.s) - 0.6) * 2));
      }
      case 'bloom': {
        const B = pal.bloom[reg.b.role];
        if (reg.part === 'pistil') return pick(pal.pistil);
        if (reg.part === 'stamen') return P.mix(H(pal.stamen[0]), H(pal.stamen[3]), reg.grain ?? P.rand());
        if (reg.part === 'sepal') return P.mix(H(pal.sepal[0]), H(pal.sepal[1]), P.rand());
        if (reg.part === 'bud') return P.mix(H(B.base), H(B.mid), 0.45 + 0.4 * (1 - reg.dn) * (reg.s < 0 ? 1 : 0.6));
        // petal: crimson hollow at the base -> body colour -> pale tip, cream ridge on the rim
        let c = P.mix(H(B.base), H(B.mid), P.clamp(0.15 + reg.along * 1.5));
        c = P.mix(c, H(B.tip), P.clamp((reg.along - 0.55) / 0.4) * 0.6);
        if (reg.face > 0) c = P.mix(c, P.shade(H(B.base), 0.8), P.clamp(1 - reg.along / 0.38) * 0.55);
        else c = P.mix(c, H(B.base), 0.12);
        c = P.shade(c, 0.82 + 0.3 * (reg.lum ?? 0.5));
        c = P.mix(c, P.shade(H(B.base), 0.7), P.clamp((reg.occ || 0) * 1.1) * 0.75);   // deep crimson crevices under each petal
        if (reg.along > 0.86 && P.rand() < 0.85) c = P.mix(c, H(B.rim), 0.7 + 0.3 * P.clamp(reg.lum ?? 0.5)); // cream impasto ridge on the rim
        return c;
      }
    }
  },
  angle(reg, u, y) {
    switch (reg.k) {
      case 'wall': return 0.55 * Math.sin(u * 4.2 + y * 3.1) + 0.45 * Math.cos(y * 5.3 - u * 2.2) - 0.45;   // broad swirls
      case 'table': return 0.05 * Math.sin(u * 20);
      case 'vase': return Math.atan(reg.dx * 0.4) * 0.9;
      case 'leaf': return reg.a + reg.s * 0.25;
      case 'stem': return reg.a;
      case 'bloom': {
        if (reg.part === 'pistil' || reg.part === 'stamen') return P.R(0, Math.PI * 2);
        if (reg.part === 'bud' || reg.part === 'sepal') return reg.ang + Math.PI / 2;
        // short curved dabs that follow the petal's rim; radial near the base
        return reg.along > 0.32 ? reg.pang + Math.PI / 2 + reg.s * 0.35 : reg.pang;
      }
    }
  },
  paint() {
    const ctx = P.ctx;
    ctx.fillStyle = '#e0a028'; ctx.fillRect(0, 0, P.W, P.H);
    const per = { vase: { len: 0.6, wid: 0.65 }, stem: { len: 1.2, wid: 0.6 }, leaf: { len: 0.9, wid: 0.8 },
                  bloom: { len: 0.42, wid: 0.62 }, table: { len: 1.4 }, wall: { len: 1.5, wid: 1.2 } };
    P.strokePass(this, { spacing: 0.0125, len: 0.04, wid: 0.0125, perRegion: per });
    P.strokePass(this, { spacing: 0.0085, len: 0.028, wid: 0.0085, perRegion: per });
    P.strokePass(this, { spacing: 0.006, len: 0.02, wid: 0.006, perRegion: per });
    P.strokePass(this, { spacing: 0.0038, len: 0.011, wid: 0.0042, only: ['bloom', 'leaf'], impasto: 1.2, perRegion: { bloom: { len: 0.9 } } });
    const cob = P.hex(this.pal.cobalt[0]), wash = P.hex(this.pal.wash);
    P.overlay((reg, px, py) => {
      if (reg.k !== 'vase' || reg.c < 0.2) return null;
      const n = 0.85 + 0.15 * Math.sin(px * 0.9 + py * 0.35) * Math.sin(py * 0.7);
      const shadeF = 1 - Math.pow(Math.abs(reg.dx), 2.5) * 0.3;
      return reg.c > 0.6 ? [P.shade(cob, shadeF * (1.05 - 0.15 * n)), 0.88 * n] : [P.shade(wash, shadeF), 0.55 * n];
    }, [SCENE.VASE.cx - 0.22, SCENE.VASE.top, SCENE.VASE.cx + 0.22, SCENE.VASE.bottom]);
    P.strokePass(this, { spacing: 0.006, len: 0.012, wid: 0.004, keep: 0.12, only: ['vase'], impasto: 0.6, alpha: 0.6 });
    P.vaseContour('#2a4690', 0.003);
    P.tableLine('#7a3410', 0.004);
    P.strokePass(this, { spacing: 0.011, len: 0.016, wid: 0.0045, keep: 0.12, perRegion: per });
    P.canvasTexture(0.03);
  },
};
