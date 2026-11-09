"""Give every painting its own bowl colours (the line art's bowl was painted blue by every style).
Body = lotus-petal relief region, ornament = vine leaves / dots / pearls (orn_mask.png). Only bluish pixels are remapped,
by luminance, so brush texture, highlights and ink lines survive.
usage: recolor_bowl.py lineart_dir painting.png style"""
import sys, numpy as np
from PIL import Image
from scipy import ndimage as ndi
d, path, style = sys.argv[1:4]
H = lambda h: np.array([int(h[i:i + 2], 16) for i in (1, 3, 5)], np.float32)
# style: (body dark, body light, ornament dark, ornament light)
PAL = {
 'monet':        ('#2f8a80', '#9adccb', '#b8487a', '#f4b8d0'),   # celadon bowl, pink vine
 'klimt':        ('#7a0c20', '#d83a4a', '#b88418', '#f8dc70'),   # crimson bowl, gold vine
 'matisse':      ('#e0a800', '#fff070', '#1c3aa8', '#5a7af0'),   # yellow bowl, blue vine
 'hockney':      ('#d81878', '#ff8ac0', '#ffffff', '#ffffff'),   # hot pink bowl, white vine
 'vangogh':      ('#0e6a62', '#4acab0', '#e8b010', '#fff060'),   # teal bowl, yellow vine
 'lichtenstein': ('#c0101c', '#ff4a50', '#ffe040', '#fff6a0'),   # red bowl, yellow vine
 'seurat':       ('#d8560e', '#fcae58', '#2a48a8', '#78a0e8'),   # orange bowl, blue vine
 'gauguin':      ('#0a9a94', '#5ae8d8', '#ffd020', '#fff090'),   # turquoise bowl, yellow vine
 'picasso':      ('#a8402c', '#e89070', '#f0e4c8', '#fffaf0'),   # terracotta bowl, cream vine
 'munch':        ('#14705a', '#4ac8a0', '#f4c020', '#fff090'),
 'schiele':      ('#7a4428', '#d8a070', '#26466a', '#6a96c0'),
 'magritte':     ('#8a1018', '#e0505a', '#ffffff', '#ffffff'),
 'dali':         ('#7a1018', '#d8404a', '#c8982c', '#f8e090'),   # deep red bowl, gold vine
}
if style not in PAL: sys.exit(0)
bd, bl, od, ol = [H(c) for c in PAL[style]]
im = np.asarray(Image.open(path).convert('RGB')).astype(np.float32)
cls = np.asarray(Image.open(f'{d}/cls.png'))[:, :, 0]
orn = ndi.binary_dilation(np.asarray(Image.open(f'{d}/orn_mask.png')) > 0, iterations=1)
bowl = np.isin(cls, [2, 3])
# petals of the relief: close the gaps at their feet with a thick line dilation, label, take the three big petals by seed point
base = np.asarray(Image.open(f'{d}/base.png').convert('L')).astype(np.float32)
ink = ndi.binary_dilation(base < 190, iterations=5)
plab, _ = ndi.label(~ink)
PETAL_SEEDS = [(528, 1255), (352, 1262), (690, 1250)]
pet_ids = [plab[y, x] for (x, y) in PETAL_SEEDS if plab[y, x] > 0]
pet_mask = np.isin(plab, pet_ids)
pd = ndi.distance_transform_edt(pet_mask)
puff = np.zeros(pet_mask.shape, np.float32)
for pid in pet_ids:
    m = plab == pid; puff[m] = pd[m] / max(pd[m].max(), 1)
dist_out, (ny, nx) = ndi.distance_transform_edt(~pet_mask, return_indices=True)
near_pet = dist_out < 6                                           # include the ink line pixels around each petal
puff = puff[ny, nx] * near_pet
pet_mask_full = near_pet
is_outer = ~pet_mask_full
r, g, b = im[..., 0], im[..., 1], im[..., 2]
blue = (b > r + 18) & (b > g + 4)
L = 0.3 * r + 0.59 * g + 0.11 * b
t = np.clip((L - 45) / 100, 0, 1)[..., None]
Hh, Ww = plab.shape; X = np.arange(Ww)[None, :].repeat(Hh, 0).astype(np.float32); Y = np.arange(Hh)[:, None].repeat(Ww, 1).astype(np.float32)
cyl = (1 - 0.45 * np.clip(((X - 528) / 285) ** 2, 0, 1))[..., None]        # round-body shading: lit centre, dark sides
lit = np.clip(1 - (X - 380) / 420, 0, 1)[..., None] * 0.18                  # light from the left
body = bowl & blue & ~orn; ornm = bowl & blue & orn
# the line pixels belong to their nearest region's class; give them the surface tone of the outer area
pet = body & ~is_outer
out = im.copy()
outer_col = (bd * 0.85)[None, None, :] * (0.6 + 0.4 * cyl) + (bl - bd)[None, None, :] * (0.10 + lit) * cyl + (t - 0.5) * 22
pu = np.clip(puff, 0, 1)[..., None] ** 0.6
pet_col = (bd + (bl - bd) * (0.30 + 0.65 * pu))[None, None, :] if False else (bd[None, None, :] + (bl - bd)[None, None, :] * (0.30 + 0.62 * pu + lit)) * (0.78 + 0.22 * cyl) + (t - 0.5) * 26
out[body & is_outer] = outer_col[body & is_outer]
out[pet] = pet_col[pet]
out[ornm] = (od + (ol - od) * t)[ornm]
Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(path)
