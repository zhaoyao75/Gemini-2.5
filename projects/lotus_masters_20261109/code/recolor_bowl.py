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
 'dali':         ('#7a1018', '#d8404a', '#c8982c', '#f8e090'),   # deep red bowl, gold vine
}
if style not in PAL: sys.exit(0)
bd, bl, od, ol = [H(c) for c in PAL[style]]
im = np.asarray(Image.open(path).convert('RGB')).astype(np.float32)
cls = np.asarray(Image.open(f'{d}/cls.png'))[:, :, 0]
orn = ndi.binary_dilation(np.asarray(Image.open(f'{d}/orn_mask.png')) > 0, iterations=1)
bowl = np.isin(cls, [2, 3])
r, g, b = im[..., 0], im[..., 1], im[..., 2]
blue = (b > r + 18) & (b > g + 4)
L = 0.3 * r + 0.59 * g + 0.11 * b
t = np.clip((L - 45) / 100, 0, 1)[..., None]
body = bowl & blue & ~orn; ornm = bowl & blue & orn
out = im.copy()
out[body] = (bd + (bl - bd) * t)[body]
out[ornm] = (od + (ol - od) * t)[ornm]
Image.fromarray(out.clip(0, 255).astype(np.uint8)).save(path)
