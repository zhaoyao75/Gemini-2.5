"""《水与石》15s vertical SD video (540x960, 30fps) with sound.

Reuses the drawing primitives of render_stills_v3.py and animates them.
Usage:  python3 render_video_v3.py            -> demo_v3_15s_sd.mp4
        ONLY=1.0,4.7,10.1 python3 render_video_v3.py   -> test frames only (frames_v3/)
"""
import os, sys, math, wave, subprocess, shutil
from collections import OrderedDict
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render_stills_v3 as S

W, H, GROUND = S.W, S.H, S.GROUND
RX, RW, RH, DRIP_X = S.RX, S.RW, S.RH, S.DRIP_X
GOLD, IVORY, RED = S.GOLD, S.IVORY, S.RED
FPS, DUR = 30, 15.0
N = int(FPS * DUR)
OW, OH = 540, 960
BOUNDS = [0, 3, 6, 10, 12.5, 15]
FR_DIR = os.path.join(HERE, "frames_v3")


# ------------------------------------------------------------------ helpers
def clamp(x, a=0.0, b=1.0):
    return min(max(x, a), b)


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def ease_out(x):
    return 1 - (1 - clamp(x)) ** 3


def out_back(x):
    x = clamp(x)
    c1 = 1.70158
    return 1 + (c1 + 1) * (x - 1) ** 3 + c1 * (x - 1) ** 2


def lerp(a, b, u):
    return a + (b - a) * u


_FONTS = {}


def font(path, size):
    k = (path, int(size))
    if k not in _FONTS:
        _FONTS[k] = S.F(path, int(size))
    return _FONTS[k]


def comp(dst, src, x, y):
    """alpha_composite with clipping."""
    x, y = int(x), int(y)
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(src.width, dst.width - x), min(src.height, dst.height - y)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    dst.alpha_composite(src.crop((sx0, sy0, sx1, sy1)), (max(0, x), max(0, y)))


def pop_text(cv, text, x, y, size, rot, color, t, t0, dur, jitter=0.0, face=None):
    u = t - t0
    if u < 0 or u > dur:
        return
    sc = .55 + .5 * out_back(u / .18)
    a = 1 - ease((u - (dur - .3)) / .3) if u > dur - .3 else 1.0
    sz = int(size * sc)
    rr = rot + jitter * math.sin(u * 60) * (1 - clamp(u / .4))
    lay = Image.new("RGBA", (sz * 3, sz * 2), (0, 0, 0, 0))
    ImageDraw.Draw(lay).text((sz * 1.5, sz), text, font=font(face or S.CAL, sz), fill=tuple(color) + (int(255 * a),), anchor="mm")
    comp(cv.top, lay.rotate(rr, resample=Image.BICUBIC), x - sz * 1.5, y - sz)


def fade_text(cv, text, x, y, size, color, a, path=None):
    if a <= 0:
        return
    cv.d.text((x, y), text, font=font(path or S.SERIF, size), fill=tuple(color) + (int(255 * clamp(a)),), anchor="mm")


# ------------------------------------------------------------------ rocks / cached backgrounds
ROCK_BASE = S.noise2d(1, 400, (40,), (1.0,))[0]
_MASKS = {}


def rock_mask(hole=0.0):
    key = round(hole, 3)
    if key in _MASKS:
        return _MASKS[key]
    pts = []
    for i, a in enumerate(np.linspace(0, 2 * math.pi, 120, endpoint=False)):
        rr = 1 + (ROCK_BASE[int(i * 3.3)] - .5) * .18
        pts.append((RX + math.cos(a) * RW / 2 * rr, min(GROUND - RH * .5 + math.sin(a) * RH * .55 * rr, GROUND + 6)))
    m = S.mask_from(lambda d: d.polygon(pts, fill=255))
    if hole > 0:
        hm = S.mask_from(lambda d: d.ellipse([RX - 40 * hole - 10, GROUND - RH - 6, RX + 40 * hole + 10, GROUND - RH + 160 * hole], fill=255))
        m = m * (1 - hm)
    if len(_MASKS) > 6:
        _MASKS.pop(next(iter(_MASKS)))
    _MASKS[key] = m
    return m


_BASE = OrderedDict()


def base(kind, hole=0.0):
    """Cached static background -> (rgb, rock-top y at the drip column)."""
    key = (kind, round(hole, 2))
    if key in _BASE:
        _BASE.move_to_end(key)
        return _BASE[key]
    S.rng = np.random.default_rng(5)
    cv = S.Canvas()
    top = GROUND - RH
    if kind != "E":
        S.far_hills(cv, .12 if kind == "C" else .16)
        if kind in "BCD":
            S.overhang(cv)
        S.ground(cv)
        if kind in "ABC":
            m = rock_mask(hole)
            S.draw_rock(cv, m)
            top = S.rock_top_y(m, DRIP_X)
    _BASE[key] = (cv.rgb, top)
    if len(_BASE) > 4:
        _BASE.popitem(last=False)
    return _BASE[key]


def newcv(rgb):
    cv = S.Canvas.__new__(S.Canvas)
    cv.rgb = rgb.copy()
    cv.top = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cv.d = ImageDraw.Draw(cv.top)
    return cv


_m0 = rock_mask(0.0)
IMPACT = (RX - RW * .42, S.rock_top_y(_m0, RX - RW * .42) + 30)

# ------------------------------------------------------------------ poses
S.POSES["windup"] = dict(pelvis=(0, .46), neck=(.05, .74), head=(.1, .88), tilt=.15,
                         legF=[(.2, .34), (.12, .12)], legB=[(-.14, .3), (-.3, .18)],
                         armF=[(.04, .9), (-.1, 1.06)], armB=[(.02, .88), (-.16, 1.0)], brow="angry", robe_wind=-1)
S.POSES["dazed"] = dict(pelvis=(0, .44), neck=(-.05, .72), head=(-.08, .86), tilt=-.3,
                        legF=[(.1, .24), (.12, 0)], legB=[(-.06, .24), (-.1, 0)],
                        armF=[(.0, .6), (.05, .45)], armB=[(-.1, .62), (-.12, .46)], brow="sulk", robe_wind=1)


def lp(p, q, u):
    return (lerp(p[0], q[0], u), lerp(p[1], q[1], u))


def mix_pose(a, b, u):
    o = {}
    for k in ("pelvis", "neck", "head"):
        o[k] = lp(a[k], b[k], u)
    o["tilt"] = lerp(a["tilt"], b["tilt"], u)
    for k in ("legF", "legB", "armF", "armB"):
        o[k] = [lp(p, q, u) for p, q in zip(a[k], b[k])]
    src = b if u >= .5 else a
    o["brow"], o["robe_wind"] = src["brow"], src["robe_wind"]
    return o


def shifted(p, dy):
    o = dict(p)
    for k in ("pelvis", "neck", "head"):
        o[k] = (p[k][0], p[k][1] + dy)
    for k in ("legF", "legB", "armF", "armB"):
        o[k] = [(x, y + dy) for x, y in p[k]]
    return o


def run_pose(t):
    ph = t * 15
    legs = []
    for off in (0, math.pi):
        a = ph + off
        th = .8 * math.sin(a)
        knee = (.26 * math.sin(th), .46 - .26 * math.cos(th))
        ths = th - .9 * max(0.0, math.cos(a))
        foot = (knee[0] + .24 * math.sin(ths), knee[1] - .24 * math.cos(ths))
        legs.append([knee, foot])
    low = min(legs[0][1][1], legs[1][1][1])
    p = dict(S.POSES["windup"])
    p["legF"], p["legB"] = legs
    return shifted(p, -low)


def breathe(p, t, amp, speed):
    o = dict(p)
    o["neck"] = (p["neck"][0], p["neck"][1] + amp * math.sin(t * speed))
    o["head"] = (p["head"][0], p["head"][1] + amp * 1.3 * math.sin(t * speed + .3))
    return o


def youth(cv, p, ox, oy, s, face, ph):
    S.POSES["_t"] = p
    return S.draw_youth(cv, "_t", ox, oy, s, face, ph)


def draw_sword(d, hand, ang, bl):
    hx, hy = hand
    ca, sa = math.cos(ang), math.sin(ang)
    S.seg(d, (hx - ca * 40, hy - sa * 40), (hx, hy), 16, 16, RED + (255,))
    S.seg(d, (hx - 28 * sa, hy + 28 * ca), (hx + 28 * sa, hy - 28 * ca), 8, 8, GOLD + (255,))
    S.seg(d, (hx, hy), (hx + ca * bl, hy + sa * bl), 14, 11, (215, 215, 210, 255))


# ------------------------------------------------------------------ shot 1 : 0-3s
_rs = np.random.default_rng(8)
SP_A = _rs.uniform(-math.pi, .2, 18)
SP_R0 = _rs.uniform(20, 50, 18)
SP_R1 = _rs.uniform(100, 210, 18)
SP_W = _rs.uniform(3, 7, 18)
FLY_L = 1.4
FLY_G = 1500.0
FLY_XL = 360.0
FLY_A0 = -0.6


def scene1(t):
    t = clamp(t, 0, 3.0)
    cv = newcv(base("A")[0])
    d = cv.d
    ix, iy = IMPACT
    s = 400
    if t < .55:
        pose, ox, oy = run_pose(t), -140 + 200 * (t / .55), GROUND
    elif t < 1.0:
        u = (t - .55) / .45
        ox, oy = 60 + 155 * u, GROUND - 90 * ease(u) - 70 * math.sin(math.pi * u)
        pw = S.POSES["windup"]
        if t < .7:
            pose = mix_pose(run_pose(.55), pw, ease((t - .55) / .15))
        elif t < .8:
            pose = pw
        else:
            pose = mix_pose(pw, S.POSES["slash"], ease((t - .8) / .2))
    else:
        v = t - 1.0
        ox = 215 - 30 * ease_out(v / .3)
        oy = lerp(GROUND - 90, GROUND, clamp(v / .4) ** 2) + 8 * math.sin(v * 70) * (1 - clamp(v / .3))
        pose = mix_pose(S.POSES["slash"], S.POSES["dazed"], ease(v / .45))
    info = youth(cv, pose, ox, oy, s, 1, t * 9)
    hx, hy = info["hands"]
    a_imp = math.atan2(iy - hy, ix - hx)
    dist = math.hypot(ix - hx, iy - hy)
    a0 = math.atan2(-1, -.5)
    if t < .8:
        ang, bl = a0, 190
    elif t < 1.0:
        u = ease((t - .8) / .2)
        ang, bl = lerp(a0, a_imp, u), lerp(190, dist + 8, u)
    else:
        ang, bl = lerp(a_imp, math.pi / 2, ease((t - 1.1) / .5)), 55
    draw_sword(d, (hx, hy), ang, bl)

    if t >= 1.0:
        v = t - 1.0
        k = ease_out(v / .35)
        al = 1 - clamp((v - .12) / .38)
        cv.glow(ix, iy, 70 + 50 * k, GOLD, .9 * math.exp(-v * 5))
        if al > 0:
            for a, r0, r1, w in zip(SP_A, SP_R0, SP_R1, SP_W):
                head_r = r0 + (r1 - r0) * k
                tail_r = r0 + (r1 - r0) * max(0.0, k - .55)
                d.line([(ix + math.cos(a) * tail_r, iy + math.sin(a) * tail_r), (ix + math.cos(a) * head_r, iy + math.sin(a) * head_r)],
                       fill=GOLD + (int(255 * al),), width=int(w))
        # broken blade tumbling to the ground
        vx = (FLY_XL - ix) / FLY_L
        vy = ((GROUND - 12 - iy) - .5 * FLY_G * FLY_L ** 2) / FLY_L
        tau = min(v, FLY_L)
        fx, fy = ix + vx * tau, iy + vy * tau + .5 * FLY_G * tau * tau
        w_ = ((-0.1 - FLY_A0) - 2 * math.pi * 3) / FLY_L
        fa = FLY_A0 + w_ * tau
        S.seg(d, (fx - 75 * math.cos(fa), fy - 75 * math.sin(fa)), (fx + 75 * math.cos(fa), fy + 75 * math.sin(fa)), 11, 4, (215, 215, 210, 255))
        pop_text(cv, "铛！", ix + 170, iy - 220, 170, 12, GOLD, t, 1.0, 1.2, jitter=6)
        # dizzy stars
        if v > .5:
            hx2, hy2 = info["head"]
            r = info["r"]
            for k2 in range(3):
                a = t * 6 + k2 * 2.09
                px, py = hx2 + math.cos(a) * r * 1.7, hy2 - r * 1.7 + math.sin(a) * r * .45
                aa = int(255 * ease((v - .5) / .3))
                S.drop(d, px, py + 4, 6, GOLD + (aa,))
    return cv.flatten()


# ------------------------------------------------------------------ shot 2 : 3-6s
def sword_pieces(d):
    S.seg(d, (150, GROUND - 8), (230, GROUND - 14), 14, 14, RED + (255,))
    S.seg(d, (230, GROUND - 14), (300, GROUND - 18), 12, 10, (200, 200, 195, 255))
    S.seg(d, (330, GROUND - 6), (410, GROUND - 4), 9, 4, (200, 200, 195, 255))


def scene2(t):
    t = clamp(t, 3.0, 6.0)
    rgb, top = base("B")
    cv = newcv(rgb)
    d = cv.d
    sit = S.POSES["sit"]
    p = breathe(sit, t, .006, 2.5)
    if 3.25 < t < 3.65:
        u = (t - 3.25) / .4
        p = shifted(p, 0)
        p["neck"] = (p["neck"][0], p["neck"][1] + .014 * math.sin(u * 30) * (1 - u))
    youth(cv, p, RX - RW * .5 - 70, GROUND, 400, -1, t * 3)
    sword_pieces(d)
    # sulk puff
    u = t - 3.3
    if 0 < u < 1.2:
        a = ease(u / .2) * (1 - ease((u - .8) / .4))
        fade_text(cv, "哼", 180, 890 - 40 * u, 70, (170, 165, 150), a, S.CAL)

    # first drop forms, falls, splashes
    G = 3200.0
    t_rel = math.sqrt(2 * (top - 532) / G)
    t_fall, t_hit = 4.2, 4.2 + t_rel
    if t < t_fall:
        r = 6 + 10 * ease((t - 3.2) / 1.0)
        if t > 3.2:
            S.drop(d, DRIP_X + math.sin(t * 9) * .6, 516 + r * .9, r)
    elif t < t_hit:
        tau = t - t_fall
        y = 532 + .5 * G * tau * tau
        S.drop(d, DRIP_X, y, 18)
        for k in range(3):
            d.line([(DRIP_X, y - 60 - k * 40), (DRIP_X, y - 45 - k * 40)], fill=GOLD + (int((120 - k * 35) * clamp(tau / .15)),), width=4)
        cv.glow(DRIP_X, y, 40, GOLD, .35)
    else:
        v = t - t_hit
        cv.glow(DRIP_X, top, 55 + 40 * ease_out(v / .5), GOLD, .6 * math.exp(-v * 4))
        for rx0, delay, al0 in ((70, 0, 220), (125, .12, 140)):
            u = (v - delay) / .9
            if 0 < u < 1:
                rx = 20 + (rx0 - 20) * ease_out(u)
                d.ellipse([DRIP_X - rx, top - rx * .22, DRIP_X + rx, top + rx * .22], outline=GOLD + (int(al0 * (1 - u)),), width=3)
        for k in range(6):
            vx, vy = (k - 2.5) * 60, -380 - (k % 2) * 90
            if v < .45:
                S.drop(d, DRIP_X + vx * v, top + vy * v + 1100 * v * v, 4.5, GOLD + (int(255 * (1 - v / .45)),))
        pop_text(cv, "滴", DRIP_X + 120, 690, 100, -8, GOLD, t, t_hit, 1.0)
        if t > 5.1:  # next drop begins to form
            r = 6 + 6 * ease((t - 5.1) / .9)
            S.drop(d, DRIP_X, 516 + r * .9, r)
    return cv.flatten()


# ------------------------------------------------------------------ shot 3 : 6-10s
def scene3(t):
    t = clamp(t, 6.0, 10.0)
    hole = round(.9 * ease((t - 6.0) / 3.9) / .04) * .04
    rgb, top = base("C", hole)
    cv = newcv(rgb)
    d = cv.d
    cx, cy, R = W / 2, 980, 560
    fa = ease((t - 6.0) / .3)
    for a in np.linspace(200, 340, 26):
        a0, a1 = math.radians(a), math.radians(a + 3)
        d.line([(cx + R * math.cos(a0), cy + R * math.sin(a0)), (cx + R * math.cos(a1), cy + R * math.sin(a1))], fill=(140, 132, 115, int(200 * fa)), width=3)
    cyc = t - 6.0
    k, fr = int(cyc), cyc - int(cyc)
    if k > 3:
        k, fr = 3, 1.0
    ang = math.radians(200 + 140 * fr)
    bx, by = cx + R * math.cos(ang), cy + R * math.sin(ang)
    al = clamp(math.sin(math.pi * fr) * 2.2) * fa
    if al > 0:
        if k % 2 == 0:
            cv.glow(bx, by, 60, GOLD, .6 * al)
            d.ellipse([bx - 34, by - 34, bx + 34, by + 34], fill=GOLD + (int(255 * al),))
        else:
            d.ellipse([bx - 32, by - 32, bx + 32, by + 32], fill=IVORY + (int(255 * al),))
            d.ellipse([bx - 18, by - 40, bx + 46, by + 24], fill=(0, 0, 0, int(255 * al)))
    fade_text(cv, "日 → 月 → 日 → 月", cx, cy - R - 40, 30, (150, 144, 130), fa)

    cv.glow(DRIP_X, top + 40, 50 + 50 * hole, GOLD, .15 + .5 * hole)
    # drop slots (more drops as time passes)
    P = .55
    for k in range(6):
        t_on = 6.0 + k * .55
        if t < t_on:
            continue
        c = ((t - t_on) / P + k * .17) % 1
        a_in = clamp((t - t_on) / .3)
        if c < .35:
            S.drop(d, DRIP_X, 516 + (10 + 6 * ease(c / .35)) * .9, 10 + 6 * ease(c / .35), GOLD + (int(230 * a_in),))
        elif c < .82:
            y = 532 + (top - 532) * ((c - .35) / .47) ** 2
            S.drop(d, DRIP_X, y, 11 + (k % 2) * 3, GOLD + (int(230 * a_in),))
        else:
            u = (c - .82) / .18
            rx = 36 + 44 * u
            d.ellipse([DRIP_X - rx, top - rx * .22, DRIP_X + rx, top + rx * .22], outline=GOLD + (int(180 * (1 - u) * a_in),), width=3)
    for txt, x, y, t0 in (("+1 天", 800, 640, 6.4), ("+1 年", 560, 720, 7.2), ("+10 年", 820, 800, 8.4)):
        u = t - t0
        if 0 < u < 1.0:
            a = ease(u / .2) * (1 - ease((u - .6) / .4))
            fade_text(cv, txt, x, y - 30 * u, int(34 * (.8 + .3 * out_back(u / .25))), GOLD, a)
    # youth falls asleep against the rock
    p = mix_pose(S.POSES["sit"], S.POSES["sleep"], ease((t - 6.0) / .6))
    p = breathe(p, t, .008, 2.2)
    youth(cv, p, RX - RW * .5 - 70, GROUND, 400, -1, t * 2.2)
    for k in range(3):
        c = (t * .8 + k / 3) % 1
        a = math.sin(math.pi * c) * ease((t - 6.5) / .4)
        fade_text(cv, "Z", 260 - 110 * c, 1010 - 140 * c, int(40 + 30 * c), IVORY, a, S.CAL)
    return cv.flatten()


# ------------------------------------------------------------------ shot 4 : 10-12.5s
_XX = np.arange(W, dtype=np.float32)[None, :]
_CRACK = (RX + 18 * np.sin(np.arange(H) / 23.0) + 10 * np.sign(np.sin(np.arange(H) / 9.0))).astype(np.float32)[:, None]
_rc = np.random.default_rng(4)
CH_X = _rc.uniform(-70, 70, 9)
CH_Y = _rc.uniform(420, 700, 9)
CH_VX = _rc.uniform(-300, 300, 9)
CH_VY = _rc.uniform(-620, -150, 9)
CH_SZ = _rc.uniform(8, 20, 9)
CH_SP = _rc.uniform(-8, 8, 9)


def rot_mask(mm, a, c):
    im = Image.fromarray((mm * 255).astype(np.uint8)).rotate(a, center=c, resample=Image.BICUBIC)
    return np.asarray(im, np.float32) / 255


def scene4(t):
    t = clamp(t, 10.0, 12.5)
    tt = t - 10.0
    cv = newcv(base("D")[0])
    d = cv.d
    p = ease_out(tt / .45)
    gap = 2 + 10 * p
    m = rock_mask(1.0)
    left = rot_mask(m * (_XX < _CRACK - gap), 15 * p, (RX - RW / 2, GROUND))
    right = rot_mask(m * (_XX > _CRACK + gap), -15 * p, (RX + RW / 2, GROUND))
    S.draw_rock(cv, left, cun=False)
    S.draw_rock(cv, right, cun=False)
    cv.glow(RX, GROUND - 260, 150, GOLD, .45 * p)
    # water
    f = ease((t - 10.25) / .5)
    if f > 0:
        for k in range(5):
            y0 = GROUND - 420 + k * 18
            n = max(2, int(14 * f))
            pts = [(RX + math.sin(u * 6 + k + t * 5) * 22 * (1 - u), y0 + u * (440 - k * 18) * 1.0) for u in np.linspace(0, f, n)]
            S.stroke(d, pts, 3, 6, GOLD + (220 - k * 30,), 8)
    hw = 260 * ease((t - 10.6) / .8)
    if hw > 5:
        for k in range(4):
            y0 = GROUND + 40 + k * 34
            pts = [(RX - hw + u * 2 * hw, y0 + math.sin(u * 12 + k + t * 5) * 8) for u in np.linspace(0, 1, 24)]
            S.stroke(d, pts, 2, 2, GOLD + (200 - k * 40,), 5)
    # flying chips
    for i in range(9):
        x = RX + CH_X[i] + CH_VX[i] * tt
        y = GROUND - CH_Y[i] + CH_VY[i] * tt + 1400 * tt * tt * .5
        a = 255 * (1 - clamp((tt - 1.1) / .5))
        if a <= 0:
            continue
        sz, r = CH_SZ[i], CH_SP[i] * tt
        pts = [(sz, 0), (0, sz * .7), (-sz * .8, 0), (0, -sz)]
        pts = [(x + px * math.cos(r) - py * math.sin(r), y + px * math.sin(r) + py * math.cos(r)) for px, py in pts]
        d.polygon(pts, fill=(150, 146, 136, int(a)))
    pop_text(cv, "咔！", RX + 30, GROUND - 860, 190, -6, IVORY, t, 10.0, 1.6, jitter=5)
    # youth jumps in surprise
    hop = 55 * math.sin(math.pi * clamp((tt - .05) / .45))
    pose = mix_pose(S.POSES["dazed"], S.POSES["amazed"], ease_out((tt - .05) / .2))
    youth(cv, pose, 215, GROUND - hop, 400, 1, t * 5)
    ua = ease((tt - .15) / .15)
    if ua > 0:
        for k in range(3):
            a = math.radians(-120 + k * 30)
            r1, r2 = 250 + 30 * (1 - ua), 300 + 30 * (1 - ua)
            d.line([(215 + math.cos(a) * r1, GROUND - hop - 440 + math.sin(a) * r1), (215 + math.cos(a) * r2, GROUND - hop - 440 + math.sin(a) * r2)], fill=IVORY + (int(220 * ua),), width=6)
    img = cv.flatten()
    if t > 12.2:  # fade out into the last shot
        img = Image.blend(img, Image.new("RGBA", (W, H), (0, 0, 0, 255)), ease((t - 12.2) / .3))
    return img


# ------------------------------------------------------------------ shot 5 : 12.5-15s
_CH = {}


def char_mask(ch):
    if ch not in _CH:
        im = Image.new("L", (320, 360), 0)
        ImageDraw.Draw(im).text((160, 180), ch, font=font(S.CAL, 176), fill=255, anchor="mm")
        _CH[ch] = im
    return _CH[ch]


_SEAL = None


def seal_img():
    global _SEAL
    if _SEAL is None:
        sl = Image.new("RGBA", (120, 120), (0, 0, 0, 0))
        sd = ImageDraw.Draw(sl)
        sd.rounded_rectangle([0, 0, 119, 119], radius=10, fill=RED + (240,))
        sd.text((60, 62), "道", font=font(S.CAL, 90), fill=(28, 8, 6, 255), anchor="mm")
        _SEAL = sl.rotate(-6, resample=Image.BICUBIC, expand=True)
    return _SEAL


def scene5(t):
    t = clamp(t, 12.5, 15.0)
    cv = newcv(base("E")[0])
    d = cv.d
    cxm = W / 2
    # drop forms, falls, splashes into rings
    if t < 12.95:
        if t >= 12.55:
            if t < 12.75:
                sz, y = 34 * ease((t - 12.55) / .2), 420
            else:
                sz, y = 34, 420 + 340 * ((t - 12.75) / .2) ** 2
            if sz > 1:
                cv.glow(cxm, y, 70, GOLD, .5)
                S.drop(d, cxm, y, sz)
    else:
        v = t - 12.95
        cv.glow(cxm, 760, 90, GOLD, .6 * math.exp(-v * 5))
        for rx0, delay, al0 in ((120, 0, 200), (200, .1, 120), (290, .2, 60)):
            u = (v - delay) / .9
            if u > 0:
                rx = lerp(20, rx0, ease_out(u))
                al = min(255, al0 * (1 + 1.6 * (1 - ease_out(u))))
                d.ellipse([cxm - rx, 760 - rx * .2, cxm + rx, 760 + rx * .2], outline=GOLD + (int(al),), width=3)
    ea = ease((t - 13.15) / .4)
    if ea > 0:
        cv.glow(cxm, 640, 70, GOLD, .5 * ea)
        S.drop(d, cxm, 640, 34, GOLD + (int(255 * ea),))
    # calligraphy, one character at a time
    for k, ch in enumerate("柔弱胜刚强"):
        u = (t - (13.1 + k * .2)) / .35
        a = ease(u)
        if a <= 0:
            continue
        sc = 1.15 - .15 * ease_out(u)
        sz = (int(320 * sc), int(360 * sc))
        im = char_mask(ch).resize(sz, Image.BICUBIC)
        b = (1 - a) * 14
        if b > .4:
            im = im.filter(ImageFilter.GaussianBlur(b))
        al = im.point(lambda v, a=a: int(v * a))
        lay = Image.new("RGBA", sz, IVORY + (0,))
        lay.putalpha(al)
        comp(cv.top, lay, cxm + (k - 2) * 182 - sz[0] / 2, 1010 - sz[1] / 2)
    fade_text(cv, "天下莫柔弱于水，", cxm, 1210, 42, (205, 198, 182), ease((t - 13.9) / .3))
    fade_text(cv, "而攻坚强者莫之能胜。", cxm, 1275, 42, (205, 198, 182), ease((t - 14.05) / .3))
    fade_text(cv, "——《道德经》第七十八章", cxm, 1365, 32, (140, 134, 120), ease((t - 14.3) / .4))
    # seal stamp
    u = t - 14.0
    if u >= 0:
        sl = seal_img()
        sc = 1 + .8 * (1 - ease_out(u / .12))
        sz = (int(sl.width * sc), int(sl.height * sc))
        im = sl.resize(sz, Image.BICUBIC)
        im.putalpha(im.getchannel("A").point(lambda v, a=clamp(u / .06): int(v * a)))
        scx, scy = W - 230 + sl.width / 2, 1080 + sl.height / 2
        comp(cv.top, im, scx - sz[0] / 2, scy - sz[1] / 2)
        if u < .4:
            rr = 60 + 160 * ease_out(u / .35)
            d.ellipse([scx - rr, scy - rr * .5, scx + rr, scy + rr * .5], outline=RED + (int(170 * (1 - u / .4)),), width=3)
    return cv.flatten()


# ------------------------------------------------------------------ UI overlay (header / subtitles / progress)
SUBS = [(.25, 2.75, "石头挡路，少年拔剑就砍。"), (3.15, 5.85, "剑断了。只有一滴水，落在石头上。"),
        (6.15, 9.85, "一天，一年，十年……"), (10.35, 12.2, "石头，自己开了。")]
_UI = {}


def ui_static():
    if _UI:
        return _UI
    class U: pass
    u = U()
    u.top = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    u.d = ImageDraw.Draw(u.top)
    S.header(u)
    _UI["hdr"] = u.top
    pa = np.zeros((360, W, 4), np.uint8)
    pa[..., 3] = (np.linspace(0, 1, 360)[:, None] ** .8 * 215).astype(np.uint8)
    _UI["grad"] = Image.fromarray(pa)
    return _UI


def ui_layer(t):
    st = ui_static()
    ui = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ha = ease(t / .5)
    if ha < 1:
        h = st["hdr"].copy()
        h.putalpha(h.getchannel("A").point(lambda v: int(v * ha)))
        ui.alpha_composite(h)
    else:
        ui.alpha_composite(st["hdr"])
    ui.alpha_composite(st["grad"], (0, H - 360))
    d = ImageDraw.Draw(ui)
    for t0, t1, txt in SUBS:
        if t0 <= t <= t1:
            n = int(clamp((t - t0) / .07, 0, len(txt)) + 1)
            a = min(ease((t - t0) / .25), ease((t1 - t) / .25))
            d.text((W / 2, H - 230 + (1 - a) * 14), txt[:n], font=font(S.SERIF, 50), fill=IVORY + (int(255 * a),), anchor="mm")
    x0, x1, y = 90, W - 90, H - 120
    seg_w = (x1 - x0 - 4 * 12) / 5
    for k in range(5):
        a = x0 + k * (seg_w + 12)
        d.line([(a, y), (a + seg_w, y)], fill=(80, 76, 70, 255), width=6)
        fr = clamp((t - BOUNDS[k]) / (BOUNDS[k + 1] - BOUNDS[k]))
        if fr > 0:
            d.line([(a, y), (a + seg_w * fr, y)], fill=GOLD + (255,), width=6)
    d.text((x0, H - 78), "00:%02d" % int(t), font=font(S.SERIF, 30), fill=(150, 144, 130, 255), anchor="lm")
    d.text((x1, H - 78), "00:15", font=font(S.SERIF, 30), fill=(110, 105, 95, 255), anchor="rm")
    return ui


# ------------------------------------------------------------------ compose
def shake(t):
    dx = dy = 0.0
    for t0, amp, dur in ((1.0, 12, .3), (10.0, 14, .35), (14.0, 9, .18)):
        u = (t - t0) / dur
        if 0 <= u < 1:
            dx += amp * (1 - u) * math.sin(t * 95 + 1.3)
            dy += amp * (1 - u) * math.sin(t * 79)
    if 9.4 < t < 10.0:
        amp = 1 + 4 * (t - 9.4) / .6
        dx += amp * math.sin(t * 120)
        dy += amp * .6 * math.sin(t * 97)
    return int(dx), int(dy)


def scene_img(t):
    if t < 3.0:
        img = scene1(t)
        if t > 2.7:
            img = Image.blend(img, scene2(3.0), ease((t - 2.7) / .3))
        return img
    if t < 6.0:
        return scene2(t)
    if t < 10.0:
        return scene3(t)
    if t < 12.5:
        return scene4(t)
    return scene5(t)


_GR = np.random.default_rng(1).normal(0, 2.5, (8, OH, OW, 1)).astype(np.float32)


def render_frame(i):
    t = i / FPS
    sc = scene_img(t)
    dx, dy = shake(t)
    if dx or dy:
        bg = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        bg.paste(sc, (dx, dy))
        sc = bg
    if 10.0 <= t < 10.15:
        fl = Image.new("RGBA", (W, H), (255, 244, 215, int(215 * (1 - (t - 10.0) / .15))))
        sc.alpha_composite(fl)
    sc.alpha_composite(ui_layer(t))
    im = sc.convert("RGB").resize((OW, OH), Image.LANCZOS)
    arr = np.asarray(im, np.float32) + _GR[i % 8]
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(os.path.join(FR_DIR, f"{i:04d}.png"))
    return i


# ------------------------------------------------------------------ audio
SR = 44100
NS = int(SR * DUR)
rs = np.random.default_rng(99)
BUF = np.zeros(NS, np.float32)


def tt(d):
    return np.arange(int(SR * d)) / SR


def nz(d):
    return rs.normal(0, 1, int(SR * d)).astype(np.float32)


def sm(x, w):
    return np.convolve(x, np.ones(w) / w, "same")


def put(t0, sig, g=1.0):
    i = int(t0 * SR)
    if i >= NS:
        return
    n = min(len(sig), NS - i)
    BUF[i:i + n] += sig[:n].astype(np.float32) * g


def plop(f0=500, f1=700, dur=.35, k=18):
    t = tt(dur)
    ph = 2 * np.pi * (f0 * t + f1 * (1 - np.exp(-35 * t)) / 35)
    return np.sin(ph) * np.exp(-t * k)


def pluck(f, dur=2.2, decay=2.2):
    t = tt(dur)
    s = sum(np.sin(2 * np.pi * f * h * t + h) * np.exp(-t * (decay + h * 1.3)) / h ** 1.25 for h in range(1, 7))
    s = s + nz(dur) * np.exp(-t * 90) * .25
    return s * np.clip(t / .004, 0, 1)


def build_audio():
    t = tt(DUR)
    BUF[:] = (.05 * np.sin(2 * np.pi * 55 * t) + .03 * np.sin(2 * np.pi * 82.5 * t)) * np.clip(t / .6, 0, 1)
    BUF[:] += sm(nz(DUR), 300) * 3.5 * (.5 + .5 * np.sin(2 * np.pi * .2 * t)) * .03
    # shot 1
    for k in range(4):
        d_ = nz(.08) * np.exp(-tt(.08) * 60)
        put(.08 + k * .14, sm(d_, 30), .35)
    sw = sm(nz(.25), 40) * np.sin(np.linspace(0, np.pi, int(SR * .25))) ** 2
    put(.78, sw * 6, .4)
    tc = tt(1.2)
    clang = sum(a * np.sin(2 * np.pi * f * tc) * np.exp(-tc * k) for f, a, k in [(620, .4, 5), (1240, .5, 7), (1870, .35, 9), (2790, .3, 13), (4150, .2, 20)]) + nz(1.2) * np.exp(-tc * 80) * .6
    put(1.0, clang, .55)
    put(1.0, sm(nz(.4), 6) * np.exp(-tt(.4) * 12) * 3, .4)
    put(1.35, np.sin(2 * np.pi * 90 * tt(.4)) * np.exp(-tt(.4) * 18), .5)
    put(1.1, sm(nz(1.3), 50) * 5 * np.exp(-tt(1.3) * 3), .12)
    for tl, f in ((2.4, 3100), (2.52, 2300), (2.62, 3900)):
        put(tl, np.sin(2 * np.pi * f * tt(.3)) * np.exp(-tt(.3) * 25), .22)
    # shot 2
    put(4.2 + math.sqrt(2 * (2.0 * 130) / 3200) if False else 4.62, plop(500, 800, .5, 13), .55)
    put(5.9, plop(560, 600, .3, 20), .15)
    # shot 3: accelerating drips, swelling pad, rumble
    tdr, step = 6.15, .5
    while tdr < 9.9:
        f0 = rs.uniform(500, 800)
        put(tdr, plop(f0, rs.uniform(500, 900), .3, 22), .18 + .22 * (tdr - 6) / 4)
        tdr += step
        step = max(.14, step * .9)
    pad = sum(np.sin(2 * np.pi * f * t) * a for f, a in ((110, .5), (164.8, .3), (220, .2), (329.6, .12)))
    env = np.clip((t - 6) / 2, 0, 1) * np.clip((10.0 - t) / .15, 0, 1) * (t >= 6)
    BUF[:] += (pad * env * (1 + .15 * np.sin(2 * np.pi * 5 * t)) * .12).astype(np.float32)
    put(9.3, sm(nz(.75), 200) * 20 * np.linspace(0, 1, int(SR * .75)) ** 2, .35)
    # shot 4: crack, debris, water
    put(10.0, np.sin(2 * np.pi * 55 * tt(1.2) * 1.0) * np.exp(-tt(1.2) * 5), .9)
    put(10.0, sm(nz(.7), 12) * np.exp(-tt(.7) * 6) * 6, .8)
    put(10.0, np.sin(2 * np.pi * 1800 * tt(.1)) * np.exp(-tt(.1) * 50), .3)
    for _ in range(14):
        ts = rs.uniform(10.05, 11.4)
        put(ts, np.sin(2 * np.pi * rs.uniform(700, 2200) * tt(.06)) * np.exp(-tt(.06) * 70), rs.uniform(.08, .2))
    n = nz(2.6)
    fl = sm(n, 4) - sm(n, 90)
    fl = fl / np.abs(fl).max() * (.6 + .4 * sm(nz(2.6), 3000) * 40)
    ev = np.clip(tt(2.6) / .6, 0, 1) * np.clip((2.6 - tt(2.6)) / .4, 0, 1)
    put(10.25, fl * ev, .3)
    # shot 5
    put(12.95, plop(420, 900, .8, 9), .6)
    for k, f in enumerate((293.7, 330, 370, 440, 587.3)):
        put(13.1 + k * .2 + .1, pluck(f, 1.6, 2.6), .22)
    put(14.0, np.sin(2 * np.pi * 70 * tt(1.0)) * np.exp(-tt(1.0) * 6), .7)
    put(14.0, pluck(146.8, 1.0, 1.8), .5)
    BUF[:] *= (np.clip(t / .3, 0, 1) * np.clip((DUR - t) / .4, 0, 1)).astype(np.float32)
    out = BUF / max(1e-6, np.abs(BUF).max()) * .85
    path = os.path.join(HERE, "audio_v3.wav")
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((out * 32767).astype(np.int16).tobytes())
    return path


if __name__ == "__main__":
    shutil.rmtree(FR_DIR, ignore_errors=True)
    os.makedirs(FR_DIR)
    only = os.environ.get("ONLY")
    idx = [int(round(float(x) * FPS)) for x in only.split(",")] if only else list(range(N))
    done = 0
    with Pool(4) as pool:
        for _ in pool.imap(render_frame, idx, chunksize=6):
            done += 1
            print(f"\rframe {done}/{len(idx)}", end="", flush=True)
    print()
    if only:
        sys.exit(0)
    wav = build_audio()
    out = os.path.join(HERE, "demo_v3_15s_sd.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(FR_DIR, "%04d.png"), "-i", wav,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-c:a", "aac", "-b:a", "128k", "-shortest", out], check=True)
    print("wrote", out)
