"""Add a blue-and-white style ornament to the bowl of the lotus line art.
The original bowl is a smooth round bowl with only a ring of lotus-petal relief, so we add
  * a scrolling vine (leaves + dots) on the shoulder band under the rim
  * a row of pearls on the foot ring
Outputs base_orn.png (line art with the ornament drawn as ink) and orn_mask.png (255 inside leaves/pearls,
used by lotus_prep.py to class those regions as the bowl's accent colour, VASE_B).
usage: lotus_bowl_ornament.py base.png base_orn.png orn_mask.png"""
import sys, math
from PIL import Image, ImageDraw
src, out, outm = sys.argv[1:4]
im = Image.open(src).convert('L'); W, H = im.size
mask = Image.new('L', (W, H), 0)
d, dm = ImageDraw.Draw(im), ImageDraw.Draw(mask)
INK = 45

def shoulder_y(x):               # centre line of the shoulder band (original pixel coords)
    return 1060 + (188 + 40 * ((x - 530) / 260) ** 2 * 0.55) / 2 + 2

def leaf(cx, cy, ang, L=24, Wd=12):
    pts = []
    for t in range(0, 41):
        a = t / 40 * 2 * math.pi
        # pointed leaf outline: lemon shape
        u = math.cos(a) * L / 2; v = math.sin(a) * Wd / 2 * (1 - 0.25 * math.cos(a) ** 2)
        pts.append((cx + u * math.cos(ang) - v * math.sin(ang), cy + u * math.sin(ang) + v * math.cos(ang)))
    d.polygon(pts, fill=255, outline=INK); d.line(pts + [pts[0]], fill=INK, width=2)
    dm.polygon(pts, fill=255)

def dot(cx, cy, r=5):
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255, outline=INK, width=2); dm.ellipse((cx - r, cy - r, cx + r, cy + r), fill=255)

# --- the shoulder band's lower edge (faint in the original, so it did not close the band): draw it as ink
low = [(x, shoulder_y(x) + 15) for x in range(262, 799, 2)]
d.line(low, fill=INK, width=2)
# --- scrolling vine on the shoulder
x0, x1, step = 312, 790, 2
pts = []
for x in range(x0, x1 + 1, step):
    pts.append((x, shoulder_y(x) + 6 * math.sin((x - x0) / 48 * 2 * math.pi)))
d.line(pts, fill=INK, width=3)
n = 0
for x in range(x0 + 14, x1 - 14, 48):
    y = shoulder_y(x) + 6 * math.sin((x - x0) / 48 * 2 * math.pi)
    up = (n % 2 == 0)
    leaf(x + 8, y + (-10 if up else 10), (-0.7 if up else 0.7), 34, 17)
    dot(x + 31, y + (8 if up else -8), 6)
    n += 1
# --- pearls on the foot ring
for x in range(386, 676, 22):
    yy = 1342 + 1.6 * ((x - 530) / 138) ** 2
    dot(x, yy, 7)
im.save(out); mask.save(outm)
