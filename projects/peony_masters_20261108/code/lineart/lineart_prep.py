"""Segment the peony line art into labelled regions and export maps for the painter.

Outputs (in the given folder):
  cls.png   R = class id, G = bloom id (0 none, 1..), B = puff (0 at outline .. 255 region centre)
  cid.png   region id encoded in RGB (24 bit), 0 = line
  line.png  R = class of the nearest region for each line pixel (255 = not a line)
  meta.json per-region orientation + bloom centres
"""
import sys, json
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

src, out = sys.argv[1], sys.argv[2]
g = np.asarray(Image.open(src).convert('L')).astype(np.float32)
H, W = g.shape
line = g < 175
line_closed = ndi.binary_dilation(line, iterations=2)          # close tiny gaps before labelling
lab, n = ndi.label(~line_closed)
print('regions', n)

# ---- classes
WALL, TABLE, VASE_W, VASE_B, STEM, LEAF, PETAL, STAMEN, BUD, SEPAL = range(10)
TABLE_Y = 1290
BLOOMS = [  # (cx, cy, rx, ry, stamen centre, role)
    (648, 430, 232, 188, (690, 405), 'a'),    # top: pink
    (260, 505, 238, 262, (248, 560), 'b'),    # left: red
    (720, 780, 188, 168, (705, 735), 'c'),    # lower right: white
]
BUDS = [(490, 200, 48), (885, 550, 42), (140, 830, 44)]
LEAF_BOXES = [(255, 280, 470, 400)]
VASE = dict(x0=350, x1=720, y0=915, y1=1408, cx=535)

idx = np.arange(n + 1)
area = ndi.sum(np.ones_like(lab), lab, idx)
cy, cx = [np.array(v) for v in zip(*ndi.center_of_mass(np.ones_like(lab), lab, idx[1:]))]
cy = np.concatenate([[0], cy]); cx = np.concatenate([[0], cx])
# region "thickness": max distance to the outline
dist = ndi.distance_transform_edt(lab > 0)
thick = ndi.maximum(dist, lab, idx)

# background = big regions touching the border
border = set(np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))) - {0}

cls_of = np.zeros(n + 1, np.uint8); bloom_of = np.zeros(n + 1, np.uint8)
for r in range(1, n + 1):
    x, y, a = cx[r], cy[r], area[r]
    if r in border or a > 150000:
        cls_of[r] = WALL; continue
    # vase
    in_neck = 1010 > y > VASE['y0'] and 425 < x < 610
    if in_neck or (VASE['x0'] < x < VASE['x1'] and 1010 <= y < VASE['y1']):
        cls_of[r] = VASE_W if a > 2500 else VASE_B; continue
    # buds (lower part = sepals)
    hit = False
    for (bx, by, br) in BUDS:
        if (x - bx) ** 2 + (y - by) ** 2 < (br * 1.25) ** 2:
            cls_of[r] = SEPAL if (y > by + br * 0.25 or a < 120) else BUD; hit = True; break
    if hit: continue
    # leaves that sit inside a bloom's bounding ellipse
    if any(x0 < x < x1 and y0 < y < y1 for (x0, y0, x1, y1) in LEAF_BOXES):
        cls_of[r] = LEAF; continue
    # blooms
    for k, (bx, by, rx, ry, (sx, sy), role) in enumerate(BLOOMS):
        if ((x - bx) / rx) ** 2 + ((y - by) / ry) ** 2 < 1.0:
            if a < 160 and (x - sx) ** 2 + (y - sy) ** 2 < 80 ** 2: cls_of[r] = STAMEN
            else: cls_of[r] = PETAL
            bloom_of[r] = k + 1; hit = True; break
    if hit: continue
    # thin long regions = stems, the rest = leaves
    cls_of[r] = STEM if (thick[r] < 7 and a > 150) else LEAF

# background pockets enclosed by stems/leaves (no veins inside) -> wall
for (px_, py_) in [(516, 607), (430, 672), (425, 814), (542, 747)]:
    r_ = lab[py_, px_]
    if r_ > 0 and cls_of[r_] == LEAF: cls_of[r_] = WALL; bloom_of[r_] = 0
clsmap = cls_of[lab]
# pixel-level fix: where a leaf leaked into a petal region through a gap in the outline,
# petal pixels outside the bloom's ellipse are leaf
Y, X = np.mgrid[0:H, 0:W]
inside = np.zeros((H, W), bool)
for (bx, by, rx, ry, _, _) in BLOOMS:
    inside |= ((X - bx) / (rx * 1.04)) ** 2 + ((Y - by) / (ry * 1.04)) ** 2 < 1
clsmap[(clsmap == PETAL) & ~inside] = LEAF
# (the leaf box is applied per region above; no pixel-level rectangle, which cut petals square)
# decoration bands that leaked into the background through gaps: fill the vase silhouette row by row
vmask = ndi.binary_dilation(np.isin(clsmap, [VASE_W, VASE_B]), iterations=4)
for yy_ in range(VASE['y0'], min(H, VASE['y1'])):
    xs = np.nonzero(vmask[yy_, VASE['x0']:VASE['x1']])[0]
    if len(xs) < 2: continue
    x0_, x1_ = VASE['x0'] + xs[0], VASE['x0'] + xs[-1]
    rowc = clsmap[yy_, x0_:x1_]
    rowc[rowc == WALL] = VASE_W
for yy_ in range(925, 1050):                                       # neck bands: fill between the neck's outlines
    xs = np.nonzero(line[yy_, 430:640])[0] + 430
    if len(xs) < 2: continue
    rowc = clsmap[yy_, xs[0]:xs[-1]]; rowc[rowc == WALL] = VASE_W
clsmap[(clsmap == WALL) & (np.arange(H)[:, None] > TABLE_Y)] = TABLE
bloommap = bloom_of[lab]

# puff: distance to outline normalised per region (0 at the line, 1 at the region's centre)
puff = np.where(lab > 0, dist / np.maximum(thick[lab], 1), 0)
puff[clsmap <= TABLE] = 1.0

# per-region orientation (principal axis) for leaves / stems
meta = {'W': W, 'H': H, 'blooms': [[b[0], b[1], b[2], b[3], b[5]] for b in BLOOMS], 'vase': VASE, 'table_y': TABLE_Y, 'angle': {}}
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

# ---- stems: thin elongated channels between two close parallel lines (lost by the gap closing)
lab0, n0 = ndi.label(~line)
d0 = ndi.distance_transform_edt(lab0 > 0)
idx0 = np.arange(n0 + 1)
th0 = ndi.maximum(d0, lab0, idx0); ar0 = ndi.sum(np.ones_like(lab0), lab0, idx0)
sl = ndi.find_objects(lab0)
# every thin channel (<= ~11 px wide) outside blooms and buds is a stem
thin = np.isin(lab0, np.nonzero((th0 <= 5.5) & (ar0 >= 25))[0])
Yg, Xg = np.mgrid[0:H, 0:W]
excl = np.zeros((H, W), bool)
for (bx, by, rx, ry, _, _) in BLOOMS: excl |= ((Xg - bx) / rx) ** 2 + ((Yg - by) / ry) ** 2 < 1.12
for (bx, by, br) in BUDS: excl |= (Xg - bx) ** 2 + (Yg - by) ** 2 < (br * 1.35) ** 2
excl |= Yg > 960
_, (iy0, ix0) = ndi.distance_transform_edt(lab == 0, return_indices=True)
nearc = clsmap[iy0, ix0]
sl = ndi.find_objects(lab0); longc = []
for r in np.nonzero((th0 <= 5.5) & (ar0 >= 40))[0]:
    o = sl[r - 1]
    if o is None: continue
    L_ = max(o[0].stop - o[0].start, o[1].stop - o[1].start)
    if L_ >= 45 and ar0[r] / L_ < 9 and 120 < (o[0].start + o[0].stop) / 2 < 960: longc.append(r)
longm = np.isin(lab0, longc)
stem_mask = thin & (~excl | longm) & ~(Yg > 960) & np.isin(clsmap, [WALL, LEAF, STEM]) & ~np.isin(nearc, [PETAL, BUD, SEPAL, STAMEN, VASE_W, VASE_B])
stem_ids = [0]
clsmap[stem_mask] = STEM
# stems entering the large blooms (inside their ellipses): thin channels in these boxes are stem too
for (x0_, y0_, x1_, y1_, wmax) in [(490, 520, 590, 650, 5.5), (335, 640, 455, 720, 8.0)]:
    loc = ndi.maximum_filter(d0[y0_:y1_, x0_:x1_], size=11) <= wmax     # locally narrow, even if the channel opens into a petal
    sub = (thin[y0_:y1_, x0_:x1_] | (loc & (d0[y0_:y1_, x0_:x1_] > 0))) & np.isin(clsmap[y0_:y1_, x0_:x1_], [PETAL, LEAF, STEM])
    clsmap[y0_:y1_, x0_:x1_][sub] = STEM
    stem_mask[y0_:y1_, x0_:x1_] |= sub
print('stem pixels', int(stem_mask.sum()), 'stem channels', len(stem_ids))
# flow field for the background: distance to the bouquet + tangent direction around it
_bq = ~np.isin(clsmap, [WALL, TABLE])
_d = ndi.distance_transform_edt(~_bq)
_ds = ndi.gaussian_filter(_d, 9)
_gy, _gx = np.gradient(_ds)
_tan = np.arctan2(_gx, -_gy)               # perpendicular to the gradient: circulates around the bouquet
flow = np.stack([((_tan + np.pi) / (2 * np.pi) * 255).astype(np.uint8), np.clip(_d / 2, 0, 255).astype(np.uint8), np.zeros_like(clsmap)], -1)
Image.fromarray(flow).save(f'{out}/flow.png')
# nearest region class for each line pixel (to colour the lines)
_, (iy, ix) = ndi.distance_transform_edt(lab == 0, return_indices=True)
near_cls = clsmap[iy, ix]
# pixels swallowed by the gap-closing dilation (soft line edges) take their nearest region's class and bloom
gapmask = (lab == 0) & ~stem_mask
clsmap[gapmask] = near_cls[gapmask]
bloommap[gapmask] = bloommap[iy, ix][gapmask]
# on the vase, soft gaps between the dense decoration lines stay white porcelain
vase_any = np.isin(clsmap, [VASE_W, VASE_B])
clsmap[gapmask & ~line & vase_any] = VASE_W
linemap = np.where(line, near_cls, 255).astype(np.uint8)
near_bloom = bloommap[iy, ix]

cls_img = np.stack([clsmap, np.where(line, near_bloom, bloommap), (np.clip(puff, 0, 1) * 255).astype(np.uint8)], -1).astype(np.uint8)
Image.fromarray(cls_img).save(f'{out}/cls.png')
cid = lab.astype(np.uint32)
Image.fromarray(np.stack([cid & 255, (cid >> 8) & 255, (cid >> 16) & 255], -1).astype(np.uint8)).save(f'{out}/cid.png')
Image.fromarray(np.stack([linemap, (g.clip(0, 255)).astype(np.uint8), linemap], -1)).save(f'{out}/line.png')
json.dump(meta, open(f'{out}/meta.json', 'w'))

# debug preview of the classification
pal = np.array([[230, 200, 120], [190, 110, 50], [245, 245, 240], [40, 70, 160], [80, 140, 60], [60, 150, 70],
                [240, 140, 170], [250, 200, 40], [210, 60, 90], [120, 170, 80]], np.uint8)
dbg = pal[clsmap]; dbg[line] = 0
Image.fromarray(dbg).save(f'{out}/debug_classes.png')
print({k: int((clsmap == i).sum()) for i, k in enumerate(['wall', 'table', 'vaseW', 'vaseB', 'stem', 'leaf', 'petal', 'stamen', 'bud', 'sepal'])})
