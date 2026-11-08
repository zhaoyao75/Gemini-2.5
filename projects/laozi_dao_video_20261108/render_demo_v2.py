"""《问道》shot 1 demo, vertical SD (540x960, 5s).

Youth walks in at the foot of an ink mountain, looks up and asks "道在哪里？";
camera tilts up the mountain to an old man on an ox under the moon.
Drawn at 1080x1920 and downscaled. Usage: python3 render_demo_v2.py
"""
import math, os, subprocess, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920            # internal canvas
OW, OH = 540, 960            # output (SD)
WH = 3000                    # world height
FPS, DUR = 30, 5.0
N = int(FPS * DUR)
FRAMES = os.path.join(HERE, "frames_v2")
os.makedirs(FRAMES, exist_ok=True)
CAL = os.path.join(HERE, "fonts", "MaShanZheng-Regular.ttf")
SERIF = os.path.join(HERE, "fonts", "NotoSerifSC-Light.otf")

IVORY = (237, 230, 214)
GOLD = (210, 175, 105)
RED = (184, 53, 42)
rng = np.random.default_rng(3)


def ease(x):
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def blur(a, r):
    return np.asarray(Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), np.float32) / 255


def noise2d(h, w, scales=(6, 20, 70), weights=(0.3, 0.4, 0.3)):
    acc = np.zeros((h, w), np.float32)
    for s, wt in zip(scales, weights):
        small = rng.random((h // s + 3, w // s + 3)).astype(np.float32)
        big = np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize(((w // s + 3) * s, (h // s + 3) * s), Image.BICUBIC), np.float32)[:h, :w] / 255
        acc += wt * big
    return acc


def noise1d(n, scale, amp):
    pts = rng.normal(0, 1, n // scale + 3)
    xs = np.arange(n) / scale
    i = xs.astype(int)
    f = xs - i
    f = f * f * (3 - 2 * f)
    return (pts[i] * (1 - f) + pts[i + 1] * f) * amp


# ---------------- world: ink mountains (grey, inverted ink on black) ----------------
print("building world…")
xs = np.arange(W, dtype=np.float32)
yy = np.arange(WH, dtype=np.float32)[:, None]
tex = noise2d(WH, W)


def mountain_layer(ridge, tone, edge_glow, tex_amt):
    below = yy - ridge[None, :]
    body = (below > 0).astype(np.float32)
    body = blur(body, 3)
    depth = np.clip(below / 900, 0, 1)
    shade = tone * (1 - 0.75 * depth) * (1 - tex_amt + tex_amt * tex)
    edge = np.exp(-np.clip(below, 0, None) / 14) * body * edge_glow
    return body, shade + edge


SUMMIT_X, SUMMIT_Y = 640, 830
GROUND_Y_ = 2560
far_ridge = 1500 + noise1d(W, 90, 120) + noise1d(W, 25, 25) - 380 * np.exp(-((xs - 250) / 260) ** 2)
far_a, far_v = mountain_layer(far_ridge, 0.22, 0.10, 0.5)
main_ridge = SUMMIT_Y + 1.15 * np.clip(np.abs(xs - SUMMIT_X) - 70, 0, None) ** 1.12 + noise1d(W, 60, 40) + noise1d(W, 14, 9)
main_ridge = np.minimum(main_ridge, 2700)
main_ridge = np.where(np.abs(xs - SUMMIT_X) < 110, SUMMIT_Y + np.abs(xs - SUMMIT_X) * 0.05, main_ridge)  # plateau for the ox
main_a, main_v = mountain_layer(main_ridge, 0.34, 0.30, 0.6)
# cun (texture) strokes on main mountain
strokes = Image.new("L", (W, WH), 0)
sd = ImageDraw.Draw(strokes)
for _ in range(80):
    x = rng.uniform(80, W - 80)
    y0 = main_ridge[int(x)] + rng.uniform(20, 380)
    if y0 > 2550:
        continue
    side = 1 if x > SUMMIT_X else -1
    for j in range(3):  # small clusters of slanted hemp-fibre strokes
        L = rng.uniform(25, 70)
        ang = math.radians(90 + side * rng.uniform(25, 45))
        xx0 = x + j * 9
        sd.line([(xx0, y0), (xx0 + L * math.cos(ang), y0 + L * math.sin(ang))], fill=int(rng.uniform(18, 40)), width=int(rng.uniform(3, 6)))
# winding path up the mountain (dotted)
path_pts = []
for k in range(60):
    u = k / 59
    py = GROUND_Y_ - u * (GROUND_Y_ - SUMMIT_Y - 10)
    px = SUMMIT_X + (1 - u) * 260 * math.sin(u * 9) - (1 - u) * 120
    path_pts.append((px, py))
for k in range(0, 59, 2):
    sd.line([path_pts[k], path_pts[k + 1]], fill=120, width=4)
strokes = blur(np.asarray(strokes, np.float32) / 255, 1.2) * blur(main_a, 2)
GROUND_Y = 2560
ground = np.clip((yy - GROUND_Y) / 6, 0, 1) * np.ones((1, W), np.float32)
ground_v = ground * (0.16 + 0.10 * tex) + np.exp(-np.abs(yy - GROUND_Y) / 4) * 0.35 * np.ones((1, W))

near = main_v * main_a + strokes * 0.9
near = near * (1 - ground) + ground_v
far_world = far_v * far_a
mist_tex = blur(noise2d(700, W * 2, (40, 120), (0.5, 0.5)), 10)

# moon glow (world space)
MOON = (585, 470, 120)
my, mx = np.mgrid[0:WH, 0:W].astype(np.float32)
md = np.hypot(mx - MOON[0], my - MOON[1])
moon_disc = np.clip((MOON[2] - md) / 2.5, 0, 1)
moon_glow = np.exp(-(np.clip(md - MOON[2], 0, None) / 160) ** 1.3) * 0.45
moon_world = np.clip(moon_disc * 0.95 + moon_glow * (1 - moon_disc), 0, 1)
del my, mx, md

# ---------------- overlays (screen space, static) ----------------
vign = np.clip(1.2 - (np.hypot((np.arange(W)[None, :] - W / 2) / W, (np.arange(H)[:, None] - H / 2) / H) * 1.45) ** 2, 0, 1).astype(np.float32)


def font(path, size):
    return ImageFont.truetype(path, size)


F_TITLE, F_SUB, F_SMALL, F_BUBBLE, F_TAG = font(CAL, 150), font(SERIF, 48), font(SERIF, 34), font(CAL, 64), font(SERIF, 34)


def seal(size, ch):
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, size - 1, size - 1], radius=8, fill=RED + (235,))
    d.text((size / 2, size / 2 + 2), ch, font=font(CAL, int(size * 0.72)), fill=(30, 10, 8, 255), anchor="mm")
    a = np.asarray(im).copy()
    rough = rng.random(a.shape[:2]) < 0.06  # worn stone texture
    a[rough, 3] = 0
    return Image.fromarray(a)


SEAL = seal(92, "道")


def draw_header(img, t):
    a = ease(t / 0.6)
    d = ImageDraw.Draw(img)
    # vertical title
    for i, ch in enumerate("问道"):
        d.text((150, 260 + i * 165), ch, font=F_TITLE, fill=IVORY + (int(255 * a),), anchor="mm")
    img.alpha_composite(Image.fromarray((np.asarray(SEAL).astype(np.float32) * [1, 1, 1, a]).astype(np.uint8)), (104, 520))
    d.text((150, 640), "第\n一\n回", font=F_SMALL, fill=(170, 165, 150, int(220 * a)), anchor="ma", spacing=6)
    # series tag top-right
    d.text((W - 70, 120), "老子的故事  01", font=F_TAG, fill=(200, 192, 175, int(230 * a)), anchor="ra")
    d.line([(W - 70 - 300 * a, 170), (W - 70, 170)], fill=GOLD + (int(200 * a),), width=2)


SUBS = [(0.2, 2.35, "少年听说，世上有一样东西，", "叫“道”。"), (2.5, 5.2, "他要去山顶，", "问一个人。")]


def draw_footer(img, t):
    d = ImageDraw.Draw(img)
    panel = Image.new("RGBA", (W, 330), (0, 0, 0, 0))
    pa = np.zeros((330, W, 4), np.uint8)
    pa[..., 3] = (np.linspace(0, 1, 330)[:, None] ** 0.7 * 200).astype(np.uint8)
    img.alpha_composite(Image.fromarray(pa), (0, H - 330))
    for t0, t1, l1, l2 in SUBS:
        a = min(ease((t - t0) / 0.35), ease((t1 - t) / 0.3))
        if a <= 0:
            continue
        dy = (1 - a) * 18
        d.text((W / 2, H - 250 + dy), l1, font=F_SUB, fill=IVORY + (int(255 * a),), anchor="mm")
        d.text((W / 2, H - 185 + dy), l2, font=F_SUB, fill=IVORY + (int(255 * a),), anchor="mm")
    # progress dots: 12 shots, shot 1 fills over time
    x0 = W / 2 - 11 * 26 / 2
    for k in range(12):
        x = x0 + k * 26
        if k == 0:
            d.ellipse([x - 7, H - 95, x + 7, H - 81], fill=GOLD + (255,))
        else:
            d.ellipse([x - 5, H - 93, x + 5, H - 83], outline=(120, 115, 105, 255), width=2)
    d.text((W - 70, H - 88), "柔弱胜刚强 ›", font=F_SMALL, fill=(120, 115, 105, 200), anchor="rm")
    d.text((70, H - 88), "00:0%d" % int(t), font=F_SMALL, fill=(120, 115, 105, 200), anchor="lm")


# ---------------- characters ----------------
def brush_line(d, p, q, w0, w1, fill):
    """Tapered stroke from p (width w0) to q (width w1)."""
    (x0, y0), (x1, y1) = p, q
    dx, dy = x1 - x0, y1 - y0
    L = math.hypot(dx, dy) or 1
    nx, ny = -dy / L, dx / L
    d.polygon([(x0 + nx * w0 / 2, y0 + ny * w0 / 2), (x1 + nx * w1 / 2, y1 + ny * w1 / 2),
               (x1 - nx * w1 / 2, y1 - ny * w1 / 2), (x0 - nx * w0 / 2, y0 - ny * w0 / 2)], fill=fill)
    d.ellipse([x1 - w1 / 2, y1 - w1 / 2, x1 + w1 / 2, y1 + w1 / 2], fill=fill)
    d.ellipse([x0 - w0 / 2, y0 - w0 / 2, x0 + w0 / 2, y0 + w0 / 2], fill=fill)


def limb(origin, a1, l1, a2, l2):
    x, y = origin
    k = (x + l1 * math.sin(a1), y + l1 * math.cos(a1))
    e = (k[0] + l2 * math.sin(a2), k[1] + l2 * math.cos(a2))
    return k, e


def draw_youth(d, ink, x, y, s, phase, walking, look_up, shade_eyes, t):
    """Stick-figure youth. (x, y) = feet on ground, s = height in px."""
    bob = abs(math.sin(phase)) * 0.015 * s if walking else 0
    hip = (x, y - 0.47 * s - bob)
    sho = (x + 0.03 * s, y - 0.79 * s - bob)
    tilt = -0.35 * look_up
    head = (sho[0] + 0.02 * s + 0.05 * s * look_up * 0, sho[1] - 0.12 * s)
    lw = 0.04 * s
    sw = math.sin(phase) * 0.5 if walking else 0.0
    # robe (ink wash, short)
    flut = math.sin(t * 6) * 0.02 * s
    ink.polygon([(sho[0] - 0.07 * s, sho[1] + 0.02 * s), (sho[0] + 0.08 * s, sho[1] + 0.02 * s),
                 (hip[0] + 0.15 * s + flut, hip[1] + 0.12 * s), (hip[0] - 0.13 * s + flut, hip[1] + 0.13 * s)], fill=150)
    # bundle on back
    bx, by = sho[0] - 0.12 * s, sho[1] + 0.06 * s
    ink.ellipse([bx - 0.09 * s, by - 0.08 * s, bx + 0.09 * s, by + 0.09 * s], fill=190)
    d.line([sho, (bx + 0.02 * s, by - 0.05 * s)], fill=IVORY + (200,), width=int(0.015 * s))
    # legs
    for sgn, al in ((1, 255), (-1, 170)):
        a_th = sw * sgn
        a_sh = a_th - (0.45 * max(0, -math.sin(phase * 1 + (0 if sgn > 0 else math.pi))) if walking else 0)
        k, f = limb(hip, a_th, 0.25 * s, a_sh, 0.23 * s)
        brush_line(d, hip, k, lw, lw * 0.9, IVORY + (al,))
        brush_line(d, k, f, lw * 0.9, lw * 0.6, IVORY + (al,))
        brush_line(d, f, (f[0] + 0.06 * s, f[1]), lw * 0.6, lw * 0.4, IVORY + (al,))
    # spine
    brush_line(d, hip, sho, lw * 1.1, lw, IVORY + (255,))
    # arms
    if shade_eyes > 0:
        a_up = -2.4 * shade_eyes + (-sw) * (1 - shade_eyes)
        a_fo = -3.6 * shade_eyes + (-sw + 0.4) * (1 - shade_eyes)
    else:
        a_up, a_fo = -sw, -sw + 0.4
    k, h = limb(sho, a_up, 0.18 * s, a_fo, 0.16 * s)
    brush_line(d, sho, k, lw * 0.9, lw * 0.7, IVORY + (255,))
    brush_line(d, k, h, lw * 0.7, lw * 0.45, IVORY + (255,))
    k, h = limb(sho, sw, 0.18 * s, sw + 0.3, 0.16 * s)
    brush_line(d, sho, k, lw * 0.9, lw * 0.7, IVORY + (170,))
    brush_line(d, k, h, lw * 0.7, lw * 0.45, IVORY + (170,))
    # head + topknot, tilted up when looking
    hx, hy = head[0] + 0.02 * s * look_up, head[1] - 0.01 * s * look_up
    r = 0.075 * s
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=IVORY + (255,))
    kx, ky = hx - r * math.sin(tilt + 0.4) * 1.1, hy - r * math.cos(tilt + 0.4) * 1.1
    d.ellipse([kx - r * 0.42, ky - r * 0.42, kx + r * 0.42, ky + r * 0.42], fill=IVORY + (255,))
    # eye dot facing direction / up
    ex, ey = hx + r * 0.45, hy - r * (0.05 + 0.4 * look_up)
    d.ellipse([ex - 4, ey - 4, ex + 4, ey + 4], fill=(10, 10, 10, 255))
    return (hx, hy - r)


def draw_sage_on_ox(d, ink, x, y, s, t):
    """Old man riding an ox. (x, y) = ox hooves baseline; s = scale (ox length)."""
    y0 = y
    y = y + 0.1 * s
    # ox body (ink wash)
    ink.ellipse([x - 0.5 * s, y - 0.62 * s, x + 0.42 * s, y - 0.25 * s], fill=200)
    ink.ellipse([x + 0.3 * s, y - 0.6 * s, x + 0.62 * s, y - 0.36 * s], fill=215)  # head
    d.arc([x - 0.5 * s, y - 0.62 * s, x + 0.42 * s, y - 0.25 * s], 190, 350, fill=IVORY + (150,), width=4)
    d.arc([x + 0.3 * s, y - 0.6 * s, x + 0.62 * s, y - 0.36 * s], 200, 40, fill=IVORY + (150,), width=4)
    ink.polygon([(x - 0.45 * s, y - 0.5 * s), (x - 0.62 * s, y - 0.28 * s + math.sin(t * 3) * 0.03 * s), (x - 0.58 * s, y - 0.27 * s)], fill=170)  # tail
    for lx in (-0.38, -0.25, 0.18, 0.3):
        brush_line(d, (x + lx * s, y - 0.32 * s), (x + (lx + 0.01) * s + math.sin(t * 2 + lx * 9) * 3, y0), 0.065 * s, 0.045 * s, (165, 160, 150, 255))
    # horns
    hx, hy = x + 0.47 * s, y - 0.58 * s
    d.arc([hx - 0.1 * s, hy - 0.16 * s, hx + 0.06 * s, hy], 180, 300, fill=IVORY + (255,), width=int(0.035 * s))
    d.arc([hx - 0.02 * s, hy - 0.17 * s, hx + 0.14 * s, hy - 0.01 * s], 220, 350, fill=IVORY + (255,), width=int(0.035 * s))
    blink = 1 if (t % 1.7) > 0.12 else 0.2
    d.ellipse([x + 0.52 * s - 6, y - 0.52 * s - 6 * blink, x + 0.52 * s + 6, y - 0.52 * s + 6 * blink], fill=IVORY + (220,))
    # sage seated
    hip = (x - 0.05 * s, y - 0.64 * s)
    sho = (x - 0.08 * s, y - 0.98 * s)
    lw = 0.035 * s
    flut = math.sin(t * 2.2) * 0.04 * s
    ink.polygon([(sho[0] - 0.12 * s, sho[1]), (sho[0] + 0.1 * s, sho[1]), (hip[0] + 0.22 * s, hip[1] + 0.2 * s),
                 (hip[0] - 0.3 * s - flut, hip[1] + 0.1 * s), (hip[0] - 0.4 * s - flut * 2, hip[1] - 0.05 * s)], fill=235)  # robe + flowing sleeve
    brush_line(d, hip, sho, lw * 1.1, lw, IVORY + (255,))
    k, f = limb(hip, 1.2, 0.17 * s, 0.1, 0.2 * s)
    brush_line(d, hip, k, lw, lw * 0.8, IVORY + (255,))
    brush_line(d, k, f, lw * 0.8, lw * 0.5, IVORY + (255,))
    # arm holding staff
    k, hnd = limb(sho, 0.9, 0.15 * s, 0.1, 0.14 * s)
    brush_line(d, sho, k, lw * 0.9, lw * 0.7, IVORY + (255,))
    brush_line(d, k, hnd, lw * 0.7, lw * 0.5, IVORY + (255,))
    brush_line(d, (hnd[0] + 0.03 * s, hnd[1] - 0.35 * s), (hnd[0] - 0.02 * s, hnd[1] + 0.45 * s), 0.018 * s, 0.022 * s, GOLD + (230,))
    # head, topknot, long beard
    r = 0.065 * s
    hx, hy = sho[0] + 0.02 * s, sho[1] - 0.1 * s
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=IVORY + (255,))
    d.ellipse([hx - r * 0.4, hy - r * 1.55, hx + r * 0.4, hy - r * 0.8], fill=IVORY + (255,))
    d.line([(hx - r * 0.9, hy - r * 1.2), (hx + r * 0.9, hy - r * 1.2)], fill=GOLD + (255,), width=4)  # hairpin
    for k2 in range(5):
        bx = hx + (k2 - 2) * 0.012 * s + r * 0.3
        sway = math.sin(t * 2 + k2) * 0.02 * s
        d.line([(bx, hy + r * 0.6), (bx + sway, hy + r * 0.6 + 0.16 * s + k2 % 2 * 0.03 * s)], fill=IVORY + (210,), width=3)
    d.ellipse([hx + r * 0.35 - 3, hy - r * 0.2 - 3, hx + r * 0.35 + 3, hy - r * 0.2 + 3], fill=(10, 10, 10, 255))
    return (hx, hy - r * 1.6)


def bubble(img, x, y, text, t0, t):
    """Ink speech bubble with typewriter text, anchored by tail at (x, y)."""
    if t < t0:
        return
    a = ease((t - t0) / 0.25)
    n = int(min(len(text), (t - t0) / 0.09 + 1))
    lay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(lay)
    bx, by, bw, bh = x + 30, y - 230, 430, 140
    d.rounded_rectangle([bx, by, bx + bw, by + bh], radius=60, fill=(18, 18, 18, int(230 * a)), outline=IVORY + (int(230 * a),), width=4)
    d.polygon([(bx + 70, by + bh - 4), (bx + 120, by + bh - 4), (x + 8, y - 10)], fill=(18, 18, 18, int(230 * a)))
    d.line([(bx + 70, by + bh - 1), (x + 8, y - 10), (bx + 120, by + bh - 1)], fill=IVORY + (int(230 * a),), width=4)
    d.text((bx + bw / 2, by + bh / 2), text[:n], font=F_BUBBLE, fill=IVORY + (int(255 * a),), anchor="mm")
    img.alpha_composite(lay)


def tag(d, x, y, tx, ty, text, a):
    if a <= 0:
        return
    d.line([(x, y), (tx, ty)], fill=GOLD + (int(200 * a),), width=2)
    d.ellipse([x - 5, y - 5, x + 5, y + 5], fill=GOLD + (int(255 * a),))
    d.text((tx + (8 if tx > x else -8), ty), text, font=F_SMALL, fill=GOLD + (int(255 * a),), anchor="lm" if tx > x else "rm")


# ---------------- timeline ----------------
def cam_y(t):  # world y at top of screen
    bottom, top = WH - H, 0
    return bottom + (top - bottom) * ease((t - 2.35) / 2.0) ** 1.0


birds = [(rng.uniform(-200, 0), rng.uniform(1300, 1700), rng.uniform(260, 380), rng.uniform(0, 6)) for _ in range(4)]
specks_x, specks_y, specks_v = rng.uniform(0, W, 90), rng.uniform(0, H, 90), rng.uniform(20, 70, 90)

ONLY = {int(v) for v in os.environ.get("ONLY", "").split(",") if v}
for i in range(N):
    if ONLY and i not in ONLY:
        continue
    t = i / FPS
    cy = cam_y(t)
    c0 = int(round(cy))
    fy = int(round(cy * 0.55 + (WH - H) * 0.45))  # far layer parallax
    reveal = ease(t / 0.7)
    sky = np.zeros((H, W), np.float32)
    g = far_world[fy:fy + H] * 0.9 + sky
    moon = moon_world[c0:c0 + H]
    nr = near[c0:c0 + H]
    na = np.maximum(main_a[c0:c0 + H], ground[c0:c0 + H])
    mist_off = int(t * 40) % W
    mist = mist_tex[:, mist_off:mist_off + W]
    mist_full = np.zeros((H, W), np.float32)
    for band_y in (2350, 1700, 1150):
        sy = int(band_y - cy - 350)
        lo, hi = max(sy, 0), min(sy + 700, H)
        if hi > lo:
            mist_full[lo:hi] += mist[lo - sy:hi - sy] * np.sin(np.linspace(0, np.pi, 700))[lo - sy:hi - sy, None]

    lum = g * (1 - na) + nr * na
    lum = lum + np.clip(mist_full - 0.45, 0, 1) * 0.55
    lum *= reveal
    rgb = lum[..., None] * np.array([0.93, 0.92, 0.9], np.float32)
    mo = moon * (1 - na) * reveal
    rgb = rgb * (1 - mo[..., None] * 0.9) + mo[..., None] * np.array(GOLD, np.float32) / 255

    # characters
    char = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    inkL = Image.new("L", (W, H), 0)
    d, di = ImageDraw.Draw(char), ImageDraw.Draw(inkL)
    gy = GROUND_Y - cy
    walk_t = min(t, 1.45)
    yx = -80 + walk_t * 330
    walking = 0.15 < t < 1.45
    look = ease((t - 1.5) / 0.4)
    youth_head = draw_youth(d, di, yx, gy, 300, walk_t * 9.5, walking, look, ease((t - 1.7) / 0.35), t)
    sage_y = SUMMIT_Y + 18 - cy
    sage_head = None
    if sage_y < H + 300:
        sage_head = draw_sage_on_ox(d, di, SUMMIT_X - 20, sage_y, 340, t)
    inkA = blur(np.asarray(inkL, np.float32) / 255, 7)
    rgb = rgb * (1 - inkA[..., None] * 0.9) + (inkA * (0.55 + 0.25 * blur(np.asarray(inkL, np.float32) / 255, 20)))[..., None] * np.array([0.78, 0.76, 0.72], np.float32)

    # falling ink specks
    spk = Image.new("L", (W, H), 0)
    sdw = ImageDraw.Draw(spk)
    for k in range(len(specks_x)):
        sx = (specks_x[k] + math.sin(t + k) * 20) % W
        sy = (specks_y[k] + specks_v[k] * t - (cy - (WH - H)) * 0.3) % H
        sdw.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=120)
    rgb += (np.asarray(spk, np.float32) / 255 * 0.5 * reveal)[..., None]

    base = Image.fromarray((np.clip(rgb * vign[..., None], 0, 1) * 255).astype(np.uint8)).convert("RGBA")
    base.alpha_composite(char)
    d = ImageDraw.Draw(base)

    # birds during the tilt
    for bx0, by0, bv, ph in birds:
        if 2.2 < t < 5:
            bx = bx0 + (t - 2.2) * bv
            by = by0 - (t - 2.2) * 60
            fl = math.sin(t * 12 + ph) * 14
            d.line([(bx - 22, by - fl), (bx, by), (bx + 22, by - fl)], fill=(200, 195, 180, 200), width=4)

    # callout tags
    tag(d, youth_head[0] - 10, youth_head[1] - 20, youth_head[0] - 60, youth_head[1] - 110, "少年", ease((t - 0.7) / 0.3) * (1 - ease((t - 2.3) / 0.3)))
    if sage_head:
        tag(d, sage_head[0] - 10, sage_head[1], sage_head[0] - 170, sage_head[1] - 80, "骑青牛的老人", ease((t - 4.1) / 0.35))
    if t < 2.6:
        bubble(base, youth_head[0] + 30, youth_head[1] - 10, "道……在哪里？", 1.65, t)

    draw_header(base, t)
    draw_footer(base, t)

    out = np.asarray(base.convert("RGB"), np.float32) / 255
    out += rng.normal(0, 0.014, (H, W, 1)).astype(np.float32)
    Image.fromarray((np.clip(out, 0, 1) * 255).astype(np.uint8)).resize((OW, OH), Image.LANCZOS).save(os.path.join(FRAMES, f"{i:04d}.png"))
    print(f"\rframe {i + 1}/{N}", end="", flush=True)
print()
if ONLY:
    raise SystemExit

# ---------------- audio: wind, footsteps, guqin pluck at the reveal ----------------
SR = 48000
ts = np.arange(int(SR * DUR)) / SR
wind = np.convolve(rng.normal(0, 1, ts.size), np.ones(400) / 400, "same") * 6 * (0.6 + 0.4 * np.sin(2 * np.pi * 0.3 * ts))
drone = 0.12 * np.sin(2 * np.pi * 65.4 * ts) + 0.06 * np.sin(2 * np.pi * 98 * ts)
steps = np.zeros_like(ts)
for k in range(5):
    t0 = 0.25 + k * (2 * math.pi / 9.5)
    if t0 > 1.4:
        break
    bt = np.clip(ts - t0, 0, None)
    steps += (ts >= t0) * np.exp(-bt * 60) * np.sin(2 * np.pi * 140 * bt) * 0.5


def pluck(t0, f, amp):
    bt = np.clip(ts - t0, 0, None)
    return (ts >= t0) * amp * sum(np.sin(2 * np.pi * f * h * bt) * np.exp(-bt * (1.5 + h)) / h for h in (1, 2, 3, 4.02))


music = pluck(1.65, 220, 0.25) + pluck(2.4, 196, 0.3) + pluck(4.1, 293.7, 0.45) + pluck(4.35, 440, 0.25)
mix = (wind + drone + steps + music) * np.clip(ts / 0.5, 0, 1) * np.clip((DUR - ts) / 0.3, 0, 1)
mix = (mix / np.abs(mix).max() * 0.8 * 32767).astype(np.int16)
wav = os.path.join(HERE, "audio_v2.wav")
with wave.open(wav, "wb") as w:
    w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(mix.tobytes())

out = os.path.join(HERE, "demo_v2_5s_sd.mp4")
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(FRAMES, "%04d.png"), "-i", wav,
                "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-c:a", "aac", "-b:a", "128k", "-shortest", out], check=True)
print("wrote", out)
