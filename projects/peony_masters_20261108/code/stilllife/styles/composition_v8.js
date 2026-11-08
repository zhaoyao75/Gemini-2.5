// Flat colour map of the shared composition (reference for designing new styles)
// shared petal shading: base colour at the heart, body colour, lit rim colour
function petalShade(reg, base, body, rim) {
  let c = P.mix(base, body, P.clamp(0.1 + reg.along * 1.1));
  if (reg.face > 0) c = P.mix(c, P.shade(base, 0.72), P.clamp(1 - reg.along / 0.4) * 0.55);   // deep inside the cup
  else c = P.mix(c, base, 0.18);                                                            // outer face, a bit deeper
  if (reg.along > 0.82) c = P.mix(c, rim, (reg.along - 0.82) / 0.18 * 0.75);                 // silky lit rim
  c = P.shade(c, 0.86 + 0.24 * (reg.lum ?? 0.5));                                           // light from upper left
  c = P.mix(c, P.shade(base, 0.78), (reg.occ || 0) * 0.45);                                 // shadow of the petal in front
  return P.shade(c, 1 - P.clamp((Math.abs(reg.s) - 0.75) * 3) * 0.1);                       // petal edges curl away
}
STYLES.composition = {
  name: '构图参考（平涂）',
  paint() {
    const H = P.hex;
    const C = { wall: H('#dcd6c8'), table: H('#a89a80'), vase: H('#6f7f99'), leaf: H('#6f9068'), stem: H('#5f7a52') };
    const B = { a: [H('#b8406a'), H('#f2b0c6')], b: [H('#7a1430'), H('#d84a62')], c: [H('#d88aa0'), H('#fbf1ee')] };
    P.fillRegions((reg) => {
      if (reg.k === 'bloom') {
        const pal = B[reg.b.role];
        if (reg.part === 'pistil') return P.mix(H('#cfdc9a'), H('#e7a6b4'), 0.5 + 0.5 * Math.sin(reg.ang * 5));
        if (reg.part === 'stamen') return P.shade(P.mix(H('#f0c234'), H('#c98a18'), reg.grain), 1.05 - reg.dn * 0.2);
        if (reg.part === 'sepal') return H('#5f8a4a');
        if (reg.part === 'bud') return P.mix(pal[0], pal[1], 0.35 + reg.along * 0.2);
        return petalShade(reg, pal[0], pal[1], P.mix(pal[1], [255, 255, 255], 0.55));
      }
      if (reg.k === 'leaf') return reg.part === 'petiole' ? C.stem : P.mix(C.leaf, H('#9ab887'), P.clamp(0.5 - reg.s * 0.5) * 0.5);
      if (reg.k === 'vase') {
        const c = P.mix(H('#f5f2ea'), H('#1f3c8c'), reg.c);
        return P.shade(c, 1 - Math.pow(Math.abs(reg.dx), 3) * 0.3 + (reg.dx < -0.3 && reg.dx > -0.6 ? 0.05 : 0));
      }
      if (reg.k === 'table') return P.mix(C.table, [60, 55, 50], reg.sh * 0.5);
      return C[reg.k];
    });
    P.vaseContour('#333', 0.003, 0); P.tableLine('#444', 0.003);
    P.petalContours(b => b.role === 'b' ? '#6a1428' : '#b0607a', 0.0009, 0.35, 3);   // faint, outer petals only
  },
};
