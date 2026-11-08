"""《水与石》v4 key stills — flat-vector chibi style (no stick figure, no ink wash).

Black background, cel-shaded slate rock, glowing aqua water, a chibi boy with a red robe and red headband.
Characters/props are drawn at 2x and box-downsampled (premultiplied) for clean edges.
Usage: python3 render_stills_v4.py   -> stills_v4/shot1..5.png + keyframes_v4.png
"""
import math, os
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
W, H, SS = 1080, 1920, 2
OUT = os.path.join(HERE, "stills_v4")
os.makedirs(OUT, exist_ok=True)
CAL = os.path.join(HERE, "fonts", "MaShanZheng-Regular.ttf")
SERIF = os.path.join(HERE, "fonts", "NotoSerifSC-Light.otf")
rng = np.random.default_rng(12)

# ---- palette ----
SKIN, BLUSH = (246, 205, 165), (240, 130, 120)
HAIR, HAIR_HL = (30, 34, 52), (72, 82, 120)
ROBE, ROBE_D, CREAM = (214, 70, 52), (160, 44, 34), (246, 232, 200)
SASH, TROUSER, TROUSER_D = (240, 190, 70), (70, 86, 140), (46, 58, 98)
SHOE = (236, 224, 196)
AQUA, AQUA_D, AQUA_L = (88, 218, 232), (30, 150, 180), (200, 248, 250)
GOLD, IVORY, RED = (244, 196, 82), (240, 232, 216), (205, 55, 42)
STEEL, STEEL_D = (222, 228, 236), (150, 160, 178)
GROUND = 1360
RX, RW, RH, DRIP_X = 680, 560, 560, 690

_F = {}


def font(path, size):
    k = (path, int(size))
    if k not in _F:
        _F[k] = ImageFont.truetype(path, int(size))
    return _F[k]


# ------------------------------------------------------------------ float image helpers
def box(a, r, axis):
    pad = [(0, 0), (0, 0)]
    pad[axis] = (r + 1, r)
    c = np.cumsum(np.pad(a, pad, mode="edge"), axis=axis, dtype=np.float64)
    hi, lo = [slice(None)] * 2, [slice(None)] * 2
    hi[axis], lo[axis] = slice(2 * r + 1, None), slice(0, -(2 * r + 1))
    return ((c[tuple(hi)] - c[tuple(lo)]) / (2 * r + 1)).astype(np.float32)


def blurf(a, r):
    r = max(1, int(r * .58))
    for _ in range(3):
        a = box(box(a, r, 0), r, 1)
    return a


def noise(h, w, scales, weights, seed):
    g = np.random.default_rng(seed)
    acc = np.zeros((h, w), np.float32)
    for s, wt in zip(scales, weights):
        small = g.random((h // s + 3, w // s + 3)).astype(np.float32)
        big = np.asarray(Image.fromarray((small * 255).astype(np.uint8)).resize(((w // s + 3) * s, (h // s + 3) * s), Image.BICUBIC), np.float32)[:h, :w] / 255
        acc += wt * big
    return acc


NZ = noise(H, W, (6, 22, 80), (.3, .4, .3), 3)
YY = np.arange(H, dtype=np.float32)[:, None]
XX = np.arange(W, dtype=np.float32)[None, :]


def mask_poly(pts):
    im = Image.new("L", (W, H), 0)
    ImageDraw.Draw(im).polygon(pts, fill=255)
    return np.asarray(im, np.float32) / 255


def mask_ell(box_):
    im = Image.new("L", (W, H), 0)
    ImageDraw.Draw(im).ellipse(box_, fill=255)
    return np.asarray(im, np.float32) / 255


def over(rgb, col, a):
    """rgb (H,W,3) ; col (H,W,3) or (3,) in 0..1 ; a (H,W) in 0..1"""
    return rgb * (1 - a[..., None]) + col * a[..., None]


def glow(rgb, x, y, r, color, amt):
    g = np.exp(-(((XX - x) ** 2) + ((YY - y) ** 2)) / (2 * r * r)).astype(np.float32) * amt
    return rgb + g[..., None] * (np.array(color, np.float32) / 255)


def lerp3(a, b, u):
    return np.array(a, np.float32) * (1 - u[..., None]) + np.array(b, np.float32) * u[..., None]


# ------------------------------------------------------------------ 2x vector layer
class Layer:
    def __init__(self):
        self.im = Image.new("RGBA", (W * SS, H * SS), (0, 0, 0, 0))
        self.d = ImageDraw.Draw(self.im)

    def _p(self, pts):
        return [(x * SS, y * SS) for x, y in pts]

    def poly(self, pts, fill):
        self.d.polygon(self._p(pts), fill=tuple(fill))

    def circ(self, x, y, r, fill):
        self.d.ellipse([(x - r) * SS, (y - r) * SS, (x + r) * SS, (y + r) * SS], fill=tuple(fill))

    def ell(self, x, y, rx, ry, fill, outline=None, width=0):
        self.d.ellipse([(x - rx) * SS, (y - ry) * SS, (x + rx) * SS, (y + ry) * SS], fill=tuple(fill) if fill else None,
                       outline=tuple(outline) if outline else None, width=int(width * SS))

    def line(self, pts, fill, width, joint=None):
        self.d.line(self._p(pts), fill=tuple(fill), width=max(1, int(width * SS)), joint=joint)

    def cap(self, p, q, w0, w1, fill):
        (x0, y0), (x1, y1) = p, q
        L = math.hypot(x1 - x0, y1 - y0) or 1
        nx, ny = -(y1 - y0) / L, (x1 - x0) / L
        self.poly([(x0 + nx * w0 / 2, y0 + ny * w0 / 2), (x1 + nx * w1 / 2, y1 + ny * w1 / 2),
                   (x1 - nx * w1 / 2, y1 - ny * w1 / 2), (x0 - nx * w0 / 2, y0 - ny * w0 / 2)], fill)
        self.circ(x0, y0, w0 / 2, fill)
        self.circ(x1, y1, w1 / 2, fill)

    def text(self, xy, s, f, fill, anchor="mm", stroke=0, stroke_fill=None):
        self.d.text((xy[0] * SS, xy[1] * SS), s, font=font(f[0], f[1] * SS), fill=tuple(fill), anchor=anchor,
                    stroke_width=int(stroke * SS), stroke_fill=tuple(stroke_fill) if stroke_fill else None)

    def to_np(self):
        a = np.asarray(self.im, np.float32) / 255
        alpha = a[..., 3:4]
        pm = a[..., :3] * alpha
        pm = pm.reshape(H, SS, W, SS, 3).mean(axis=(1, 3))
        al = alpha.reshape(H, SS, W, SS, 1).mean(axis=(1, 3))
        rgb = pm / np.maximum(al, 1e-4)
        return rgb, al[..., 0]


def stamp(rgb, layer):
    c, a = layer.to_np()
    return over(rgb, c, a)


# ------------------------------------------------------------------ background, ground, rocks
def background(glow_xy=(RX, GROUND - 330)):
    rgb = np.zeros((H, W, 3), np.float32)
    rgb += np.array([.012, .018, .034], np.float32) * (1 - YY / H)[..., None]
    rgb = glow(rgb, glow_xy[0], glow_xy[1], 430, (90, 120, 170), .12)
    xs = np.arange(W, dtype=np.float32)
    for off, amp, col, k in ((300, 1.0, (.04, .05, .08), 0), (230, .8, (.06, .075, .11), 1)):
        ridge = GROUND - off - 110 * amp * np.exp(-((xs - (200 + 400 * k)) / 230) ** 2) - 60 * np.sin(xs / (150 + 40 * k) + k) - 80 * np.exp(-((xs - (920 - 300 * k)) / 210) ** 2)
        m = ((YY > ridge[None, :]) & (YY < GROUND)).astype(np.float32)
        m = blurf(m, 2)
        top = np.clip((YY - ridge[None, :]) / 220, 0, 1)
        c = np.array(col, np.float32) * (1.25 - .5 * top[..., None])
        rgb = over(rgb, c, m)
    g = np.random.default_rng(5)
    for _ in range(70):
        x, y = g.uniform(0, W), g.uniform(60, GROUND - 450)
        rgb = glow(rgb, x, y, g.uniform(1.2, 2.2), (220, 230, 255), g.uniform(.12, .5))
    gm = (YY >= GROUND).astype(np.float32) * np.ones((1, W), np.float32)
    ground = np.array([.105, .12, .15], np.float32) * (1 - .55 * np.clip((YY - GROUND) / (H - GROUND), 0, 1))[..., None]
    ground = ground * (.92 + .16 * NZ[..., None])
    rgb = over(rgb, ground, gm)
    rgb = rgb + (np.exp(-np.abs(YY - GROUND) / 3.0) * (YY >= GROUND) * .12)[..., None] * np.array([.7, .8, 1], np.float32)
    return rgb


def shade_rock(m, dark=(.15, .18, .25), mid=(.36, .41, .51), light=(.68, .75, .86), moss=True):
    h = blurf(m, 26) * .55 + blurf(m, 90) * .45
    gy, gx = np.gradient(h)
    s = np.clip(.52 + (gx * .6 + gy * .8) * 55, 0, 1)
    sq = np.round(s * 4) / 4
    s = s * .4 + sq * .6
    u1, u2 = np.clip(s / .5, 0, 1), np.clip((s - .5) / .5, 0, 1)
    d_, m_, l_ = [np.array(c, np.float32) for c in (dark, mid, light)]
    col = (d_ * (1 - u1[..., None]) + m_ * u1[..., None]) * (1 - u2[..., None]) + (m_ * (1 - u2[..., None]) + l_ * u2[..., None]) * u2[..., None] if False else \
        np.where((s < .5)[..., None], d_ * (1 - u1[..., None]) + m_ * u1[..., None], m_ * (1 - u2[..., None]) + l_ * u2[..., None])
    col = col * (.9 + .2 * NZ[..., None])
    if moss:
        mo = blurf(np.clip((NZ - .5) * 5, 0, 1), 3) * np.clip((YY - (GROUND - 150)) / 70, 0, 1)
        col = col * (1 - mo[..., None] * .8) + np.array([.28, .52, .34], np.float32) * mo[..., None] * .8
    a = blurf(m, 1.2)
    edge = np.clip((1 - blurf(m, 5)) * 2.4, 0, 1) * m
    col = col * (1 - edge[..., None] * .75) + np.array([.07, .09, .13], np.float32) * edge[..., None] * .75
    return col, np.clip(a * 1.15, 0, 1)


_r0 = np.random.default_rng(21).random(400)
_k = 28
_RB = np.convolve(np.concatenate([_r0[-_k:], _r0, _r0[:_k]]), np.ones(_k) / _k, 'same')[_k:-_k]
_RB = (_RB - _RB.min()) / (_RB.max() - _RB.min())


def rock_mask(hole=0.0):
    pts = []
    for i, a in enumerate(np.linspace(0, 2 * math.pi, 120, endpoint=False)):
        rr = 1 + (_RB[int(i * 3.3)] - .5) * .18
        pts.append((RX + math.cos(a) * RW / 2 * rr, min(GROUND - RH * .5 + math.sin(a) * RH * .55 * rr, GROUND + 6)))
    m = mask_poly(pts)
    if hole > 0:
        m = m * (1 - mask_ell([RX - 40 * hole - 10, GROUND - RH - 6, RX + 40 * hole + 10, GROUND - RH + 160 * hole]))
    return m


def rock_top(m, x):
    col = np.nonzero(m[:, int(x)] > .5)[0]
    return int(col[0]) if len(col) else GROUND


def draw_overhang(rgb):
    pts = [(560, 0), (W, 0), (W, 620), (980, 560), (860, 545), (760, 520), (700, 500), (660, 470), (600, 420)]
    m = mask_poly(pts) * (YY > 330)
    c, a = shade_rock(m.astype(np.float32), dark=(.1, .12, .18), mid=(.24, .28, .36), light=(.45, .5, .62), moss=False)
    return over(rgb, c, a)


def draw_rock(rgb, m):
    c, a = shade_rock(m)
    return over(rgb, c, a)


def pebbles_and_grass(L, seed=2):
    g = np.random.default_rng(seed)
    for _ in range(26):
        x = g.uniform(30, W - 30)
        if RX - RW * .5 < x < RX + RW * .5:
            continue
        for k in range(3):
            L.poly([(x + k * 9 - 5, GROUND + 3), (x + k * 9 + g.uniform(-4, 4), GROUND - g.uniform(14, 30)), (x + k * 9 + 5, GROUND + 3)], (52, 96, 78, 255))
    for _ in range(10):
        x, y = g.uniform(40, W - 40), g.uniform(GROUND + 40, GROUND + 260)
        L.ell(x, y, g.uniform(8, 20), g.uniform(4, 9), (52, 58, 72, 255))


# ------------------------------------------------------------------ the boy
POSES = {
    "slash": dict(pelvis=(0, .34), neck=(.08, .60), tilt=.2, legF=[(.16, .27), (.29, .12)], legB=[(-.1, .25), (-.27, .19)],
                  armF=[(.2, .74), (.31, .88)], armB=[(.14, .75), (.27, .9)], expr="angry", wind=-1),
    "sit": dict(pelvis=(0, .1), neck=(-.05, .37), tilt=.35, legF=[(.2, .24), (.31, .03)], legB=[(.16, .22), (.27, .03)],
                armF=[(.05, .2), (.2, .29)], armB=[(.03, .24), (.18, .31)], expr="sulk", wind=1),
    "sleep": dict(pelvis=(0, .1), neck=(-.07, .37), tilt=-.55, legF=[(.22, .2), (.38, .03)], legB=[(.17, .18), (.34, .03)],
                  armF=[(.1, .2), (.2, .12)], armB=[(.05, .22), (.16, .13)], expr="sleep", wind=1),
    "amazed": dict(pelvis=(0, .34), neck=(-.01, .60), tilt=-.2, legF=[(.08, .18), (.11, .03)], legB=[(-.08, .18), (-.12, .03)],
                   armF=[(.13, .72), (.17, .93)], armB=[(-.14, .7), (-.2, .91)], expr="wow", wind=-1),
}


def unit(v):
    L = math.hypot(*v) or 1
    return (v[0] / L, v[1] / L)


def boy(L, p, ox, oy, s, face=1, ph=0.0):
    """Chibi boy. (ox, oy) = feet origin, s = body scale (full figure ~1.08*s)."""
    T = lambda q: (ox + q[0] * s * face, oy - q[1] * s)
    Pp, Nn = T(p["pelvis"]), T(p["neck"])
    a = p["tilt"] * face
    C = (Nn[0] + .21 * s * math.sin(a), Nn[1] - .21 * s * math.cos(a))
    r = .2 * s
    ca, sa = math.cos(a), math.sin(a)

    def hv(dx, dy):  # head frame: dx forward, dy down (in px)
        x, y = dx * face, dy
        return (C[0] + x * ca - y * sa, C[1] + x * sa + y * ca)

    # ground shadow
    L.ell(ox + .02 * s * face, oy + 6 if oy > GROUND - 5 else GROUND + 8, .38 * s, .05 * s, (0, 0, 0, 90))

    def sleeve(key, col):
        el, ha = T(p[key][0]), T(p[key][1])
        L.cap(Nn, el, .1 * s, .09 * s, col)
        L.cap(el, ha, .09 * s, .105 * s, col)
        L.circ(ha[0], ha[1], .052 * s, SKIN)

    def leg(key, col):
        kn, ft = T(p[key][0]), T(p[key][1])
        L.cap(Pp, kn, .1 * s, .09 * s, col)
        L.cap(kn, ft, .09 * s, .08 * s, col)
        L.ell(ft[0] + face * .035 * s, ft[1] + .012 * s, .085 * s, .045 * s, SHOE)
        L.ell(ft[0] + face * .035 * s, ft[1] + .035 * s, .085 * s, .014 * s, (150, 130, 100, 255))

    # back limbs
    sleeve("armB", ROBE_D)
    leg("legB", TROUSER_D)
    # robe
    d = unit((Pp[0] - Nn[0], Pp[1] - Nn[1]))
    n = (-d[1], d[0])
    mid = (Nn[0] + (Pp[0] - Nn[0]) * .6, Nn[1] + (Pp[1] - Nn[1]) * .6)
    hem = (Pp[0] + d[0] * .11 * s + p["wind"] * face * .05 * s + math.sin(ph) * .015 * s, Pp[1] + d[1] * .11 * s)
    pts = [(Nn[0] + n[0] * .105 * s, Nn[1] + n[1] * .105 * s), (Nn[0] - n[0] * .105 * s, Nn[1] - n[1] * .105 * s),
           (mid[0] - n[0] * .115 * s, mid[1] - n[1] * .115 * s), (hem[0] - n[0] * .15 * s, hem[1] - n[1] * .15 * s),
           (hem[0] + n[0] * .15 * s, hem[1] + n[1] * .15 * s), (mid[0] + n[0] * .115 * s, mid[1] + n[1] * .115 * s)]
    L.line(pts + [pts[0]], ROBE, .06 * s, joint="curve")
    L.poly(pts, ROBE)
    low = [pts[2], pts[3], pts[4], pts[5]]
    sh = [(mid[0] + (Pp[0] - mid[0]) * .35 + n[0] * k * .12 * s, mid[1] + (Pp[1] - mid[1]) * .35 + n[1] * k * .12 * s) for k in (-1, 1)]
    L.poly([sh[0], sh[1], low[2], low[1]], ROBE_D)
    L.line([low[1], low[2]], CREAM, .02 * s)  # hem trim
    waist = (Nn[0] + (Pp[0] - Nn[0]) * .78, Nn[1] + (Pp[1] - Nn[1]) * .78)
    L.line([(waist[0] - n[0] * .125 * s, waist[1] - n[1] * .125 * s), (waist[0] + n[0] * .125 * s, waist[1] + n[1] * .125 * s)], SASH, .05 * s)
    L.circ(waist[0] + n[0] * .06 * s * face, waist[1] + n[1] * .06 * s * face, .03 * s, (200, 150, 40, 255))
    L.poly([(Nn[0] + n[0] * .075 * s, Nn[1] + n[1] * .075 * s), (Nn[0] - n[0] * .075 * s, Nn[1] - n[1] * .075 * s), (Nn[0] + d[0] * .14 * s, Nn[1] + d[1] * .14 * s)], CREAM)
    # front limbs
    leg("legF", TROUSER)
    sleeve("armF", ROBE)

    # --- head ---
    # headband tails (behind)
    for k, (amp, ln) in enumerate(((.07, .5), (.05, .38))):
        pts = []
        for u in np.linspace(0, 1, 14):
            o = hv(-.17 * s - u * ln * s, -.1 * s + math.sin(u * 6 + k + ph) * amp * s * u + u * .06 * s * (k + 1))
            pts.append(o)
        for i in range(len(pts) - 1):
            w = (.05 - .035 * i / len(pts)) * s
            L.cap(pts[i], pts[i + 1], w, w * .9, RED + (255,))
    L.circ(*hv(-.07 * s, -(r + .02 * s)), .08 * s, HAIR + (255,))  # bun
    L.circ(*hv(-.09 * s, -(r + .045 * s)), .025 * s, HAIR_HL + (255,))
    L.circ(C[0], C[1], r * 1.03, HAIR + (255,))
    fc = hv(.015 * s, .012 * s)
    L.circ(fc[0], fc[1], r * .97, SKIN + (255,))
    rf = r * .97

    def fh(dx, dy):  # face-circle frame (fractions of rf)
        return hv(.015 * s + dx * rf, .012 * s + dy * rf)

    cap = [fh(math.cos(math.radians(th)) * 1.0, math.sin(math.radians(th)) * 1.0) for th in np.linspace(-8, -172, 22)]
    fringe = [(-.97, -.1), (-.78, .08), (-.55, -.04), (-.32, .26), (-.05, -.02), (.2, .3), (.45, .0), (.7, .2), (.95, -.04)]
    L.poly(cap + [fh(*q) for q in fringe], HAIR + (255,))
    L.line([fh(math.cos(math.radians(th)) * .82, math.sin(math.radians(th)) * .82) for th in np.linspace(-140, -75, 10)], HAIR_HL + (255,), .018 * s)
    # headband across forehead
    band = [fh(x, -.3 + .12 * (x * x) - .06 * x) for x in np.linspace(-.97, .95, 16)]
    L.line(band, RED + (255,), .045 * s, joint="curve")
    # face
    ex = (.4, .88)  # back eye, front eye (fraction of rf)
    ey = .2
    expr = p["expr"]
    dark = (30, 24, 34, 255)
    for k, x in enumerate(ex):
        cx, cy = fh(x, ey)
        if expr == "sleep":
            L.line([(cx - .03 * s, cy), (cx - .015 * s, cy + .014 * s), (cx + .015 * s, cy + .014 * s), (cx + .03 * s, cy)], dark, .011 * s)
        else:
            big = 1.25 if expr == "wow" else 1.0
            L.ell(cx, cy, .026 * s * big, .036 * s * big, dark)
            L.circ(cx - .008 * s, cy - .013 * s * big, .01 * s, (255, 255, 255, 255))
            L.circ(cx + .007 * s, cy + .012 * s, .005 * s, (255, 255, 255, 200))
        bx, by = fh(x, ey - .3)
        sg = 1 if k == 1 else -1
        if expr == "angry":
            L.line([(bx - .035 * s * sg * -1 * -1 + 0, by + (.02 if k == 1 else -.0) * s), (bx + .035 * s * (1 if k == 1 else -1) * -1, by - .0 * s)], dark, .014 * s)
        elif expr == "sulk":
            L.line([(bx - .03 * s, by + (.012 if k == 1 else -.012) * s), (bx + .03 * s, by + (-.012 if k == 1 else .012) * s)], dark, .012 * s)
        elif expr == "wow":
            L.line([hv(0, 0)] * 2, dark, 1) if False else None
            L.line([(bx - .03 * s, by - .018 * s), (bx, by - .03 * s), (bx + .03 * s, by - .018 * s)], dark, .012 * s, joint="curve")
        else:
            L.line([(bx - .03 * s, by), (bx + .03 * s, by - .005 * s)], dark, .011 * s)
        cb = fh(x + (.1 if k == 1 else -.12), ey + .42)
        L.ell(cb[0], cb[1], .03 * s, .017 * s, BLUSH + (110,))
    mx, my = fh(.66, .66)
    if expr == "angry":
        L.ell(mx, my, .03 * s, .03 * s, dark)
        L.ell(mx, my + .008 * s, .018 * s, .012 * s, (230, 90, 90, 255))
    elif expr == "sulk":
        L.line([(mx - .026 * s, my + .012 * s), (mx, my - .004 * s), (mx + .026 * s, my + .012 * s)], dark, .011 * s, joint="curve")
        tx, ty = fh(.9, ey + .55)
        L.poly([(tx, ty - .03 * s), (tx - .016 * s, ty + .008 * s), (tx + .016 * s, ty + .008 * s)], AQUA + (255,))
        L.circ(tx, ty + .008 * s, .016 * s, AQUA + (255,))
    elif expr == "sleep":
        L.ell(mx, my, .014 * s, .018 * s, dark)
        bx2, by2 = fh(1.18, .42)
        L.ell(bx2, by2, .05 * s, .05 * s, (190, 235, 250, 110), outline=(230, 250, 255, 230), width=.008 * s)
        L.circ(bx2 - .017 * s, by2 - .017 * s, .01 * s, (255, 255, 255, 230))
    elif expr == "wow":
        L.ell(mx, my + .004 * s, .024 * s, .034 * s, dark)
        L.ell(mx, my + .016 * s, .014 * s, .014 * s, (230, 90, 90, 255))
    return dict(head=C, r=r, hand=T(p["armF"][1]), hand2=T(p["armB"][1]), T=T)


# ------------------------------------------------------------------ props & effects
def sword(L, hand, ang, blade, snapped=True):
    hx, hy = hand
    ca, sa = math.cos(ang), math.sin(ang)
    nx, ny = -sa, ca
    # grip + pommel
    L.cap((hx - ca * 46, hy - sa * 46), (hx + ca * 6, hy + sa * 6), 17, 17, ROBE + (255,))
    L.circ(hx - ca * 52, hy - sa * 52, 11, SASH + (255,))
    # guard
    L.cap((hx + ca * 8 + nx * 30, hy + sa * 8 + ny * 30), (hx + ca * 8 - nx * 30, hy + sa * 8 - ny * 30), 12, 12, SASH + (255,))
    # blade (with jagged snapped end)
    pts = [(hx + ca * 12 + nx * 15, hy + sa * 12 + ny * 15), (hx + ca * blade + nx * 11, hy + sa * blade + ny * 11)]
    jag = [(.2, -.9), (.0, .2), (-.25, -.5), (-.5, .8), (-.7, -.2)] if snapped else [(0, 0)]
    for t_, o_ in jag:
        pts.append((hx + ca * (blade + t_ * 18) + nx * o_ * 11, hy + sa * (blade + t_ * 18) + ny * o_ * 11))
    pts += [(hx + ca * 12 - nx * 15, hy + sa * 12 - ny * 15)]
    L.poly(pts, STEEL + (255,))
    L.line([(hx + ca * 16 + nx * 4, hy + sa * 16 + ny * 4), (hx + ca * (blade - 10) + nx * 3, hy + sa * (blade - 10) + ny * 3)], (255, 255, 255, 230), 4)
    L.poly([(hx + ca * 12 - nx * 15, hy + sa * 12 - ny * 15), (hx + ca * (blade - 6) - nx * 10, hy + sa * (blade - 6) - ny * 10), (hx + ca * 12 - nx * 3, hy + sa * 12 - ny * 3)], STEEL_D + (255,))


def starburst(L, x, y, r1, r2, n, fill, rot=0.0):
    pts = []
    for i in range(n * 2):
        r = r1 if i % 2 == 0 else r2
        a = rot + i * math.pi / n
        pts.append((x + math.cos(a) * r, y + math.sin(a) * r))
    L.poly(pts, fill)


def water_drop(L, x, y, s, a=255):
    def shape(sc, dx=0, dy=0):
        r = .9 * s * sc
        tip = (x + dx, y + dy - 2.0 * s * sc)
        arc = [(x + dx + r * math.sin(th), y + dy - r * math.cos(th)) for th in np.linspace(math.radians(63.3), math.radians(296.7), 28)]
        return [tip] + arc
    L.poly(shape(1), AQUA_D + (a,))
    L.poly(shape(.8, -.06 * s, -.04 * s), AQUA + (a,))
    L.ell(x - .3 * s, y - .15 * s, .16 * s, .3 * s, AQUA_L + (a,))
    L.circ(x - .32 * s, y + .35 * s, .08 * s, (255, 255, 255, a))


def ring(L, x, y, rx, al, w=4):
    L.ell(x, y, rx, rx * .22, None, outline=AQUA + (int(al),), width=w)
    L.ell(x, y, rx * .8, rx * .22 * .8, None, outline=AQUA_L + (int(al * .6),), width=2)


def pop_text(L, s, xy, size, rot, fill, stroke_fill=(20, 10, 10, 255), font_=CAL):
    sub = Layer()
    sub.text(xy, s, (font_, size), fill, stroke=9, stroke_fill=stroke_fill)
    if rot:
        sub.im = sub.im.rotate(rot, center=(xy[0] * SS, xy[1] * SS), resample=Image.BICUBIC)
    L.im.alpha_composite(sub.im)


# ------------------------------------------------------------------ UI (no series line any more)
def seal_img(size):
    sl = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sl)
    sd.rounded_rectangle([0, 0, size - 1, size - 1], radius=size // 10, fill=RED + (240,))
    sd.text((size / 2, size * .52), "道", font=font(CAL, size * .75), fill=(28, 8, 6, 255), anchor="mm")
    return sl


def ui(img, shot, tcode, sub):
    im = img.convert("RGBA")
    d = ImageDraw.Draw(im)
    d.text((W / 2 - 40, 150), "水 与 石", font=font(CAL, 112), fill=IVORY + (255,), anchor="mm")
    im.alpha_composite(seal_img(78), (W // 2 + 170, 112))
    pa = np.zeros((360, W, 4), np.uint8)
    pa[..., 3] = (np.linspace(0, 1, 360)[:, None] ** .8 * 215).astype(np.uint8)
    im.alpha_composite(Image.fromarray(pa), (0, H - 360))
    d = ImageDraw.Draw(im)
    if sub:
        d.text((W / 2, H - 230), sub, font=font(SERIF, 50), fill=IVORY + (255,), anchor="mm")
    x0, x1, y = 90, W - 90, H - 120
    seg = (x1 - x0 - 48) / 5
    for k in range(5):
        a = x0 + k * (seg + 12)
        d.line([(a, y), (a + seg, y)], fill=(80, 76, 70, 255), width=6)
        if k < shot - 1:
            d.line([(a, y), (a + seg, y)], fill=GOLD + (255,), width=6)
        elif k == shot - 1:
            d.line([(a, y), (a + seg * .55, y)], fill=GOLD + (255,), width=6)
    d.text((x0, H - 78), "00:%02d" % tcode, font=font(SERIF, 30), fill=(150, 144, 130, 255), anchor="lm")
    d.text((x1, H - 78), "00:15", font=font(SERIF, 30), fill=(110, 105, 95, 255), anchor="rm")
    return im.convert("RGB")


def finish(rgb):
    yy, xx = np.ogrid[0:H, 0:W]
    vign = np.clip(1.2 - (np.hypot((xx - W / 2) / W, (yy - H / 2) / H) * 1.5) ** 2, 0, 1)
    out = np.clip(rgb * vign[..., None], 0, 1)
    return Image.fromarray((out * 255).astype(np.uint8))


# ------------------------------------------------------------------ shots
def shot1():
    rgb = background()
    m = rock_mask()
    rgb = draw_rock(rgb, m)
    ix, iy = RX - RW * .42, rock_top(m, RX - RW * .42) + 30
    rgb = glow(rgb, ix, iy, 90, GOLD, .9)
    L = Layer()
    pebbles_and_grass(L)
    # speed lines behind the boy
    for k, (yy_, ln) in enumerate(((GROUND - 260, 150), (GROUND - 330, 220), (GROUND - 190, 120), (GROUND - 420, 130))):
        L.line([(20, yy_), (20 + ln, yy_ - 6)], (255, 255, 255, 120), 6)
    info = boy(L, POSES["slash"], 175, GROUND - 90, 420, 1, 0.8)
    hx, hy = info["hand"]
    hx2, hy2 = info["hand2"]
    hand = ((hx + hx2) / 2, (hy + hy2) / 2)
    ang = math.atan2(iy - hand[1], ix - hand[0])
    sword(L, hand, ang, math.hypot(ix - hand[0], iy - hand[1]) + 6)
    # impact burst + sparks
    starburst(L, ix, iy, 80, 30, 9, (255, 246, 205, 255), .2)
    starburst(L, ix, iy, 48, 20, 9, (255, 255, 255, 255), .6)
    g = np.random.default_rng(8)
    for _ in range(20):
        a = g.uniform(-math.pi, .1)
        r0, r1 = g.uniform(60, 90), g.uniform(130, 230)
        L.line([(ix + math.cos(a) * r0, iy + math.sin(a) * r0), (ix + math.cos(a) * r1, iy + math.sin(a) * r1)], GOLD + (255,), g.uniform(4, 8))
    # broken tip flying away
    fx, fy = 640, 520
    tip = Layer()
    sword(tip, (fx, fy), math.radians(-35), 110, True)
    tip.im = tip.im.rotate(0)
    L.im.alpha_composite(tip.im)
    for k in range(3):
        L.d.arc([(fx - 150 - k * 22) * SS, (fy - 150 - k * 22) * SS, (fx + 150 + k * 22) * SS, (fy + 150 + k * 22) * SS], 150 + k * 8, 205 + k * 8, fill=(255, 255, 255, 150 - k * 40), width=4 * SS)
    pop_text(L, "铛！", (ix + 190, iy - 250), 190, 12, GOLD + (255,))
    rgb = stamp(rgb, L)
    return ui(finish(rgb), 1, 1, "石头挡路，少年拔剑就砍。")


def shot2():
    rgb = background()
    rgb = draw_overhang(rgb)
    m = rock_mask()
    rgb = draw_rock(rgb, m)
    top = rock_top(m, DRIP_X)
    rgb = glow(rgb, DRIP_X, top, 60, AQUA, .6)
    L = Layer()
    pebbles_and_grass(L)
    boy(L, POSES["sit"], RX - RW * .5 - 70, GROUND, 420, -1, 1.5)
    # broken sword on the ground
    sword(L, (150, GROUND - 14), math.radians(-3), 90, True)
    L.poly([(335, GROUND - 4), (420, GROUND - 14), (418, GROUND - 2)], STEEL + (255,))
    # drops
    water_drop(L, DRIP_X, 540, 14)
    water_drop(L, DRIP_X, 760, 18)
    for k in range(3):
        L.line([(DRIP_X, 690 - k * 40), (DRIP_X, 705 - k * 40)], AQUA_L + (int(160 - k * 50),), 5)
    ring(L, DRIP_X, top, 70, 230)
    ring(L, DRIP_X, top, 120, 120, 3)
    pop_text(L, "滴", (DRIP_X + 130, 700), 110, -8, AQUA_L + (255,), (10, 40, 55, 255))
    # sulking puff
    for k, (x, y, r_) in enumerate(((190, 900, 26), (150, 860, 18), (120, 830, 11))):
        L.circ(x, y, r_, (230, 230, 240, 90))
    pop_text(L, "哼", (225, 870), 70, 0, (200, 200, 215, 255), (20, 20, 30, 255))
    rgb = stamp(rgb, L)
    return ui(finish(rgb), 2, 4, "剑断了。只有一滴水，落在石头上。")


def shot3():
    rgb = background()
    cx, cy, R = W / 2, 980, 560
    rgb = draw_overhang(rgb)
    m = rock_mask(.8)
    rgb = draw_rock(rgb, m)
    top = GROUND - RH + 90
    rgb = glow(rgb, RX, top + 40, 70, AQUA, .8)
    L = Layer()
    for a in np.linspace(200, 340, 26):
        a0, a1 = math.radians(a), math.radians(a + 3)
        L.line([(cx + R * math.cos(a0), cy + R * math.sin(a0)), (cx + R * math.cos(a1), cy + R * math.sin(a1))], (160, 170, 195, 190), 4)
    sx, sy = cx + R * math.cos(math.radians(222)), cy + R * math.sin(math.radians(222))
    rgb = glow(rgb, sx, sy, 70, GOLD, .7)
    for k in range(12):  # sun rays
        a = k * math.pi / 6
        L.line([(sx + math.cos(a) * 46, sy + math.sin(a) * 46), (sx + math.cos(a) * 66, sy + math.sin(a) * 66)], GOLD + (255,), 6)
    L.circ(sx, sy, 36, GOLD + (255,))
    mx, my = cx + R * math.cos(math.radians(318)), cy + R * math.sin(math.radians(318))
    L.circ(mx, my, 34, IVORY + (255,))
    L.circ(mx + 16, my - 10, 30, (6, 8, 14, 255))
    pebbles_and_grass(L)
    for k, yv in enumerate(range(560, top - 30, 70)):
        water_drop(L, DRIP_X, yv, 10 + (k % 2) * 3, 235)
    ring(L, DRIP_X, top + 10, 60, 200, 3)
    for txt, x, y, al in (("+1 天", 800, 640, 240), ("+1 年", 560, 720, 220), ("+10 年", 830, 800, 200)):
        pop_text(L, txt, (x, y), 40, 0, GOLD + (al,), (20, 10, 5, 255), SERIF)
    boy(L, POSES["sleep"], RX - RW * .5 - 70, GROUND, 420, -1, 2.2)
    for zx, zy, zs in ((250, 1000, 44), (205, 940, 58), (150, 865, 74)):
        pop_text(L, "Z", (zx, zy), zs, 0, IVORY + (235,), (30, 40, 70, 255))
    rgb = stamp(rgb, L)
    return ui(finish(rgb), 3, 8, "一天，一年，十年……")


def shot4():
    rgb = background()
    rgb = draw_overhang(rgb)
    m = rock_mask(1.0)
    crack = RX + 18 * np.sin(YY / 23.0) + 10 * np.sign(np.sin(YY / 9.0))
    gap = 12
    left = m * (XX < crack - gap)
    right = m * (XX > crack + gap)

    def rot(mm, ang, c):
        return np.asarray(Image.fromarray((mm * 255).astype(np.uint8)).rotate(ang, center=c, resample=Image.BICUBIC), np.float32) / 255

    left, right = rot(left, 15, (RX - RW / 2, GROUND)), rot(right, -15, (RX + RW / 2, GROUND))
    # light pouring through the gap
    lit = blurf(m * (np.abs(XX - crack) < 70), 20)
    rgb = glow(rgb, RX, GROUND - 300, 170, AQUA, .8)
    rgb = over(rgb, np.array(AQUA_L, np.float32) / 255, np.clip(lit * .9, 0, 1) * np.exp(-((XX - RX) / 60) ** 2))
    rgb = draw_rock(rgb, left)
    rgb = draw_rock(rgb, right)
    L = Layer()
    pebbles_and_grass(L)
    # water gushing out and spreading
    for k, (dx, w) in enumerate(((0, 50), (-24, 24), (24, 24))):
        pts = [(RX + dx + math.sin(u * 5 + k) * 14 * (1 - u), GROUND - 430 + u * 450) for u in np.linspace(0, 1, 16)]
        for i in range(len(pts) - 1):
            L.cap(pts[i], pts[i + 1], w, w * 1.05, (AQUA if k == 0 else AQUA_D) + (235,))
    for i in range(5):
        L.line([(RX - 8 + i * 4, GROUND - 400 + i * 20), (RX - 6 + i * 3, GROUND - 40)], AQUA_L + (200,), 5)
    L.ell(RX, GROUND + 70, 330, 62, AQUA_D + (170,))
    L.ell(RX, GROUND + 64, 260, 44, AQUA + (190,))
    ring(L, RX, GROUND + 70, 330, 220)
    ring(L, RX, GROUND + 70, 230, 160, 3)
    g = np.random.default_rng(4)
    for k in range(10):
        cx_, cy_ = RX + g.uniform(-210, 210), GROUND - g.uniform(450, 740)
        sz, r_ = g.uniform(10, 24), g.uniform(0, 6)
        pts = [(sz, 0), (0, sz * .7), (-sz * .8, 0), (0, -sz)]
        L.poly([(cx_ + px * math.cos(r_) - py * math.sin(r_), cy_ + px * math.sin(r_) + py * math.cos(r_)) for px, py in pts], (150, 160, 180, 255))
    for k in range(3):
        a = math.radians(-130 + k * 32)
        L.line([(235 + math.cos(a) * 250, GROUND - 440 + math.sin(a) * 250), (235 + math.cos(a) * 310, GROUND - 440 + math.sin(a) * 310)], IVORY + (255,), 7)
    boy(L, POSES["amazed"], 235, GROUND, 420, 1, 0.5)
    pop_text(L, "咔！", (RX + 30, GROUND - 880), 200, -6, IVORY + (255,))
    rgb = stamp(rgb, L)
    return ui(finish(rgb), 4, 11, "石头，自己开了。")


def shot5():
    rgb = np.zeros((H, W, 3), np.float32) + (np.array([.012, .018, .034], np.float32) * (1 - YY / H)[..., None])
    rgb = glow(rgb, W / 2, 700, 300, AQUA, .22)
    L = Layer()
    water_drop(L, W / 2, 640, 36)
    for rx, al in ((120, 230), (200, 140), (290, 80)):
        ring(L, W / 2, 770, rx, al)
    rgb = glow(rgb, W / 2, 640, 80, AQUA, .6)
    for k, ch in enumerate("柔弱胜刚强"):
        L.text((W / 2 + (k - 2) * 182, 1010), ch, (CAL, 176), IVORY + (255,), stroke=0)
    L.im.alpha_composite(seal_img(120).rotate(-6, resample=Image.BICUBIC, expand=True).resize((int(130 * SS), int(130 * SS))), ((W - 230) * SS, 1080 * SS))
    rgb = stamp(rgb, L)
    img = finish(rgb)
    d = ImageDraw.Draw(img)
    d.text((W / 2, 1210), "天下莫柔弱于水，", font=font(SERIF, 42), fill=(205, 198, 182), anchor="mm")
    d.text((W / 2, 1275), "而攻坚强者莫之能胜。", font=font(SERIF, 42), fill=(205, 198, 182), anchor="mm")
    d.text((W / 2, 1365), "——《道德经》第七十八章", font=font(SERIF, 32), fill=(140, 134, 120), anchor="mm")
    return ui(img, 5, 14, None)


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
    sheet.save(os.path.join(HERE, "keyframes_v4.png"))
