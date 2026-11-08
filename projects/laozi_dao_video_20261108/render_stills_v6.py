"""《水与石》v6 key stills — black + gold pixel style (after the "朱元璋" reference frame).

Pixel-art boy / rock / props (drawn at 1/6 resolution, nearest-neighbour upscaled), glowing gold light
and water, pixel font, and a glowing gold "pit depth" curve with boxed milestone labels in shot 3.
Builds on render_stills_v5.py (boy rig, rock geometry).  Usage: python3 render_stills_v6.py
"""
import os, sys, math
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render_stills_v5 as S
from render_stills_v5 import W, H, SS, GROUND, RX, RW, RH, DRIP_X, XX, YY, blurf, over, glow, mask_poly

PX = 6
OUT = os.path.join(HERE, "stills_v6")
os.makedirs(OUT, exist_ok=True)
UNI = "/usr/share/fonts/opentype/unifont/unifont.otf"

GOLD = (255, 205, 80)
GOLD_L = (255, 244, 205)
GOLD_D = (200, 130, 22)
TEAR = (150, 210, 255)

# ---- re-colour the boy for the gold/black look (S.boy reads these module globals at call time) ----
S.ROBE, S.ROBE_D, S.CREAM, S.SASH = (240, 184, 48), (184, 128, 26), (255, 240, 200), (200, 60, 40)
S.TROUSER, S.TROUSER_D, S.SHOE = (112, 84, 50), (72, 54, 30), (60, 40, 24)
S.HAIR, S.HAIR_HL = (24, 20, 24), (84, 72, 62)
S.AQUA, S.AQUA_D, S.AQUA_L = GOLD, GOLD_D, GOLD_L
S.STEEL = (232, 232, 226)

TG = dict(top=(.44, .37, .27), mid=(.28, .23, .17), hl=(1.0, .82, .44), sh=(.17, .14, .105), deep=(.085, .07, .055))
TG_DARK = dict(top=(.21, .175, .125), mid=(.135, .11, .08), hl=(.6, .47, .25), sh=(.08, .065, .05), deep=(.04, .035, .028))


# ------------------------------------------------------------------ pixel layer (same API as S.Layer, drawn at 1/PX)
class PixLayer:
    def __init__(self):
        self.f = 1.0 / PX
        self.im = Image.new("RGBA", (W // PX, H // PX), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def _p(self, pts):
        return [(x * self.f, y * self.f) for x, y in pts]

    def poly(self, pts, fill):
        self.d.polygon(self._p(pts), fill=tuple(fill))

    def circ(self, x, y, r, fill):
        f = self.f
        self.d.ellipse([(x - r) * f, (y - r) * f, (x + r) * f, (y + r) * f], fill=tuple(fill))

    def ell(self, x, y, rx, ry, fill, outline=None, width=0):
        f = self.f
        self.d.ellipse([(x - rx) * f, (y - ry) * f, (x + rx) * f, (y + ry) * f], fill=tuple(fill) if fill else None,
                       outline=tuple(outline) if outline else None, width=max(1, round(width * f)))

    def line(self, pts, fill, width, joint=None):
        self.d.line(self._p(pts), fill=tuple(fill), width=max(1, round(width * self.f)), joint=joint)

    def cap(self, p, q, w0, w1, fill):
        (x0, y0), (x1, y1) = p, q
        L = math.hypot(x1 - x0, y1 - y0) or 1
        nx, ny = -(y1 - y0) / L, (x1 - x0) / L
        self.poly([(x0 + nx * w0 / 2, y0 + ny * w0 / 2), (x1 + nx * w1 / 2, y1 + ny * w1 / 2),
                   (x1 - nx * w1 / 2, y1 - ny * w1 / 2), (x0 - nx * w0 / 2, y0 - ny * w0 / 2)], fill)
        self.circ(x0, y0, w0 / 2, fill)
        self.circ(x1, y1, w1 / 2, fill)

    def to_np(self):
        a = np.asarray(self.im, np.float32) / 255
        al = np.repeat(np.repeat((a[..., 3] > .3).astype(np.float32), PX, 0), PX, 1)
        rgb = np.repeat(np.repeat(a[..., :3], PX, 0), PX, 1)
        return rgb, al


def stampP(rgb, PL):
    c, a = PL.to_np()
    return over(rgb, c, a)


def glow_layer(rgb, layer, r, amt, color=GOLD):
    _, a = layer.to_np()
    return rgb + blurf(a, r)[..., None] * (np.array(color, np.float32) / 255) * amt


def pix(a):
    c = PX // 2
    s = a[c::PX, c::PX][:H // PX, :W // PX]
    return np.repeat(np.repeat(s, PX, 0), PX, 1)


# ------------------------------------------------------------------ scene pieces
def bg6(gx=RX, gy=GROUND - 330):
    rgb = np.zeros((H, W, 3), np.float32)
    rgb += np.array([.022, .016, .008], np.float32) * (1 - YY / H)[..., None]
    rgb = glow(rgb, gx, gy, 430, (255, 190, 70), .11)
    xs = np.arange(W, dtype=np.float32)
    for off, amp, col, k in ((300, 1.0, (.05, .04, .028), 0), (230, .8, (.075, .06, .04), 1)):
        ridge = GROUND - off - 110 * amp * np.exp(-((xs - (200 + 400 * k)) / 230) ** 2) - 60 * np.sin(xs / (150 + 40 * k) + k) - 80 * np.exp(-((xs - (920 - 300 * k)) / 210) ** 2)
        m = blurf(((YY > ridge[None, :]) & (YY < GROUND)).astype(np.float32), 2)
        top = np.clip((YY - ridge[None, :]) / 220, 0, 1)
        rgb = over(rgb, np.array(col, np.float32) * (1.25 - .5 * top[..., None]), m)
    g = np.random.default_rng(5)
    for _ in range(60):
        rgb = glow(rgb, g.uniform(0, W), g.uniform(60, GROUND - 450), g.uniform(1.2, 2.2), (255, 235, 190), g.uniform(.12, .5))
    gm = (YY >= GROUND).astype(np.float32) * np.ones((1, W), np.float32)
    ground = np.array([.09, .07, .05], np.float32) * (1 - .6 * np.clip((YY - GROUND) / (H - GROUND), 0, 1))[..., None]
    ground = ground * (.92 + .16 * S.NZ[..., None])
    rgb = over(rgb, ground, gm)
    rgb += (np.exp(-np.abs(YY - GROUND) / 3.0) * (YY >= GROUND) * .22)[..., None] * np.array([1, .8, .4], np.float32)
    return rgb


def rays(rgb, cx, cy, amt, n=14):
    th = np.arctan2(YY - cy, XX - cx)
    r = np.hypot(XX - cx, YY - cy)
    ray = np.clip(np.sin(th * n) * .5 + .5, 0, 1) ** 5
    f = ray * np.exp(-r / 420) * np.clip(r / 60, 0, 1) * amt
    return rgb + f[..., None] * np.array([1, .78, .3], np.float32) * .5


def platform(rgb, cx, y, wid=360):
    m = S.mask_ell([cx - wid / 2, y, cx + wid / 2, y + 12])
    rgb = rgb + blurf(m, 16)[..., None] * np.array([1, .75, .25], np.float32) * .9
    return over(rgb, np.array([1, .95, .75], np.float32), blurf(m, 1.2))


def rock_pix(rgb, m, pal=TG, shadow=True):
    if shadow:
        sm = S.mask_ell([RX - RW * .62, GROUND - 22, RX + RW * .62, GROUND + 46])
        rgb = over(rgb, np.zeros(3, np.float32), blurf(sm, 14) * .6)
    col, a = S.shade_rock(m, pal)
    col = np.round(pix(col) * 18) / 18
    return over(rgb, col, (pix(a) > .5).astype(np.float32))


def overhang_pix(rgb):
    pts = [(560, 0), (W, 0), (W, 620), (980, 560), (860, 545), (760, 520), (700, 500), (660, 470), (600, 420)]
    m = (mask_poly(pts) * (YY > 330)).astype(np.float32)
    col, a = S.shade_rock(m, TG_DARK, 1.2)
    return over(rgb, np.round(pix(col) * 18) / 18, (pix(a) > .5).astype(np.float32))


def details6(PL, m, cracks=True):
    top = S.ROCK_TOP
    if cracks:
        dark = (28, 20, 12, 255)
        for pts, w in (([(RX - 70, top + 100), (RX - 45, top + 170), (RX - 90, top + 245), (RX - 62, top + 330)], 9),
                       ([(RX + 120, top + 130), (RX + 95, top + 200), (RX + 140, top + 270)], 8),
                       ([(RX - 45, top + 170), (RX - 10, top + 205)], 7)):
            for i in range(len(pts) - 1):
                PL.cap(pts[i], pts[i + 1], w, w * .8, dark)
        g = np.random.default_rng(6)
        for _ in range(18):
            x, y = RX + g.uniform(-190, 190), top + g.uniform(120, 400)
            if m[int(y), int(x)] > .9:
                PL.ell(x, y, g.uniform(6, 12), g.uniform(5, 8), (150, 120, 70, 255))


def pebbles6(PL, seed=2):
    g = np.random.default_rng(seed)
    for _ in range(14):
        x, y = g.uniform(40, W - 40), g.uniform(GROUND + 50, GROUND + 330)
        PL.ell(x, y, g.uniform(10, 24), g.uniform(6, 11), (62, 48, 30, 255))
        PL.ell(x - 4, y - 3, 5, 3, (98, 78, 48, 255))


def boy6(PL, pose, ox, oy, s, face, ph):
    S.AQUA = TEAR
    info = S.boy(PL, S.POSES[pose], ox, oy, s, face, ph)
    S.AQUA = GOLD
    return info


def blade_piece(L, x, y, ang, ln=120):
    ca, sa = math.cos(ang), math.sin(ang)
    loc = [(-ln / 2, 13), (ln / 2 - 10, 10), (ln / 2 + 30, 0), (ln / 2 - 10, -10), (-ln / 2, -13), (-ln / 2 + 8, -6), (-ln / 2 - 8, 0), (-ln / 2 + 10, 7)]
    L.poly([(x + u * ca - v * sa, y + u * sa + v * ca) for u, v in loc], S.STEEL + (255,))


def catmull(pts, n=28):
    P = [pts[0]] + list(pts) + [pts[-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1], P[i], P[i + 1], P[i + 2]
        for t in np.linspace(0, 1, n, endpoint=False):
            t2, t3 = t * t, t ** 3
            out.append(tuple(.5 * (2 * p1[k] + (-p0[k] + p2[k]) * t + (2 * p0[k] - 5 * p1[k] + 4 * p2[k] - p3[k]) * t2 + (-p0[k] + 3 * p1[k] - 3 * p2[k] + p3[k]) * t3) for k in (0, 1)))
    out.append(tuple(pts[-1]))
    return out


# ------------------------------------------------------------------ UI
def finish6(rgb, shot):
    img = S.finish(rgb)
    tm = Image.new("L", (W, H), 0)
    ImageDraw.Draw(tm).text((W / 2 - 30, 150), "水 与 石", font=S.font(UNI, 96), fill=255, anchor="mm")
    a = np.asarray(img, np.float32) / 255
    a += blurf(np.asarray(tm, np.float32) / 255, 14)[..., None] * np.array([1, .75, .3], np.float32) * .6
    img = Image.fromarray((np.clip(a, 0, 1) * 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    d.text((W / 2 - 30, 150), "水 与 石", font=S.font(UNI, 96), fill=(255, 232, 160, 255), anchor="mm")
    img.alpha_composite(S.seal_img(78), (W // 2 + 210, 112))
    d = ImageDraw.Draw(img)
    x0, x1, y = 90, W - 90, H - 110
    seg = (x1 - x0 - 48) / 5
    for k in range(5):
        a_ = x0 + k * (seg + 12)
        d.line([(a_, y), (a_ + seg, y)], fill=(70, 58, 40, 255), width=6)
        if k < shot - 1:
            d.line([(a_, y), (a_ + seg, y)], fill=GOLD + (255,), width=6)
        elif k == shot - 1:
            d.line([(a_, y), (a_ + seg * .55, y)], fill=GOLD + (255,), width=6)
    return img.convert("RGB")


def pop(L, s, xy, size, rot, fill=GOLD + (255,)):
    S.pop_text(L, s, xy, size, rot, fill, (34, 16, 4, 255), UNI)


# ------------------------------------------------------------------ shots
def shot1():
    rgb = bg6()
    m = S.rock_mask()
    rgb = rock_pix(rgb, m)
    iy = GROUND - 300
    ix = float(np.nonzero(m[iy] > .5)[0][0]) + 6
    rgb = rays(rgb, 300, 1000, .5)
    rgb = glow(rgb, 300, 1000, 220, GOLD, .22)
    rgb = glow(rgb, ix, iy, 55, GOLD, .45)
    PL, L = PixLayer(), S.Layer()
    details6(PL, m)
    pebbles6(PL)
    for yy_, ln in ((GROUND - 260, 150), (GROUND - 330, 220), (GROUND - 190, 120), (GROUND - 420, 130)):
        L.line([(20, yy_), (20 + ln, yy_ - 6)], GOLD_L + (150,), 6)
    info = boy6(PL, "slash", 150, GROUND - 90, 420, 1, .8)
    hand = ((info["hand"][0] + info["hand2"][0]) / 2, (info["hand"][1] + info["hand2"][1]) / 2)
    ang = math.atan2(iy - hand[1], ix - hand[0])
    S.sword(PL, hand, ang, math.hypot(ix - hand[0], iy - hand[1]) + 6)
    S.starburst(PL, ix, iy, 52, 20, 9, (255, 246, 205, 255), .2)
    S.starburst(PL, ix, iy, 30, 12, 9, (255, 255, 255, 255), .6)
    g = np.random.default_rng(8)
    for _ in range(14):
        a = g.uniform(-math.pi, .1)
        r0, r1 = g.uniform(40, 60), g.uniform(100, 175)
        PL.line([(ix + math.cos(a) * r0, iy + math.sin(a) * r0), (ix + math.cos(a) * r1, iy + math.sin(a) * r1)], GOLD + (255,), g.uniform(5, 9))
    blade_piece(PL, 640, 560, math.radians(-35), 120)
    for k in range(3):
        L.d.arc([(640 - 150 - k * 22) * SS, (560 - 150 - k * 22) * SS, (640 + 150 + k * 22) * SS, (560 + 150 + k * 22) * SS], 150 + k * 8, 205 + k * 8, fill=GOLD_L + (150 - k * 40,), width=4 * SS)
    pop(L, "铛！", (ix + 200, iy - 260), 200, 12)
    rgb = stampP(rgb, PL)
    return finish6(S.stamp(rgb, L), 1)


def shot2():
    rgb = bg6()
    rgb = overhang_pix(rgb)
    m = S.rock_mask()
    rgb = rock_pix(rgb, m)
    top = S.rock_top(m, DRIP_X)
    bx = RX - RW * .5 - 70
    rgb = rays(rgb, bx, 1150, .4)
    rgb = glow(rgb, bx, 1150, 220, GOLD, .2)
    rgb = platform(rgb, bx + 20, GROUND + 4)
    rgb = glow(rgb, DRIP_X, top, 60, GOLD, .6)
    PL, L = PixLayer(), S.Layer()
    details6(PL, m)
    pebbles6(PL)
    boy6(PL, "sit", bx, GROUND, 420, -1, 1.5)
    S.sword(PL, (150, GROUND - 14), math.radians(-3), 90, True)
    PL.poly([(335, GROUND - 4), (420, GROUND - 14), (418, GROUND - 2)], S.STEEL + (255,))
    S.water_drop(PL, DRIP_X, 540, 14)
    S.water_drop(PL, DRIP_X, top - 70, 18)
    for k in range(3):
        PL.line([(DRIP_X, top - 140 - k * 40), (DRIP_X, top - 125 - k * 40)], GOLD_L + (255,), 6)
    S.ring(L, DRIP_X, top, 70, 230)
    S.ring(L, DRIP_X, top, 120, 120, 3)
    for x, y, r_ in ((190, 990, 26), (150, 950, 18), (120, 920, 11)):
        PL.circ(x, y, r_, (120, 110, 100, 255))
    pop(L, "滴", (DRIP_X + 130, top - 90), 120, -8, GOLD_L + (255,))
    pop(L, "哼", (225, 960), 76, 0, (200, 190, 175, 255))
    rgb = stampP(rgb, PL)
    return finish6(S.stamp(rgb, L), 2)


def shot3():
    rgb = bg6()
    rgb = overhang_pix(rgb)
    m = S.rock_mask(.8)
    rgb = rock_pix(rgb, m)
    top = S.rock_top(m, DRIP_X)
    bx = RX - RW * .5 - 70
    rgb = rays(rgb, bx, 1150, .3)
    rgb = platform(rgb, bx + 20, GROUND + 4)
    rgb = glow(rgb, RX, top + 20, 70, GOLD, .9)
    PL, L, CL = PixLayer(), S.Layer(), S.Layer()
    details6(PL, m)
    pebbles6(PL)
    for k, yv in enumerate(range(560, top - 30, 70)):
        S.water_drop(PL, DRIP_X, yv, 10 + (k % 2) * 3, 255)
    boy6(PL, "sleep", bx, GROUND, 420, -1, 2.2)
    # ---- glowing "pit depth" curve with boxed milestones (after the reference chart) ----
    labels = (("1天", 100, 420), ("1年", 120, 600), ("10年", 140, 790))
    nodes = [(125, 420), (88, 600), (130, 790)]
    path = catmull([(112, 330)] + nodes)
    CL.line(path, GOLD + (255,), 9, joint="curve")
    CL.line(path, GOLD_L + (255,), 3, joint="curve")
    rgb = glow_layer(rgb, CL, 14, 1.1)
    rgb = S.stamp(rgb, CL)
    g = np.random.default_rng(3)
    for (txt, size, cy), (nx, ny) in zip(labels, nodes):
        fnt = S.font(UNI, size)
        x0, y0, x1, y1 = fnt.getbbox(txt)
        w, h, pad = x1 - x0, y1 - y0, 22
        left = 200
        L.line([(nx + 14, ny), (left, ny)], GOLD + (200,), 3)
        L.d.rectangle([(nx - 14) * SS, (ny - 14) * SS, (nx + 14) * SS, (ny + 14) * SS], fill=(20, 14, 6, 255), outline=GOLD_L + (255,), width=3 * SS)
        L.d.rectangle([left * SS, (cy - h / 2 - pad) * SS, (left + w + 2 * pad) * SS, (cy + h / 2 + pad) * SS], fill=(18, 12, 4, 225), outline=GOLD + (255,), width=3 * SS)
        L.text((left + pad + w / 2, cy), txt, (UNI, size), GOLD + (255,))
    ex, ey = nodes[-1]
    L.circ(ex, ey, 20, GOLD_L + (255,))
    for _ in range(9):
        a, r = g.uniform(-1.2, 1.2), g.uniform(24, 75)
        s_ = g.uniform(5, 11)
        px_, py_ = ex - 22 - r * .55 * math.cos(a), ey + r * math.sin(a) * 1.1
        L.d.rectangle([(px_ - s_) * SS, (py_ - s_) * SS, (px_ + s_) * SS, (py_ + s_) * SS], fill=GOLD + (int(g.uniform(120, 230)),))
    rgb = glow(rgb, ex, ey, 40, GOLD, .9)
    for zx, zy, zs in ((245, 1075, 46), (205, 1020, 60), (165, 960, 78)):
        L.text((zx, zy), "Z", (UNI, zs), GOLD_L + (235,), stroke=4, stroke_fill=(34, 16, 4, 255))
    rgb = stampP(rgb, PL)
    return finish6(S.stamp(rgb, L), 3)


def shot4():
    rgb = bg6()
    rgb = overhang_pix(rgb)
    m = S.rock_mask(1.0)
    crack = RX + 18 * np.sin(YY / 23.0) + 10 * np.sign(np.sin(YY / 9.0))
    gap = 12
    left, right = m * (XX < crack - gap), m * (XX > crack + gap)
    rot = lambda mm, ang, c: np.asarray(Image.fromarray((mm * 255).astype(np.uint8)).rotate(ang, center=c, resample=Image.BICUBIC), np.float32) / 255
    left, right = rot(left, 15, (RX - RW / 2, GROUND)), rot(right, -15, (RX + RW / 2, GROUND))
    lit = blurf(m * (np.abs(XX - crack) < 70), 20)
    rgb = glow(rgb, RX, GROUND - 300, 170, GOLD, .9)
    rgb = over(rgb, np.array(GOLD_L, np.float32) / 255, np.clip(lit * .9, 0, 1) * np.exp(-((XX - RX) / 60) ** 2))
    rgb = rock_pix(rgb, left)
    rgb = rock_pix(rgb, right, shadow=False)
    rgb = rays(rgb, 235, 1150, .4)
    rgb = glow(rgb, 235, 1150, 220, GOLD, .2)
    rgb = platform(rgb, 235, GROUND + 4, 300)
    PL, L, WL = PixLayer(), S.Layer(), S.Layer()
    pebbles6(PL)
    for k, (dx, w) in enumerate(((0, 50), (-24, 24), (24, 24))):
        pts = [(RX + dx + math.sin(u * 5 + k) * 14 * (1 - u), GROUND - 430 + u * 450) for u in np.linspace(0, 1, 16)]
        for i in range(len(pts) - 1):
            WL.cap(pts[i], pts[i + 1], w, w * 1.05, (GOLD if k == 0 else GOLD_D) + (240,))
    for i in range(5):
        WL.line([(RX - 8 + i * 4, GROUND - 400 + i * 20), (RX - 6 + i * 3, GROUND - 40)], GOLD_L + (230,), 5)
    WL.ell(RX, GROUND + 70, 330, 62, GOLD_D + (170,))
    WL.ell(RX, GROUND + 64, 260, 44, GOLD + (190,))
    S.ring(WL, RX, GROUND + 70, 330, 220)
    S.ring(WL, RX, GROUND + 70, 230, 160, 3)
    rgb = glow_layer(rgb, WL, 16, .8)
    rgb = S.stamp(rgb, WL)
    g = np.random.default_rng(4)
    for k in range(10):
        cx_, cy_ = RX + g.uniform(-210, 210), GROUND - g.uniform(450, 740)
        sz, r_ = g.uniform(10, 24), g.uniform(0, 6)
        pts = [(sz, 0), (0, sz * .7), (-sz * .8, 0), (0, -sz)]
        PL.poly([(cx_ + px * math.cos(r_) - py * math.sin(r_), cy_ + px * math.sin(r_) + py * math.cos(r_)) for px, py in pts], (190, 160, 105, 255))
    for k in range(3):
        a = math.radians(-130 + k * 32)
        PL.line([(235 + math.cos(a) * 250, GROUND - 440 + math.sin(a) * 250), (235 + math.cos(a) * 310, GROUND - 440 + math.sin(a) * 310)], GOLD_L + (255,), 8)
    boy6(PL, "amazed", 235, GROUND, 420, 1, .5)
    pop(L, "咔！", (RX + 30, GROUND - 880), 200, -6, GOLD_L + (255,))
    rgb = stampP(rgb, PL)
    return finish6(S.stamp(rgb, L), 4)


def shot5():
    rgb = np.zeros((H, W, 3), np.float32) + (np.array([.022, .016, .008], np.float32) * (1 - YY / H)[..., None])
    rgb = glow(rgb, W / 2, 760, 340, (255, 190, 70), .2)
    rgb = rays(rgb, W / 2, 700, .35, 12)
    PL, L = PixLayer(), S.Layer()
    S.water_drop(PL, W / 2, 640, 36)
    for rx, al in ((120, 230), (200, 140), (290, 80)):
        S.ring(L, W / 2, 770, rx, al)
    rgb = glow(rgb, W / 2, 640, 80, GOLD, .7)
    # big title line, then verse with gold keywords
    big = Image.new("L", (W, H), 0)
    for k, ch in enumerate("柔弱胜刚强"):
        L.text((W / 2 + (k - 2) * 182, 1010), ch, (UNI, 176), (255, 244, 215, 255))
        ImageDraw.Draw(big).text((W / 2 + (k - 2) * 182, 1010), ch, font=S.font(UNI, 176), fill=255, anchor="mm")
    rgb = rgb + blurf(np.asarray(big, np.float32) / 255, 18)[..., None] * np.array([1, .75, .3], np.float32) * .55
    rgb = stampP(rgb, PL)
    rgb = S.stamp(rgb, L)
    img = finish6(rgb, 5).convert("RGBA")
    d = ImageDraw.Draw(img)

    def line(txt, y, hi):
        n, sz = len(txt), 48
        for i, ch in enumerate(txt):
            d.text((W / 2 - n * sz / 2 + sz * i + sz / 2, y), ch, font=S.font(UNI, sz), fill=(GOLD if i in hi else (236, 228, 210)) + (255,), anchor="mm")

    line("天下莫柔弱于水，", 1215, {6})
    line("而攻坚强者莫之能胜。", 1285, {5, 6, 7, 8})
    d.text((W / 2, 1375), "——《道德经》第七十八章", font=S.font(UNI, 32), fill=(150, 136, 110, 255), anchor="mm")
    return img.convert("RGB")


if __name__ == "__main__":
    only = [int(x) for x in os.environ.get("ONLY", "1,2,3,4,5").split(",")]
    fns = {1: shot1, 2: shot2, 3: shot3, 4: shot4, 5: shot5}
    ims = []
    for k in only:
        im = fns[k]()
        im.save(os.path.join(OUT, f"shot{k}.png"))
        ims.append(im.resize((540, 960), Image.LANCZOS))
        print("shot", k, flush=True)
    sheet = Image.new("RGB", (556 * len(ims) - 16, 960), (40, 40, 40))
    for k, im in enumerate(ims):
        sheet.paste(im, (k * 556, 0))
    sheet.save(os.path.join(HERE, "keyframes_v6.png"))
