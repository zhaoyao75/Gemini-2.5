"""《水与石》12s vertical SD video (540x960, 30fps) with sound effects only (no voice-over).

Animates the v5 still-frame look (render_stills_v5.py).
Usage:  python3 render_video_v5.py                  -> demo_v5_12s_sd.mp4
        ONLY=1.0,3.4,5.5 python3 render_video_v5.py -> test frames only (frames_v5/)
"""
import os, sys, math, wave, subprocess, shutil
from collections import OrderedDict
from multiprocessing import Pool
import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import render_stills_v5 as S
from render_stills_v5 import W, H, SS, GROUND, RX, RW, RH, DRIP_X, GOLD, IVORY, RED, AQUA, AQUA_D, AQUA_L, STEEL

FPS, DUR = 30, 12.0
N = int(FPS * DUR)
OW, OH = 540, 960
BOUNDS = [0, 2.0, 4.0, 7.5, 9.5, 12.0]
FR_DIR = os.path.join(HERE, "frames_v5")


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


def comp(dst, src, x, y):
    x, y = int(x), int(y)
    sx0, sy0 = max(0, -x), max(0, -y)
    sx1, sy1 = min(src.width, dst.width - x), min(src.height, dst.height - y)
    if sx1 <= sx0 or sy1 <= sy0:
        return
    dst.alpha_composite(src.crop((sx0, sy0, sx1, sy1)), (max(0, x), max(0, y)))


def pop(L, text, x, y, size, rot, fill, t, t0, dur, stroke_fill=(20, 10, 10, 255), font_=None, jitter=0.0):
    """Comic pop-up text on a 2x layer: overshoot scale-in, fade-out in the last .25s."""
    u = t - t0
    if u < 0 or u > dur:
        return
    sc = .55 + .5 * out_back(u / .18)
    a = 1 - ease((u - (dur - .25)) / .25) if u > dur - .25 else 1.0
    sz = int(size * sc)
    pad = int(sz * 1.7)
    sub = Image.new("RGBA", (2 * pad * SS, 2 * pad * SS), (0, 0, 0, 0))
    ImageDraw.Draw(sub).text((pad * SS, pad * SS), text, font=S.font(font_ or S.CAL, sz * SS), anchor="mm",
                             fill=tuple(fill[:3]) + (int(fill[3] * a),), stroke_width=9 * SS,
                             stroke_fill=tuple(stroke_fill[:3]) + (int(stroke_fill[3] * a),))
    rr = rot + jitter * math.sin(u * 60) * (1 - clamp(u / .4))
    if rr:
        sub = sub.rotate(rr, resample=Image.BICUBIC)
    comp(L.im, sub, (x - pad) * SS, (y - pad) * SS)


# ------------------------------------------------------------------ poses
S.POSES["windup"] = dict(pelvis=(0, .34), neck=(.05, .60), tilt=.1, legF=[(.14, .27), (.2, .1)], legB=[(-.1, .25), (-.22, .14)],
                         armF=[(.0, .74), (-.12, .93)], armB=[(.03, .73), (-.17, .87)], expr="angry", wind=-1)
S.POSES["dazed"] = dict(pelvis=(0, .34), neck=(-.03, .58), tilt=-.1, legF=[(.08, .2), (.1, .03)], legB=[(-.08, .2), (-.1, .03)],
                        armF=[(.0, .42), (.04, .26)], armB=[(-.1, .44), (-.12, .28)], expr="sulk", wind=1)


def lp(p, q, u):
    return (lerp(p[0], q[0], u), lerp(p[1], q[1], u))


def mix_pose(a, b, u):
    o = {"pelvis": lp(a["pelvis"], b["pelvis"], u), "neck": lp(a["neck"], b["neck"], u), "tilt": lerp(a["tilt"], b["tilt"], u)}
    for k in ("legF", "legB", "armF", "armB"):
        o[k] = [lp(p, q, u) for p, q in zip(a[k], b[k])]
    src = b if u >= .5 else a
    o["expr"], o["wind"] = src["expr"], src["wind"]
    return o


def shifted(p, dy):
    o = dict(p)
    for k in ("pelvis", "neck"):
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
        knee = (.16 * math.sin(th), .34 - .16 * math.cos(th))
        ths = th - .9 * max(0.0, math.cos(a))
        legs.append([knee, (knee[0] + .16 * math.sin(ths), knee[1] - .16 * math.cos(ths))])
    low = min(legs[0][1][1], legs[1][1][1])
    p = dict(S.POSES["windup"])
    p["legF"], p["legB"] = legs
    return shifted(p, .03 - low)


def breathe(p, t, amp, speed):
    o = dict(p)
    o["neck"] = (p["neck"][0], p["neck"][1] + amp * math.sin(t * speed))
    return o


def blade_piece(L, x, y, ang, ln=120):
    ca, sa = math.cos(ang), math.sin(ang)
    loc = [(-ln / 2, 13), (ln / 2 - 10, 10), (ln / 2 + 30, 0), (ln / 2 - 10, -10), (-ln / 2, -13), (-ln / 2 + 8, -6), (-ln / 2 - 8, 0), (-ln / 2 + 10, 7)]
    L.poly([(x + u * ca - v * sa, y + u * sa + v * ca) for u, v in loc], STEEL + (255,))
    L.line([(x - ca * ln / 3 - sa * 4, y - sa * ln / 3 + ca * 4), (x + ca * ln / 3 - sa * 3, y + sa * ln / 3 + ca * 3)], (255, 255, 255, 230), 4)


# ------------------------------------------------------------------ cached backgrounds
_BG = []
_BASE = OrderedDict()


def bg0():
    if not _BG:
        _BG.append(S.background())
    return _BG[0]


def base(kind, a=0.0):
    key = (kind, round(a, 2))
    if key in _BASE:
        _BASE.move_to_end(key)
        return _BASE[key]
    rgb = bg0()
    if kind == "A":
        m = S.rock_mask()
        val = (S.draw_rock(rgb, m), m)
    elif kind == "B":
        m = S.rock_mask()
        val = (S.draw_rock(S.draw_overhang(rgb), m), m)
    elif kind == "C":
        m = S.rock_mask(a)
        val = (S.draw_rock(S.draw_overhang(rgb), m), m)
    elif kind == "D":  # cracking rock, a = opening progress 0..1
        rgb = S.draw_overhang(rgb)
        m = S.rock_mask(1.0)
        crack = RX + 18 * np.sin(S.YY / 23.0) + 10 * np.sign(np.sin(S.YY / 9.0))
        gap = 2 + 10 * a
        rot = lambda mm, ang, c: np.asarray(Image.fromarray((mm * 255).astype(np.uint8)).rotate(ang, center=c, resample=Image.BICUBIC), np.float32) / 255
        left = rot(m * (S.XX < crack - gap), 15 * a, (RX - RW / 2, GROUND))
        right = rot(m * (S.XX > crack + gap), -15 * a, (RX + RW / 2, GROUND))
        lit = S.blurf(m * (np.abs(S.XX - crack) < 70), 20)
        rgb = S.glow(rgb, RX, GROUND - 300, 170, AQUA, .8 * a)
        rgb = S.over(rgb, np.array(AQUA_L, np.float32) / 255, np.clip(lit * .9, 0, 1) * np.exp(-((S.XX - RX) / 60) ** 2) * a)
        rgb = S.draw_rock(rgb, left)
        rgb = S.draw_rock(rgb, right, shadow=False)
        val = (rgb, (left, right))
    else:  # "E": plain dark gradient for the last shot
        rgb = np.zeros((H, W, 3), np.float32) + (np.array([.012, .018, .034], np.float32) * (1 - S.YY / H)[..., None])
        val = (S.glow(rgb, W / 2, 700, 300, AQUA, .22), None)
    _BASE[key] = val
    if len(_BASE) > 4:
        _BASE.popitem(last=False)
    return val


_m0 = S.rock_mask()
_IY = GROUND - 300
IMPACT = (float(np.nonzero(_m0[_IY] > .5)[0][0]) + 6, _IY)
FLY_L, FLY_G, FLY_XL, FLY_A0 = .85, 2200.0, 320.0, -0.6


# ------------------------------------------------------------------ shot 1 : 0-2s
_g = np.random.default_rng(8)
SP_A, SP_R0, SP_R1, SP_W = _g.uniform(-math.pi, .1, 14), _g.uniform(36, 56, 14), _g.uniform(95, 170, 14), _g.uniform(3, 6, 14)


def scene1(t):
    t = clamp(t, 0, 2.0)
    rgb, m = base("A")
    ix, iy = IMPACT
    v = t - 1.0
    if v >= 0:
        rgb = S.glow(rgb, ix, iy, 55 + 25 * ease_out(v / .3), GOLD, .5 * math.exp(-v * 7))
    L = S.Layer()
    S.rock_details(L, m)
    S.pebbles_and_grass(L)
    s = 420
    if t < .55:
        pose, ox, oy = run_pose(t), -160 + 210 * (t / .55), GROUND
    elif t < 1.0:
        u = (t - .55) / .45
        ox, oy = 50 + 100 * u, GROUND - 90 * ease(u) - 80 * math.sin(math.pi * u)
        pw = S.POSES["windup"]
        if t < .7:
            pose = mix_pose(run_pose(.55), pw, ease((t - .55) / .15))
        elif t < .8:
            pose = pw
        else:
            pose = mix_pose(pw, S.POSES["slash"], ease((t - .8) / .2))
    else:
        ox = 150 - 30 * ease_out(v / .3)
        oy = lerp(GROUND - 90, GROUND, clamp(v / .4) ** 2) + 8 * math.sin(v * 70) * (1 - clamp(v / .3))
        pose = mix_pose(S.POSES["slash"], S.POSES["dazed"], ease(v / .4))
    if t < 1.0:  # speed lines behind the boy
        sp = ease(t / .15) * (1 - ease((t - .8) / .2))
        for dy_, ln in ((-260, 150), (-330, 220), (-190, 120), (-420, 130)):
            L.line([(ox - 150 - ln * sp, GROUND + dy_), (ox - 150, GROUND + dy_ - 6)], (255, 255, 255, int(120 * sp)), 6)
    info = S.boy(L, pose, ox, oy, s, 1, t * 9)
    hand = ((info["hand"][0] + info["hand2"][0]) / 2, (info["hand"][1] + info["hand2"][1]) / 2)
    a_imp = math.atan2(iy - hand[1], ix - hand[0])
    dist = math.hypot(ix - hand[0], iy - hand[1])
    a0 = math.atan2(-1, -.5)
    if t < .8:
        ang, bl = a0, 190
    elif t < 1.0:
        u = ease((t - .8) / .2)
        ang, bl = lerp(a0, a_imp, u), lerp(190, dist + 6, u)
    else:
        ang, bl = lerp(a_imp, math.pi / 2, ease((t - 1.1) / .5)), 55
    S.sword(L, hand, ang, bl, snapped=(t >= 1.0))
    if v >= 0:
        k = ease_out(v / .15)
        al = 1 - clamp(v / .25)
        if al > 0:
            S.starburst(L, ix, iy, 52 * (.7 + .5 * k), 20, 9, (255, 246, 205, int(255 * al)), .2)
            S.starburst(L, ix, iy, 30 * (.7 + .5 * k), 12, 9, (255, 255, 255, int(255 * al)), .6)
        kk = ease_out(v / .35)
        sa = 1 - clamp((v - .12) / .38)
        if sa > 0:
            for a, r0, r1, w in zip(SP_A, SP_R0, SP_R1, SP_W):
                hr = r0 + (r1 - r0) * kk
                tr = r0 + (r1 - r0) * max(0.0, kk - .55)
                L.line([(ix + math.cos(a) * tr, iy + math.sin(a) * tr), (ix + math.cos(a) * hr, iy + math.sin(a) * hr)], GOLD + (int(255 * sa),), w)
        vx = (FLY_XL - ix) / FLY_L
        vy = ((GROUND - 12 - iy) - .5 * FLY_G * FLY_L ** 2) / FLY_L
        tau = min(v, FLY_L)
        fx, fy = ix + vx * tau, iy + vy * tau + .5 * FLY_G * tau * tau
        fa = FLY_A0 + (((-0.1 - FLY_A0) - 2 * math.pi * 2) / FLY_L) * tau
        blade_piece(L, fx, fy, fa, 120)
        pop(L, "铛！", ix + 200, iy - 260, 190, 12, GOLD + (255,), t, 1.0, 1.0, jitter=6)
        if v > .4:
            hx2, hy2 = info["head"]
            r = info["r"]
            for k2 in range(3):
                a = t * 7 + k2 * 2.09
                px, py = hx2 + math.cos(a) * r * 1.6, hy2 - r * 1.5 + math.sin(a) * r * .4
                S.starburst(L, px, py, 12, 5, 5, GOLD + (int(255 * ease((v - .4) / .2)),), a)
    return S.finish(S.stamp(rgb, L))


# ------------------------------------------------------------------ shot 2 : 2-4s
def scene2(t):
    t = clamp(t, 2.0, 4.0)
    rgb, m = base("B")
    top = S.rock_top(m, DRIP_X)
    G = 3200.0
    t_fall = 2.9
    t_hit = t_fall + math.sqrt(2 * (top - 532) / G)
    L = S.Layer()
    S.rock_details(L, m)
    S.pebbles_and_grass(L)
    p = breathe(S.POSES["sit"], t, .006, 2.5)
    if 2.15 < t < 2.5:
        u = (t - 2.15) / .35
        p["neck"] = (p["neck"][0], p["neck"][1] + .014 * math.sin(u * 30) * (1 - u))
    S.boy(L, p, RX - RW * .5 - 70, GROUND, 420, -1, t * 3)
    S.sword(L, (150, GROUND - 14), math.radians(-3), 90, True)
    L.poly([(335, GROUND - 4), (420, GROUND - 14), (418, GROUND - 2)], STEEL + (255,))
    u = t - 2.15
    if 0 < u < 1.2:
        a = int(255 * ease(u / .2) * (1 - ease((u - .7) / .5)))
        for x, y, r_ in ((190, 990, 26), (150, 950, 18), (120, 920, 11)):
            L.circ(x, y - 30 * u, r_, (230, 230, 240, int(90 * a / 255)))
        pop(L, "哼", 225, 960 - 30 * u, 76, 0, (200, 200, 215, 255), t, 2.15, 1.2, (20, 20, 30, 255))
    if t < t_fall:
        r = 6 + 10 * ease((t - 2.0) / .9)
        S.water_drop(L, DRIP_X + math.sin(t * 9) * .6, 516 + r * .9, r)
    elif t < t_hit:
        tau = t - t_fall
        y = 532 + .5 * G * tau * tau
        S.water_drop(L, DRIP_X, y, 18)
        for k in range(3):
            L.line([(DRIP_X, y - 60 - k * 40), (DRIP_X, y - 45 - k * 40)], AQUA_L + (int((160 - k * 50) * clamp(tau / .12)),), 5)
        rgb = S.glow(rgb, DRIP_X, y, 40, AQUA, .3)
    else:
        v = t - t_hit
        rgb = S.glow(rgb, DRIP_X, top, 55 + 40 * ease_out(v / .5), AQUA, .6 * math.exp(-v * 3))
        for rx0, delay, al0 in ((70, 0, 230), (125, .1, 130)):
            uu = (v - delay) / .7
            if 0 < uu < 1:
                S.ring(L, DRIP_X, top, 20 + (rx0 - 20) * ease_out(uu), al0 * (1 - uu), 4 if rx0 < 100 else 3)
        for k in range(6):
            vx, vy = (k - 2.5) * 60, -380 - (k % 2) * 90
            if v < .45:
                S.water_drop(L, DRIP_X + vx * v, top + vy * v + 1100 * v * v, 4.5, int(255 * (1 - v / .45)))
        pop(L, "滴", DRIP_X + 130, top - 90, 120, -8, AQUA_L + (255,), t, t_hit, .8, (10, 40, 55, 255))
        if t > 3.7:
            r = 6 + 6 * ease((t - 3.7) / .3)
            S.water_drop(L, DRIP_X, 516 + r * .9, r)
    return S.finish(S.stamp(rgb, L))


# ------------------------------------------------------------------ shot 3 : 4-7.5s
LABELS = (("1天", 420, 100, 4.35), ("1年", 600, 120, 5.2), ("10年", 790, 140, 6.1))


def scene3(t):
    t = clamp(t, 4.0, 7.5)
    hole = round(.8 * ease((t - 4.0) / 3.3) / .04) * .04
    rgb, m = base("C", hole)
    top = S.rock_top(m, DRIP_X)
    cx, cy, R = W / 2, 1000, 560
    L = S.Layer()
    S.rock_details(L, m)
    fa = ease((t - 4.0) / .3)
    for a in np.linspace(200, 340, 26):
        a0, a1 = math.radians(a), math.radians(a + 3)
        L.line([(cx + R * math.cos(a0), cy + R * math.sin(a0)), (cx + R * math.cos(a1), cy + R * math.sin(a1))], (160, 170, 195, int(190 * fa)), 4)
    cyc = (t - 4.0) / .875
    k, fr = min(int(cyc), 3), clamp(cyc - int(cyc)) if cyc < 4 else 1.0
    ang = math.radians(200 + 140 * fr)
    bx, by = cx + R * math.cos(ang), cy + R * math.sin(ang)
    al = clamp(math.sin(math.pi * fr) * 2.2) * fa
    if al > 0:
        if k % 2 == 0:
            rgb = S.glow(rgb, bx, by, 70, GOLD, .7 * al)
            for q in range(12):
                a = q * math.pi / 6 + t
                L.line([(bx + math.cos(a) * 46, by + math.sin(a) * 46), (bx + math.cos(a) * 66, by + math.sin(a) * 66)], GOLD + (int(255 * al),), 6)
            L.circ(bx, by, 36, GOLD + (int(255 * al),))
        else:
            L.circ(bx, by, 34, IVORY + (int(255 * al),))
            L.circ(bx + 16, by - 10, 30, (6, 8, 14, int(255 * al)))
    S.pebbles_and_grass(L)
    # drops: more and more of them
    P = .45
    for q in range(6):
        t_on = 4.0 + q * .4
        if t < t_on:
            continue
        c = ((t - t_on) / P + q * .17) % 1
        a_in = clamp((t - t_on) / .3)
        if c < .35:
            r = 10 + 6 * ease(c / .35)
            S.water_drop(L, DRIP_X, 516 + r * .9, r, int(230 * a_in))
        elif c < .82:
            y = 532 + (top - 532) * ((c - .35) / .47) ** 2
            S.water_drop(L, DRIP_X, y, 11 + (q % 2) * 3, int(235 * a_in))
        else:
            uu = (c - .82) / .18
            S.ring(L, DRIP_X, top, 36 + 44 * uu, 180 * (1 - uu) * a_in, 3)
    rgb = S.glow(rgb, RX, top + 20, 70, AQUA, .25 + .6 * hole / .8)
    # time labels (sizes 100 / 120 / 140), each pops in and stays
    for i, (txt, y, size, t0) in enumerate(LABELS):
        if i > 0 and t > t0:
            aa = int(230 * ease((t - t0) / .15))
            ay = (LABELS[i - 1][1] + y) / 2 - 4 + (0 if i == 1 else 6)
            L.poly([(308, ay - 12), (352, ay - 12), (330, ay + 16)], IVORY + (aa,))
        pop(L, txt, 330, y, size, 0, GOLD + (255,), t, t0, 99, (40, 22, 6, 255), S.BOLD)
    p = mix_pose(S.POSES["sit"], S.POSES["sleep"], ease((t - 4.0) / .5))
    S.boy(L, breathe(p, t, .008, 2.2), RX - RW * .5 - 70, GROUND, 420, -1, t * 2.2)
    for q, (zx, zy, zs) in enumerate(((245, 1075, 46), (205, 1020, 60), (165, 960, 78))):
        c = (t * .9 + q / 3) % 1
        a = int(235 * math.sin(math.pi * c) * ease((t - 4.4) / .4))
        if a > 0:
            L.text((zx - 40 * c, zy - 60 * c), "Z", (S.CAL, zs + 14 * c), IVORY + (a,), stroke=4, stroke_fill=(30, 40, 70, a))
    return S.finish(S.stamp(rgb, L))


# ------------------------------------------------------------------ shot 4 : 7.5-9.5s
_rc = np.random.default_rng(4)
CH_X, CH_Y = _rc.uniform(-70, 70, 10), _rc.uniform(420, 700, 10)
CH_VX, CH_VY = _rc.uniform(-320, 320, 10), _rc.uniform(-650, -150, 10)
CH_SZ, CH_SP = _rc.uniform(10, 24, 10), _rc.uniform(-8, 8, 10)


def scene4(t):
    t = clamp(t, 7.5, 9.5)
    tt = t - 7.5
    p = ease_out(tt / .45)
    rgb, (left, right) = base("D", p)
    L = S.Layer()
    S.rock_details(L, left, cracks=False)
    S.rock_details(L, right, cracks=False)
    S.pebbles_and_grass(L)
    f = ease((tt - .12) / .35)
    if f > 0:
        for k, (dx, w) in enumerate(((0, 50), (-24, 24), (24, 24))):
            ytop = GROUND + 20 - 450 * f
            pts = [(RX + dx + math.sin(u * 5 + k + t * 8) * 14 * (1 - u), GROUND + 20 - u * 450 * f) for u in np.linspace(0, 1, 16)]
            for i in range(len(pts) - 1):
                L.cap(pts[i], pts[i + 1], w, w * 1.05, (AQUA if k == 0 else AQUA_D) + (235,))
        for i in range(5):
            L.line([(RX - 8 + i * 4, GROUND + 20 - 450 * f + i * 20), (RX - 6 + i * 3 + math.sin(t * 9 + i) * 3, GROUND - 40)], AQUA_L + (200,), 5)
    pw = ease((tt - .35) / .5)
    if pw > 0:
        L.ell(RX, GROUND + 70, 330 * pw, 62 * pw, AQUA_D + (170,))
        L.ell(RX, GROUND + 64, 260 * pw, 44 * pw, AQUA + (190,))
        S.ring(L, RX, GROUND + 70, 330 * pw, 220)
        S.ring(L, RX, GROUND + 70, (230 + 30 * math.sin(t * 5)) * pw, 160, 3)
    for i in range(10):
        a = 255 * (1 - clamp((tt - 1.2) / .6))
        if a <= 0:
            continue
        x = RX + CH_X[i] + CH_VX[i] * tt
        y = GROUND - CH_Y[i] + CH_VY[i] * tt + 700 * tt * tt
        sz, r_ = CH_SZ[i], CH_SP[i] * tt
        pts = [(sz, 0), (0, sz * .7), (-sz * .8, 0), (0, -sz)]
        L.poly([(x + px * math.cos(r_) - py * math.sin(r_), y + px * math.sin(r_) + py * math.cos(r_)) for px, py in pts], (170, 182, 205, int(a)))
    pop(L, "咔！", RX + 30, GROUND - 880, 200, -6, IVORY + (255,), t, 7.5, 1.5, jitter=5)
    hop = 55 * math.sin(math.pi * clamp((tt - .05) / .45))
    pose = mix_pose(S.POSES["dazed"], S.POSES["amazed"], ease_out((tt - .05) / .2))
    S.boy(L, pose, 235, GROUND - hop, 420, 1, t * 5)
    ua = ease((tt - .15) / .15)
    if ua > 0:
        for k in range(3):
            a = math.radians(-130 + k * 32)
            r1, r2 = 250 + 30 * (1 - ua), 310 + 30 * (1 - ua)
            L.line([(235 + math.cos(a) * r1, GROUND - hop - 440 + math.sin(a) * r1), (235 + math.cos(a) * r2, GROUND - hop - 440 + math.sin(a) * r2)], IVORY + (int(255 * ua),), 7)
    img = S.finish(S.stamp(rgb, L))
    if t > 9.25:
        img = Image.blend(img, Image.new("RGB", (W, H), (0, 0, 0)), ease((t - 9.25) / .25))
    return img


# ------------------------------------------------------------------ shot 5 : 9.5-12s
_CH = {}


def char_mask(ch):
    if ch not in _CH:
        im = Image.new("L", (320, 360), 0)
        ImageDraw.Draw(im).text((160, 180), ch, font=S.font(S.CAL, 176), fill=255, anchor="mm")
        _CH[ch] = im
    return _CH[ch]


def scene5(t):
    from PIL import ImageFilter
    t = clamp(t, 9.5, 12.0)
    rgb, _ = base("E")
    L = S.Layer()
    cxm = W / 2
    if t < 9.95:
        if t >= 9.55:
            if t < 9.75:
                sz, y = 36 * ease((t - 9.55) / .2), 420
            else:
                sz, y = 36, 420 + 350 * ((t - 9.75) / .2) ** 2
            if sz > 1:
                rgb = S.glow(rgb, cxm, y, 70, AQUA, .5)
                S.water_drop(L, cxm, y, sz)
    else:
        v = t - 9.95
        rgb = S.glow(rgb, cxm, 770, 90, AQUA, .6 * math.exp(-v * 5))
        for rx0, delay, al0 in ((120, 0, 230), (200, .1, 140), (290, .2, 80)):
            u = (v - delay) / .9
            if u > 0:
                S.ring(L, cxm, 770, lerp(20, rx0, ease_out(u)), min(255, al0 * (1 + 1.6 * (1 - ease_out(u)))))
    ea = ease((t - 10.15) / .3)
    if ea > 0:
        rgb = S.glow(rgb, cxm, 640, 80, AQUA, .6 * ea)
        S.water_drop(L, cxm, 640, 36, int(255 * ea))
    img = S.finish(S.stamp(rgb, L)).convert("RGBA")
    for k, ch in enumerate("柔弱胜刚强"):
        u = (t - (10.1 + k * .15)) / .3
        a = ease(u)
        if a <= 0:
            continue
        sc = 1.15 - .15 * ease_out(u)
        sz = (int(320 * sc), int(360 * sc))
        im = char_mask(ch).resize(sz, Image.BICUBIC)
        b = (1 - a) * 14
        if b > .4:
            im = im.filter(ImageFilter.GaussianBlur(b))
        lay = Image.new("RGBA", sz, IVORY + (0,))
        lay.putalpha(im.point(lambda v, a=a: int(v * a)))
        comp(img, lay, cxm + (k - 2) * 182 - sz[0] / 2, 1010 - sz[1] / 2)
    d = ImageDraw.Draw(img)
    for txt, y, size, t0, col in (("天下莫柔弱于水，", 1210, 42, 10.85, (205, 198, 182)), ("而攻坚强者莫之能胜。", 1275, 42, 11.0, (205, 198, 182)),
                                  ("——《道德经》第七十八章", 1365, 32, 11.25, (140, 134, 120))):
        a = ease((t - t0) / .3)
        if a > 0:
            d.text((cxm, y), txt, font=S.font(S.SERIF, size), fill=col + (int(255 * a),), anchor="mm")
    return img.convert("RGB")


# ------------------------------------------------------------------ UI: title + seal on top, thin progress bar
_UI = []


def ui_layer(t):
    if not _UI:
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(im).text((W / 2 - 40, 150), "水 与 石", font=S.font(S.CAL, 112), fill=IVORY + (255,), anchor="mm")
        im.alpha_composite(S.seal_img(78), (W // 2 + 170, 112))
        _UI.append(im)
    ui = _UI[0].copy()
    ha = ease(t / .4)
    if ha < 1:
        ui.putalpha(ui.getchannel("A").point(lambda v: int(v * ha)))
    d = ImageDraw.Draw(ui)
    x0, x1, y = 90, W - 90, H - 110
    seg = (x1 - x0 - 48) / 5
    for k in range(5):
        a = x0 + k * (seg + 12)
        d.line([(a, y), (a + seg, y)], fill=(80, 76, 70, 255), width=6)
        fr = clamp((t - BOUNDS[k]) / (BOUNDS[k + 1] - BOUNDS[k]))
        if fr > 0:
            d.line([(a, y), (a + seg * fr, y)], fill=GOLD + (255,), width=6)
    return ui


# ------------------------------------------------------------------ compose
def shake(t):
    dx = dy = 0.0
    for t0, amp, dur in ((1.0, 11, .3), (7.5, 14, .35)):
        u = (t - t0) / dur
        if 0 <= u < 1:
            dx += amp * (1 - u) * math.sin(t * 95 + 1.3)
            dy += amp * (1 - u) * math.sin(t * 79)
    if 7.0 < t < 7.5:
        amp = 1 + 4 * (t - 7.0) / .5
        dx += amp * math.sin(t * 120)
        dy += amp * .6 * math.sin(t * 97)
    return int(dx), int(dy)


def scene_img(t):
    if t < 2.0:
        img = scene1(t)
        if t > 1.8:
            img = Image.blend(img, scene2(2.0), ease((t - 1.8) / .2))
        return img
    if t < 4.0:
        return scene2(t)
    if t < 7.5:
        return scene3(t)
    if t < 9.5:
        return scene4(t)
    return scene5(t)


_GR = np.random.default_rng(1).normal(0, 2.5, (8, OH, OW, 1)).astype(np.float32)


def render_frame(i):
    t = i / FPS
    sc = scene_img(t).convert("RGBA")
    dx, dy = shake(t)
    if dx or dy:
        bg = Image.new("RGBA", (W, H), (0, 0, 0, 255))
        bg.paste(sc, (dx, dy))
        sc = bg
    if 7.5 <= t < 7.65:
        sc.alpha_composite(Image.new("RGBA", (W, H), (255, 244, 215, int(215 * (1 - (t - 7.5) / .15)))))
    sc.alpha_composite(ui_layer(t))
    im = sc.convert("RGB").resize((OW, OH), Image.LANCZOS)
    arr = np.asarray(im, np.float32) + _GR[i % 8]
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(os.path.join(FR_DIR, f"{i:04d}.png"))
    return i


# ------------------------------------------------------------------ sound effects (synthesised, no voice)
SR = 44100
NS = int(SR * DUR)
rs = np.random.default_rng(99)
BUF = np.zeros(NS, np.float32)


def tt_(d):
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
    t = tt_(dur)
    return np.sin(2 * np.pi * (f0 * t + f1 * (1 - np.exp(-35 * t)) / 35)) * np.exp(-t * k)


def pluck(f, dur=1.6, decay=2.4):
    t = tt_(dur)
    s = sum(np.sin(2 * np.pi * f * h * t + h) * np.exp(-t * (decay + h * 1.3)) / h ** 1.25 for h in range(1, 7))
    return (s + nz(dur) * np.exp(-t * 90) * .25) * np.clip(t / .004, 0, 1)


def ding(f, dur=1.3):
    t = tt_(dur)
    return (np.sin(2 * np.pi * f * t) + .5 * np.sin(2 * np.pi * f * 2.76 * t) * np.exp(-t * 4) + .25 * np.sin(2 * np.pi * f * 5.4 * t) * np.exp(-t * 7)) * np.exp(-t * 3.2)


def sweep(dur, up=True):
    n = sm(nz(dur), 40)
    env = np.sin(np.linspace(0, np.pi, len(n))) ** 2
    return n * env * (np.linspace(.4, 1, len(n)) if up else 1)


def build_audio():
    t = tt_(DUR)
    BUF[:] = (.04 * np.sin(2 * np.pi * 55 * t) + .025 * np.sin(2 * np.pi * 82.5 * t)) * np.clip(t / .5, 0, 1)
    # shot 1: run, swing, clang, snap, tumbling blade, landing
    for q in range(4):
        put(.08 + q * .14, sm(nz(.08), 30) * np.exp(-tt_(.08) * 60) * 3, .35)
    put(.72, sweep(.28) * 6, .35)
    tc = tt_(1.0)
    put(1.0, sum(a * np.sin(2 * np.pi * f * tc) * np.exp(-tc * k) for f, a, k in [(620, .4, 6), (1240, .5, 8), (1870, .35, 10), (2790, .3, 14), (4150, .2, 22)]) + nz(1.0) * np.exp(-tc * 80) * .5, .5)
    put(1.0, np.sin(2 * np.pi * 90 * tt_(.35)) * np.exp(-tt_(.35) * 18), .4)
    put(1.04, sweep(.7, False) * 4, .12)
    for tl, f in ((1.85, 3100), (1.93, 2300)):
        put(tl, np.sin(2 * np.pi * f * tt_(.3)) * np.exp(-tt_(.3) * 25), .2)
    put(1.35, plop(260, -150, .3, 14), .3)
    for q, f in enumerate((880, 1109, 1319)):
        put(1.45 + q * .1, ding(f, .5), .08)
    # shot 2: drop
    put(3.37, plop(500, 800, .5, 13), .55)
    put(3.52, plop(560, 600, .3, 20), .15)
    # shot 3: glass dings on each label, day/night sweeps, accelerating drips, rumble
    for tl, f in ((4.35, 659), (5.2, 784), (6.1, 988)):
        put(tl, ding(f), .28)
    for q in range(4):
        put(4.0 + q * .875, sweep(.7) * 3, .08)
    tdr, step = 4.1, .4
    while tdr < 7.4:
        put(tdr, plop(rs.uniform(500, 800), rs.uniform(500, 900), .3, 22), .16 + .2 * (tdr - 4) / 3.5)
        tdr += step
        step = max(.12, step * .88)
    put(6.8, sm(nz(.7), 200) * 20 * np.linspace(0, 1, int(SR * .7)) ** 2, .35)
    # shot 4: crack, debris, surprise, water
    put(7.5, np.sin(2 * np.pi * 55 * tt_(1.2)) * np.exp(-tt_(1.2) * 5), .9)
    put(7.5, sm(nz(.7), 12) * np.exp(-tt_(.7) * 6) * 6, .8)
    for _ in range(14):
        put(rs.uniform(7.55, 8.7), np.sin(2 * np.pi * rs.uniform(700, 2200) * tt_(.06)) * np.exp(-tt_(.06) * 70), rs.uniform(.08, .2))
    tsl = tt_(.35)
    put(7.7, np.sin(2 * np.pi * np.cumsum(400 + 700 * tsl / .35) / SR) * np.exp(-tsl * 6), .22)
    n = nz(2.0)
    fl = sm(n, 4) - sm(n, 90)
    fl = fl / np.abs(fl).max() * (.6 + .4 * sm(nz(2.0), 3000) * 40)
    put(7.65, fl * np.clip(tt_(2.0) / .5, 0, 1) * np.clip((2.0 - tt_(2.0)) / .4, 0, 1), .3)
    # shot 5: drop, quick plucks per character, closing note
    put(9.95, plop(420, 900, .8, 9), .6)
    for q, f in enumerate((293.7, 330, 370, 440, 587.3)):
        put(10.1 + q * .15 + .05, pluck(f, 1.4, 2.6), .22)
    put(10.9, pluck(146.8, 1.0, 1.8), .5)
    put(10.9, ding(1174, 1.2), .1)
    BUF[:] *= (np.clip(t / .3, 0, 1) * np.clip((DUR - t) / .5, 0, 1)).astype(np.float32)
    out = BUF / max(1e-6, np.abs(BUF).max()) * .85
    path = os.path.join(HERE, "audio_v5.wav")
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
    out = os.path.join(HERE, "demo_v5_12s_sd.mp4")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(FR_DIR, "%04d.png"), "-i", wav,
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20", "-c:a", "aac", "-b:a", "128k", "-shortest", out], check=True)
    print("wrote", out)
