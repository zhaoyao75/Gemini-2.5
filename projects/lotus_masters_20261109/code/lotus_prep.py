"""Lotus line art -> labelled regions (same output maps as the peony version).
Outputs in the given folder: cls.png, cid.png, line.png, flow.png, meta.json, debug_classes.png
Class ids are kept identical to the peony pipeline so the painters can be reused:
  WALL = background / pond haze, TABLE = water inside the bowl, VASE_W = bowl body, VASE_B = lotus-petal relief on the bowl,
  STEM, LEAF, PETAL, STAMEN (seed pod + stamens), BUD, SEPAL
Fixes are applied per REGION (seed points), never with coordinate rectangles.
"""
import sys, json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

src, out = sys.argv[1], sys.argv[2]
g = np.asarray(Image.open(src).convert('L')).astype(np.float32)
H, W = g.shape
line = g < 190
line_closed = ndi.binary_dilation(line, iterations=2)
lab, n = ndi.label(~line_closed)
print('regions', n)

WALL, TABLE, VASE_W, VASE_B, STEM, LEAF, PETAL, STAMEN, BUD, SEPAL = range(10)
# (cx, cy, rx, ry, stamen centre, role)
BLOOMS = [
    (690, 500, 310, 262, (735, 462), 'a'),    # big top-right bloom
    (305, 745, 225, 165, (318, 702), 'b'),    # left bloom
]
BUDS = [(305, 232, 72)]                       # closed bud, top left
BOWL = dict(x0=245, x1=812, y0=1075, y1=1410, cx=528)
POD_CENTRES = [(735, 462, 62), (318, 702, 62), (592, 790, 52)]   # seed pods: small regions near them are STAMEN

idx = np.arange(n + 1)
area = ndi.sum(np.ones_like(lab), lab, idx)
cy, cx = [np.array(v) for v in zip(*ndi.center_of_mass(np.ones_like(lab), lab, idx[1:]))]
cy = np.concatenate([[0], cy]); cx = np.concatenate([[0], cx])
dist = ndi.distance_transform_edt(lab > 0)
thick = ndi.maximum(dist, lab, idx)
border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}

cls_of = np.zeros(n + 1, np.uint8); bloom_of = np.zeros(n + 1, np.uint8)
for r in range(1, n + 1):
    x, y, a = cx[r], cy[r], area[r]
    if r in border or a > 150000:
        cls_of[r] = WALL; continue
    if BOWL['x0'] < x < BOWL['x1'] and BOWL['y0'] + 10 < y < BOWL['y1']:
        cls_of[r] = VASE_B if (a > 1500 and y > 1170) else VASE_W; continue
    hit = False
    for (px_, py_, pr) in POD_CENTRES:
        if (x - px_) ** 2 + (y - py_) ** 2 < pr ** 2 and a < 700:
            cls_of[r] = STAMEN; hit = True; break
    if hit: continue
    for (bx, by, br) in BUDS:
        if (x - bx) ** 2 + (y - by) ** 2 < (br * 1.25) ** 2:
            cls_of[r] = SEPAL if (y > by + br * 0.45 or a < 120) else BUD; hit = True; break
    if hit: continue
    for k, (bx, by, rx, ry, _, _) in enumerate(BLOOMS):
        if ((x - bx) / rx) ** 2 + ((y - by) / ry) ** 2 < 1.0:
            cls_of[r] = PETAL; bloom_of[r] = k + 1; hit = True; break
    if hit: continue
    cls_of[r] = STEM if (thick[r] < 9 and a > 150) else LEAF

# ---- region-level fixes from visual inspection: (x, y, class, bloom id)  — any pixel inside the region will do
exec(open(sys.argv[3]).read()) if len(sys.argv) > 3 else None
FIX = globals().get('FIX', [])
for (fx, fy, fc, fb) in FIX:
    win = lab[max(fy - 6, 0):fy + 7, max(fx - 6, 0):fx + 7]; vals = win[win > 0]
    if len(vals) == 0: print('FIX found no region near', fx, fy); continue
    r_ = np.bincount(vals).argmax()
    cls_of[r_] = fc; bloom_of[r_] = fb
clsmap = cls_of[lab]
bloommap = bloom_of[lab]

puff = np.where(lab > 0, dist / np.maximum(thick[lab], 1), 0)
puff[np.isin(clsmap, [WALL, TABLE])] = 1.0

meta = {'W': W, 'H': H, 'blooms': [[b[0], b[1], b[2], b[3], b[5]] for b in BLOOMS], 'vase': BOWL, 'table_y': 99999, 'angle': {}}
yy, xx = np.nonzero(lab > 0)
ll = lab[yy, xx]
order = np.argsort(ll); ll, yy, xx = ll[order], yy[order], xx[order]
starts = np.searchsorted(ll, idx)
for r in range(1, n + 1):
    if cls_of[r] not in (LEAF, STEM, SEPAL): continue
    s, e = starts[r], starts[r + 1] if r < n else len(ll)
    if e - s < 5: continue
    X = np.stack([xx[s:e] - cx[r], yy[s:e] - cy[r]])
    w, v = np.linalg.eigh(X @ X.T)
    vx, vy = v[:, 1]
    meta['angle'][int(r)] = float(np.arctan2(vy, vx))

# flow field around the plant (for background strokes)
_bq = ~np.isin(clsmap, [WALL, TABLE])
_d = ndi.distance_transform_edt(~_bq)
_ds = ndi.gaussian_filter(_d, 9)
_gy, _gx = np.gradient(_ds)
_tan = np.arctan2(_gx, -_gy)
flow = np.stack([((_tan + np.pi) / (2 * np.pi) * 255).astype(np.uint8), np.clip(_d / 2, 0, 255).astype(np.uint8), np.zeros_like(clsmap)], -1)
Image.fromarray(flow).save(f'{out}/flow.png')

_, (iy, ix) = ndi.distance_transform_edt(lab == 0, return_indices=True)
near_cls = clsmap[iy, ix]
gapmask = (lab == 0)
clsmap[gapmask] = near_cls[gapmask]
bloommap[gapmask] = bloommap[iy, ix][gapmask]
linemap = np.where(line, near_cls, 255).astype(np.uint8)
near_bloom = bloommap[iy, ix]
cls_img = np.stack([clsmap, np.where(line, near_bloom, bloommap), (np.clip(puff, 0, 1) * 255).astype(np.uint8)], -1).astype(np.uint8)
Image.fromarray(cls_img).save(f'{out}/cls.png')
cid = lab.astype(np.uint32)
Image.fromarray(np.stack([cid & 255, (cid >> 8) & 255, (cid >> 16) & 255], -1).astype(np.uint8)).save(f'{out}/cid.png')
Image.fromarray(np.stack([linemap, (g.clip(0, 255)).astype(np.uint8), linemap], -1)).save(f'{out}/line.png')
json.dump(meta, open(f'{out}/meta.json', 'w'))
pal = np.array([[235, 235, 235], [120, 200, 230], [245, 245, 200], [40, 70, 160], [150, 90, 40], [60, 160, 70],
                [240, 140, 170], [250, 200, 40], [210, 60, 90], [120, 170, 80]], np.uint8)
dbg = pal[clsmap]; dbg[line] = 0
Image.fromarray(dbg).save(f'{out}/debug_classes.png')
print({k: int((clsmap == i).sum()) for i, k in enumerate(['wall', 'table', 'vaseW', 'vaseB', 'stem', 'leaf', 'petal', 'stamen', 'bud', 'sepal'])})
