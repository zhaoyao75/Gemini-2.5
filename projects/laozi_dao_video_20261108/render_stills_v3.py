"""《水与石》key stills for the 15s vertical story (storyboard_v3.md).

Draws each shot's key frame at 1080x1920 and saves 540x960 PNGs + a contact sheet.
Usage: python3 render_stills_v3.py
"""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1080, 1920
OUT = os.path.join(HERE, "stills_v3")
os.makedirs(OUT, exist_ok=True)
CAL = os.path.join(HERE, "fonts", "MaShanZheng-Regular.ttf")
SERIF = os.path.join(HERE, "fonts", "NotoSerifSC-Light.otf")

IVORY = (237, 230, 214)
GOLD = (222, 184, 108)
RED = (190, 52, 40)
GROUND = 1360
rng = np.random.default_rng(11)


def F(path, size):
    return ImageFont.truetype(path, size)


def blur(a, r):
    return np.asarray(Image.fromarray(np.clip(a * 255, 0, 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r)), np.float32) / 255


def noise2d(h, w, scales, weights):
    acc = np.zeros((h, w), np.float32)
    for s, wt in zip(scales, weights):
        sh, sw = (s, s) if isinstance(s, int) else s
        small = rng.random((h // sh + 3, w // sw + 3)).astype(np.float32)
        big = np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize(((w // sw + 3) * sw, (h // sh + 3) * sh), Image.BICUBIC), np.float32)[:h, :w] / 255
        acc += wt * big
    return acc


TEX = noise2d(H, W, (5, 18, 60), (0.3, 0.4, 0.3))
STREAK = noise2d(H, W, ((2, 40), (4, 90)), (0.6, 0.4))  # dry-brush streaks (horizontal)
PAPER = noise2d(H, W, (3, 200), (0.5, 0.5))


class Canvas:
    def __init__(self):
        self.rgb = np.zeros((H, W, 3), np.float32) + (PAPER[..., None] * 0.035)
        self.top = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.top)

    def wash(self, mask, tone, edge=0.25, tex=0.45, color=(0.93, 0.91, 0.87)):
        """Ink wash from a 0..1 mask: soft body + lighter pooled rim, textured."""
        m = blur(mask, 2.5)
        rim = np.clip(m - blur(m, 9), 0, 1) * 2.2
        v = m * tone * (1 - tex + tex * TEX) + rim * edge * (0.5 + 0.5 * STREAK)
        a = np.clip(m * 1.2, 0, 1)
        self.rgb = self.rgb * (1 - a[..., None]) + v[..., None] * np.array(color, np.float32)

    def glow(self, x, y, r, color, amt):
        yy, xx = np.ogrid[0:H, 0:W]
        g = np.exp(-((xx - x) ** 2 + (yy - y) ** 2) / (2 * r * r)).astype(np.float32) * amt
        self.rgb += g[..., None] * np.array(color, np.float32) / 255

    def flatten(self):
        yy, xx = np.ogrid[0:H, 0:W]
        vign = np.clip(1.18 - (np.hypot((xx - W / 2) / W, (yy - H / 2) / H) * 1.5) ** 2, 0, 1)
        base = Image.fromarray((np.clip(self.rgb * vign[..., None], 0, 1) * 255).astype(np.uint8)).convert("RGBA")
        base.alpha_composite(self.top)
        return base


def mask_from(draw_fn):
    im = Image.new("L", (W, H), 0)
    draw_fn(ImageDraw.Draw(im))
    return np.asarray(im, np.float32) / 255


# ---------- brush primitives ----------
def seg(d, p, q, w0, w1, fill):
    (x0, y0), (x1, y1) = p, q
    L = math.hypot(x1 - x0, y1 - y0) or 1
    nx, ny = -(y1 - y0) / L, (x1 - x0) / L
    d.polygon([(x0 + nx * w0 / 2, y0 + ny * w0 / 2), (x1 + nx * w1 / 2, y1 + ny * w1 / 2),
               (x1 - nx * w1 / 2, y1 - ny * w1 / 2), (x0 - nx * w0 / 2, y0 - ny * w0 / 2)], fill=fill)
    for (x, y), w in (((x0, y0), w0), ((x1, y1), w1)):
        d.ellipse([x - w / 2, y - w / 2, x + w / 2, y + w / 2], fill=fill)


def stroke(d, pts, w0, w1, fill, wmid=None):
    """Brush stroke through points; width swells to wmid in the middle."""
    n = len(pts) - 1
    wmid = wmid or max(w0, w1)
    for i in range(n):
        u0, u1 = i / n, (i + 1) / n
        wa = w0 + (wmid - w0) * math.sin(u0 * math.pi) if u0 < 0.5 else w1 + (wmid - w1) * math.sin(u0 * math.pi)
        wb = w0 + (wmid - w0) * math.sin(u1 * math.pi) if u1 < 0.5 else w1 + (wmid - w1) * math.sin(u1 * math.pi)
        seg(d, pts[i], pts[i + 1], wa, wb, fill)


def curve(p0, p1, p2, n=12):
    return [((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * p1[0] + u * u * p2[0],
             (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * p1[1] + u * u * p2[1]) for u in np.linspace(0, 1, n)]


# ---------- the youth ----------
POSES = {
    # local units: x forward, y up, feet origin, height 1
    "slash": dict(pelvis=(0, .46), neck=(.1, .74), head=(.17, .88), tilt=-.25,
                  legF=[(.2, .32), (.34, .12)], legB=[(-.14, .32), (-.33, .22)],
                  armF=[(.2, .86), (.3, 1.0)], armB=[(.1, .88), (.26, 1.0)], brow="angry", robe_wind=-1),
    "sit": dict(pelvis=(0, .1), neck=(-.07, .44), head=(-.02, .57), tilt=.35,
                legF=[(.22, .3), (.3, 0)], legB=[(.18, .27), (.25, 0)],
                armF=[(.08, .27), (.21, .33)], armB=[(.06, .29), (.19, .35)], brow="sulk", robe_wind=1),
    "sleep": dict(pelvis=(0, .1), neck=(-.08, .44), head=(-.06, .56), tilt=.75,
                  legF=[(.24, .25), (.38, 0)], legB=[(.2, .22), (.36, .02)],
                  armF=[(.1, .22), (.2, .14)], armB=[(.06, .24), (.16, .14)], brow="sleep", robe_wind=1),
    "amazed": dict(pelvis=(0, .46), neck=(-.03, .76), head=(-.05, .9), tilt=-.15,
                   legF=[(.08, .24), (.1, 0)], legB=[(-.1, .24), (-.14, 0)],
                   armF=[(.1, .9), (.16, 1.1)], armB=[(-.14, .88), (-.2, 1.08)], brow="wow", robe_wind=-1),
}


def draw_youth(cv, pose, ox, oy, s, face=1, ph=0.0):
    p = POSES[pose]
    T = lambda q: (ox + q[0] * s * face, oy - q[1] * s)
    pel, nek, hd = T(p["pelvis"]), T(p["neck"]), T(p["head"])
    lw = 0.05 * s
    r = 0.125 * s
    # robe: ink wash short tunic from shoulders to mid-thigh, flaring with wind
    wind = p["robe_wind"] * face
    sx, sy = nek
    px, py = pel
    dx, dy = px - sx, py - sy
    L = math.hypot(dx, dy)
    nx, ny = -dy / L, dx / L
    robe = [(sx + nx * .07 * s, sy + ny * .07 * s), (sx - nx * .07 * s, sy - ny * .07 * s),
            (px - nx * .15 * s + dx * .25 + wind * .06 * s, py - ny * .15 * s + dy * .25),
            (px + dx * .32 + wind * .14 * s, py + dy * .3),
            (px + nx * .17 * s + dx * .25 + wind * .02 * s, py + ny * .17 * s + dy * .25)]
    cv.wash(mask_from(lambda d: d.polygon(robe, fill=255)), 0.5, edge=0.35)
    d = cv.d
    back = IVORY + (150,)
    front = IVORY + (255,)
    # back limbs first (dimmer), then spine, then front limbs
    for key, col in (("legB", back), ("armB", back)):
        a, b = p[key]
        root = pel if key.startswith("leg") else nek
        stroke(d, [root, T(a), T(b)], lw, lw * .45, col, lw * 1.05)
    stroke(d, curve(pel, ((pel[0] + nek[0]) / 2 - 0.03 * s * face, (pel[1] + nek[1]) / 2), nek, 8), lw * 1.1, lw * .9, front, lw * 1.25)
    for key in ("legF", "armF"):
        a, b = p[key]
        root = pel if key.startswith("leg") else nek
        stroke(d, [root, T(a), T(b)], lw, lw * .45, front, lw * 1.05)
    # head
    hx, hy = hd
    d.ellipse([hx - r, hy - r, hx + r, hy + r], fill=front)
    tilt = p["tilt"] * face
    # topknot at back-top
    kx, ky = hx - math.sin(tilt + .5 * face) * r * 1.05, hy - math.cos(tilt + .5 * face) * r * 1.05
    d.ellipse([kx - r * .38, ky - r * .38, kx + r * .38, ky + r * .38], fill=front)
    # red headband across forehead + two flowing tails behind
    ang = math.degrees(tilt)
    d.arc([hx - r * 1.02, hy - r * 1.02, hx + r * 1.02, hy + r * 1.02], 200 + ang, 340 + ang, fill=RED + (255,), width=int(r * .32))
    bx, by = hx - face * r * .9 * math.cos(tilt), hy - r * .45
    for k, (amp, ln) in enumerate(((.10, .55), (.06, .42))):
        pts = [(bx - face * u * ln * s, by + math.sin(u * 7 + k + ph) * amp * s * u + u * .05 * s * (k + 1)) for u in np.linspace(0, 1, 14)]
        stroke(d, pts, r * .22, r * .04, RED + (240,), r * .24)
    # face: eye + brow (looking along face direction)
    ex, ey = hx + face * r * .45, hy - r * .02
    brow = p["brow"]
    dark = (12, 12, 12, 255)
    if brow == "sleep":
        d.arc([ex - 14, ey - 10, ex + 14, ey + 10], 10, 170, fill=dark, width=5)
    else:
        er = 9 if brow != "wow" else 12
        d.ellipse([ex - er, ey - er, ex + er, ey + er], fill=dark)
    if brow == "angry":
        d.line([(ex - face * 22, ey - 30), (ex + face * 14, ey - 18)], fill=dark, width=6)
    elif brow == "sulk":
        d.line([(ex - face * 20, ey - 20), (ex + face * 14, ey - 28)], fill=dark, width=5)
        d.line([(ex + face * 2, ey + 34), (ex + face * 24, ey + 30)], fill=dark, width=4)
    elif brow == "wow":
        d.arc([ex - 22, ey - 44, ex + 22, ey - 14], 200, 340, fill=dark, width=5)
        d.ellipse([ex + face * 6 - 10, ey + 26, ex + face * 6 + 10, ey + 48], outline=dark, width=4)
    return dict(head=hd, r=r, hands=T(p["armF"][1]), T=T)


# ---------- rock ----------
RX, RW, RH = 680, 560, 560


def rock_mask(hole=0.0):
    pts = []
    base = noise2d(1, 400, (40,), (1.0,))[0]
    for i, a in enumerate(np.linspace(0, 2 * math.pi, 120, endpoint=False)):
        rr = 1 + (base[int(i * 3.3)] - .5) * .18
        x = RX + math.cos(a) * RW / 2 * rr
        y = GROUND - RH * .5 + math.sin(a) * RH * .55 * rr
        pts.append((x, min(y, GROUND + 6)))
    m = mask_from(lambda d: d.polygon(pts, fill=255))
    if hole > 0:  # pit worn by drops, at the top
        hm = mask_from(lambda d: d.ellipse([RX - 40 * hole - 10, GROUND - RH - 6, RX + 40 * hole + 10, GROUND - RH + 160 * hole], fill=255))
        m = m * (1 - hm)
    return m


def rock_top_y(m, x):
    col = np.nonzero(m[:, int(x)] > .5)[0]
    return col[0] if len(col) else GROUND


def draw_rock(cv, m, cun=True):
    cv.wash(m, 0.33, edge=0.55, tex=0.55)
    if cun:  # a few dry hemp-fibre strokes
        lay = Image.new("L", (W, H), 0)
        d = ImageDraw.Draw(lay)
        for _ in range(26):
            x = rng.uniform(RX - RW * .38, RX + RW * .38)
            y = rng.uniform(GROUND - RH * .85, GROUND - 60)
            pts = curve((x, y), (x + rng.uniform(-30, 30), y + 35), (x + rng.uniform(-50, 10), y + 80), 6)
            stroke(d, pts, 2, 1, int(rng.uniform(50, 110)), 7)
        a = blur(np.asarray(lay, np.float32) / 255, 1) * m * (0.5 + 0.5 * STREAK)
        cv.rgb += a[..., None] * np.array(IVORY, np.float32) / 255 * 0.8


def ground(cv):
    g = mask_from(lambda d: d.rectangle([0, GROUND, W, H], fill=255))
    cv.wash(g, 0.12, edge=0.0, tex=0.6)
    lay = Image.new("L", (W, H), 0)
    stroke(ImageDraw.Draw(lay), [(40, GROUND + 4), (540, GROUND - 2), (1040, GROUND + 5)], 3, 2, 255, 10)
    a = blur(np.asarray(lay, np.float32) / 255, 1.2) * (0.35 + 0.65 * STREAK)
    cv.rgb += a[..., None] * np.array(IVORY, np.float32) / 255 * 0.7


def far_hills(cv, amt=0.16):
    xs = np.arange(W)
    ridge = GROUND - 260 - 120 * np.exp(-((xs - 200) / 220) ** 2) - 60 * np.sin(xs / 140) - 80 * np.exp(-((xs - 900) / 200) ** 2)
    m = (np.arange(H)[:, None] > ridge[None, :]).astype(np.float32)
    m[GROUND:] = 0
    cv.wash(m * (1 - np.clip((np.arange(H)[:, None] - ridge[None, :]) / 300, 0, 1)), amt, edge=.12, tex=.5)


def overhang(cv):
    pts = [(560, 0), (W, 0), (W, 620), (980, 560), (860, 545), (760, 520), (700, 500), (660, 470), (600, 420)]
    m = mask_from(lambda d: d.polygon(pts, fill=255)) * (np.arange(H)[:, None] > 330)
    cv.wash(m.astype(np.float32), 0.3, edge=.5, tex=.55)


DRIP_X = 690


def drop(d, x, y, s, fill=GOLD + (255,)):
    d.polygon([(x, y - s * 1.6), (x - s * .75, y - s * .1), (x + s * .75, y - s * .1)], fill=fill)
    d.ellipse([x - s * .8, y - s * .8, x + s * .8, y + s * .8], fill=fill)


# ---------- overlays ----------
def header(cv):
    d = cv.d
    d.text((W / 2, 150), "水 与 石", font=F(CAL, 112), fill=IVORY + (255,), anchor="mm")
    sl = Image.new("RGBA", (78, 78), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sl)
    sd.rounded_rectangle([0, 0, 77, 77], radius=8, fill=RED + (235,))
    sd.text((39, 41), "道", font=F(CAL, 58), fill=(28, 8, 6, 255), anchor="mm")
    cv.top.alpha_composite(sl, (W // 2 + 210, 112))
    d.text((W / 2, 238), "老子小故事 · 01", font=F(SERIF, 32), fill=(170, 162, 145, 255), anchor="mm")
    d.line([(W / 2 - 170, 272), (W / 2 + 170, 272)], fill=GOLD + (140,), width=2)


def footer(cv, shot, t, sub):
    d = cv.d
    pa = np.zeros((360, W, 4), np.uint8)
    pa[..., 3] = (np.linspace(0, 1, 360)[:, None] ** .8 * 215).astype(np.uint8)
    cv.top.alpha_composite(Image.fromarray(pa), (0, H - 360))
    if sub:
        d.text((W / 2, H - 230), sub, font=F(SERIF, 50), fill=IVORY + (255,), anchor="mm")
    # 5-segment progress bar
    x0, x1, y = 90, W - 90, H - 120
    seg_w = (x1 - x0 - 4 * 12) / 5
    for k in range(5):
        a = x0 + k * (seg_w + 12)
        d.line([(a, y), (a + seg_w, y)], fill=(80, 76, 70, 255), width=6)
        if k < shot - 1:
            d.line([(a, y), (a + seg_w, y)], fill=GOLD + (255,), width=6)
        elif k == shot - 1:
            d.line([(a, y), (a + seg_w * .55, y)], fill=GOLD + (255,), width=6)
    d.text((x0, H - 78), "00:%02d" % t, font=F(SERIF, 30), fill=(150, 144, 130, 255), anchor="lm")
    d.text((x1, H - 78), "00:15", font=F(SERIF, 30), fill=(110, 105, 95, 255), anchor="rm")


def sfx(cv, text, x, y, size, rot, color=IVORY):
    lay = Image.new("RGBA", (size * 3, size * 2), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((size * 1.5, size), text, font=F(CAL, size), fill=color + (255,), anchor="mm")
    lay = lay.rotate(rot, resample=Image.BICUBIC, expand=False)
    cv.top.alpha_composite(lay, (int(x - size * 1.5), int(y - size)))


# ---------- shots ----------
def shot1():
    cv = Canvas()
    far_hills(cv)
    ground(cv)
    m = rock_mask()
    draw_rock(cv, m)
    ix, iy = RX - RW * .42, rock_top_y(m, RX - RW * .42) + 30  # impact point on rock shoulder
    cv.glow(ix, iy, 70, GOLD, .7)
    y = draw_youth(cv, "slash", 215, GROUND - 90, 400, face=1)
    d = cv.d
    hx, hy = y["hands"]
    # sword: hilt + snapped blade stub towards impact
    ang = math.atan2(iy - hy, ix - hx)
    tip = (hx + math.cos(ang) * 150, hy + math.sin(ang) * 150)
    seg(d, (hx - math.cos(ang) * 40, hy - math.sin(ang) * 40), (hx, hy), 16, 16, RED + (255,))
    seg(d, (hx - 14 * math.sin(ang) * 2, hy + 14 * math.cos(ang) * 2), (hx + 14 * math.sin(ang) * 2, hy - 14 * math.cos(ang) * 2), 8, 8, GOLD + (255,))
    seg(d, (hx, hy), tip, 14, 11, (215, 215, 210, 255))
    # flying broken half, spinning
    fx, fy = 620, 470
    a2 = math.radians(-35)
    seg(d, (fx - 75 * math.cos(a2), fy - 75 * math.sin(a2)), (fx + 75 * math.cos(a2), fy + 75 * math.sin(a2)), 11, 4, (215, 215, 210, 255))
    for k in range(3):
        d.arc([fx - 110 - k * 18, fy - 110 - k * 18, fx + 110 + k * 18, fy + 110 + k * 18], 150 + k * 10, 210 + k * 10, fill=(200, 195, 180, 150 - k * 40), width=3)
    # sparks
    for k in range(16):
        a = rng.uniform(-math.pi, .2)
        r0, r1 = rng.uniform(20, 50), rng.uniform(90, 190)
        d.line([(ix + math.cos(a) * r0, iy + math.sin(a) * r0), (ix + math.cos(a) * r1, iy + math.sin(a) * r1)], fill=GOLD + (255,), width=int(rng.uniform(3, 7)))
    sfx(cv, "铛！", ix + 170, iy - 220, 170, 12, GOLD)
    header(cv)
    footer(cv, 1, 1, "石头挡路，少年拔剑就砍。")
    return cv.flatten()


def shot2():
    cv = Canvas()
    far_hills(cv)
    overhang(cv)
    ground(cv)
    m = rock_mask()
    draw_rock(cv, m)
    top = rock_top_y(m, DRIP_X)
    draw_youth(cv, "sit", RX - RW * .5 - 70, GROUND, 400, face=-1)
    d = cv.d
    # broken sword on the ground
    seg(d, (150, GROUND - 8), (230, GROUND - 14), 14, 14, RED + (255,))
    seg(d, (230, GROUND - 14), (300, GROUND - 18), 12, 10, (200, 200, 195, 255))
    seg(d, (330, GROUND - 6), (410, GROUND - 4), 9, 4, (200, 200, 195, 255))
    # hanging drop, falling drop, splash on rock
    drop(d, DRIP_X, 532, 14)
    cv.glow(DRIP_X, 760, 40, GOLD, .35)
    drop(d, DRIP_X, 760, 18)
    for k in range(3):
        d.line([(DRIP_X, 700 - k * 40), (DRIP_X, 715 - k * 40)], fill=GOLD + (120 - k * 35,), width=4)
    for k, (rx, al) in enumerate(((70, 200), (120, 110))):
        d.ellipse([DRIP_X - rx, top - rx * .22, DRIP_X + rx, top + rx * .22], outline=GOLD + (al,), width=3)
    sfx(cv, "滴", DRIP_X + 120, 690, 100, -8, GOLD)
    # sulking puff
    d.text((RX - RW * .5 - 220, GROUND - 470), "哼", font=F(CAL, 70), fill=(170, 165, 150, 255), anchor="mm")
    header(cv)
    footer(cv, 2, 4, "剑断了。只有一滴水，落在石头上。")
    return cv.flatten()


def shot3():
    cv = Canvas()
    d = cv.d
    # sun & moon arcs (time passing)
    cx, cy, R = W / 2, 980, 560
    for a in np.linspace(200, 340, 26):
        a0, a1 = math.radians(a), math.radians(a + 3)
        d.line([(cx + R * math.cos(a0), cy + R * math.sin(a0)), (cx + R * math.cos(a1), cy + R * math.sin(a1))], fill=(140, 132, 115, 200), width=3)
    sx, sy = cx + R * math.cos(math.radians(222)), cy + R * math.sin(math.radians(222))
    cv.glow(sx, sy, 60, GOLD, .6)
    d.ellipse([sx - 34, sy - 34, sx + 34, sy + 34], fill=GOLD + (255,))
    mx, my = cx + R * math.cos(math.radians(318)), cy + R * math.sin(math.radians(318))
    d.ellipse([mx - 32, my - 32, mx + 32, my + 32], fill=IVORY + (255,))
    d.ellipse([mx - 18, my - 40, mx + 46, my + 24], fill=(0, 0, 0, 255))
    d.text((cx, cy - R - 40), "日 → 月 → 日 → 月", font=F(SERIF, 30), fill=(150, 144, 130, 255), anchor="mm")
    far_hills(cv, .12)
    overhang(cv)
    ground(cv)
    m = rock_mask(hole=.8)
    draw_rock(cv, m)
    top = GROUND - RH
    cv.glow(DRIP_X, top + 60, 60, GOLD, .55)
    # stream of drops
    for k, yv in enumerate(range(540, top, 70)):
        drop(cv.d, DRIP_X, yv, 10 + (k % 2) * 3, GOLD + (230,))
    # year counters
    for k, (txt, x, y) in enumerate((("+1 天", 800, 640), ("+1 年", 560, 720), ("+10 年", 820, 800))):
        cv.d.text((x, y), txt, font=F(SERIF, 34), fill=GOLD + (230 - k * 20,), anchor="mm")
    draw_youth(cv, "sleep", RX - RW * .5 - 70, GROUND, 400, face=-1)
    for k, (zx, zy, zs) in enumerate(((250, 1010, 40), (205, 950, 54), (150, 875, 70))):
        cv.d.text((zx, zy), "Z", font=F(CAL, zs), fill=IVORY + (220,), anchor="mm")
    header(cv)
    footer(cv, 3, 8, "一天，一年，十年……")
    return cv.flatten()


def shot4():
    cv = Canvas()
    far_hills(cv)
    overhang(cv)
    ground(cv)
    m = rock_mask(hole=1.0)
    yy, xx = np.mgrid[0:H, 0:W]
    crack = RX + 18 * np.sin(yy / 23.0) + 10 * np.sign(np.sin(yy / 9.0))
    left = Image.fromarray((m * (xx < crack - 10) * 255).astype(np.uint8))
    right = Image.fromarray((m * (xx > crack + 10) * 255).astype(np.uint8))
    left = np.asarray(left.rotate(15, center=(RX - RW / 2, GROUND), resample=Image.BICUBIC), np.float32) / 255
    right = np.asarray(right.rotate(-15, center=(RX + RW / 2, GROUND), resample=Image.BICUBIC), np.float32) / 255
    draw_rock(cv, left, cun=False)
    draw_rock(cv, right, cun=False)
    cv.glow(RX, GROUND - 260, 150, GOLD, .45)
    d = cv.d
    # water flowing out of the gap and across the ground
    for k in range(5):
        y0 = GROUND - 420 + k * 18
        pts = [(RX + math.sin(u * 6 + k) * 22 * (1 - u), y0 + u * (440 - k * 18)) for u in np.linspace(0, 1, 14)]
        stroke(d, pts, 3, 6, GOLD + (220 - k * 30,), 8)
    for k in range(4):
        y0 = GROUND + 40 + k * 34
        pts = [(RX - 260 + u * 520, y0 + math.sin(u * 12 + k) * 8) for u in np.linspace(0, 1, 24)]
        stroke(d, pts, 2, 2, GOLD + (200 - k * 40,), 5)
    # flying chips
    for k in range(9):
        cx, cy = RX + rng.uniform(-200, 200), GROUND - rng.uniform(450, 720)
        sz = rng.uniform(8, 20)
        d.polygon([(cx, cy - sz), (cx + sz, cy), (cx, cy + sz * .7), (cx - sz * .8, cy)], fill=(150, 146, 136, 255))
    sfx(cv, "咔！", RX + 30, GROUND - 860, 190, -6, IVORY)
    draw_youth(cv, "amazed", 215, GROUND, 400, face=1)
    for k in range(3):  # surprise marks
        a = math.radians(-120 + k * 30)
        cv.d.line([(215 + math.cos(a) * 250, GROUND - 400 + math.sin(a) * 250 - 40), (215 + math.cos(a) * 300, GROUND - 400 + math.sin(a) * 300 - 40)], fill=IVORY + (220,), width=6)
    header(cv)
    footer(cv, 4, 11, "石头，自己开了。")
    return cv.flatten()


def shot5():
    cv = Canvas()
    d = cv.d
    cv.glow(W / 2, 640, 70, GOLD, .5)
    drop(d, W / 2, 640, 34)
    for k, (rx, al) in enumerate(((120, 200), (200, 120), (290, 60))):
        d.ellipse([W / 2 - rx, 760 - rx * .2, W / 2 + rx, 760 + rx * .2], outline=GOLD + (al,), width=3)
    big = F(CAL, 176)
    for k, ch in enumerate("柔弱胜刚强"):
        d.text((W / 2 + (k - 2) * 182, 1010), ch, font=big, fill=IVORY + (255,), anchor="mm")
    sl = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sl)
    sd.rounded_rectangle([0, 0, 119, 119], radius=10, fill=RED + (240,))
    sd.text((60, 62), "道", font=F(CAL, 90), fill=(28, 8, 6, 255), anchor="mm")
    cv.top.alpha_composite(sl.rotate(-6, resample=Image.BICUBIC, expand=True), (W - 230, 1080))
    d.text((W / 2, 1210), "天下莫柔弱于水，", font=F(SERIF, 42), fill=(205, 198, 182, 255), anchor="mm")
    d.text((W / 2, 1275), "而攻坚强者莫之能胜。", font=F(SERIF, 42), fill=(205, 198, 182, 255), anchor="mm")
    d.text((W / 2, 1365), "——《道德经》第七十八章", font=F(SERIF, 32), fill=(140, 134, 120, 255), anchor="mm")
    header(cv)
    footer(cv, 5, 14, None)
    return cv.flatten()


if __name__ == "__main__":
    imgs = []
    for k, fn in enumerate((shot1, shot2, shot3, shot4, shot5), 1):
        img = fn().convert("RGB").resize((540, 960), Image.LANCZOS)
        img.save(os.path.join(OUT, f"shot{k}.png"))
        imgs.append(img)
        print("shot", k)
    sheet = Image.new("RGB", (540 * 5 + 16 * 4, 960), (40, 40, 40))
    for k, im in enumerate(imgs):
        sheet.paste(im, (k * 556, 0))
    sheet.save(os.path.join(HERE, "keyframes_v3.png"))
    print("done")
