"""Standalone music for 《美国中期选举一次看懂》 — a Game of Thrones-style epic. An ORIGINAL piece (none of the show's notes are used).
From published analyses of the main title (cello lead because its tone is darker; a solo violin joins later and the orchestra repeats the theme; rustic percussion;
6/8 compound meter; a minor key that keeps flipping to its major; big leaps such as octaves; a repeated riff). Used here as techniques, with a different key, melody and chords:
  key / chords   D minor:  Dm | Bb | Gm | A  (ten bars up to the drop: Dm Bb Gm A Dm Bb Gm A Gm A, so the cycle restarts on Dm exactly at beat 44)
  meter          6/8: one video beat = three triplet eighths, a gallop; the cello ostinato goes up and down the chord tones
  melody         a leap up a minor sixth, then steps down:  D4-Bb4-A4-G4-A4 | Bb3-G4-F4-Eb4-F4 | G3-Eb4-D4-C4-D4 | A3-F4-E4-D4-C#4
                 solo cello (low) with an octave line above; violins join after four bars; at the drop the whole orchestra plays it with brass and a bell
  percussion     low toms and a taiko-like kick on the beat, a galloping tom fill, a rising roll into the drop, one huge hit on it
  outro          the cello alone, the phrase once, ending on D
  structure      起 solo cello + quiet pulse | 承 layers add up | 转 the theme climbs instead of falling + a rising roll, break, | 合 climax with brass | pull-back | second rise | end
"""
import json, os, wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
TL = json.loads((ROOT / "src" / "timeline.json").read_text())
SC, TOTAL = TL["scenes_beats"], TL["total_beats"]
SR, VBEAT = 44100, 60 / float(os.environ.get("VIDEO_BPM", TL["bpm"]))
INTRO, TB = TL["intro_seconds"], SC["D_title"][1]
def T(n): return n / TB * INTRO if n < TB else INTRO + (n - TB) * VBEAT
A0 = SC["A_race"][0]
DROP = SC["E_bell"][0]                      # video beat 44 (the bell strike)
BREAK0 = DROP - 2
BUILD0 = DROP - 6
OUT0 = SC["J_end"][0]
CUT = 55.0                                 # the climax ends here (video beat 55); pull-back, second rise at 58, outro at 62
STEP = 1 / 8                               # one 16th note in video beats
DUR = T(TOTAL) + TL["tail_seconds"]
N = int(DUR * SR); tt = np.arange(N) / SR; rng = np.random.default_rng(66)
BUS = {k: np.zeros((N, 2)) for k in ("lead", "arp", "keys", "drums", "bass", "pad", "fx")}

def add(bus, sig, start, pan=0.0, gain=1.0):
    i = int(round(start * SR))
    if i >= N: return
    sig = np.asarray(sig, float)
    if sig.ndim == 1: sig = np.stack([sig * np.sqrt(0.5 * (1 - pan)), sig * np.sqrt(0.5 * (1 + pan))], 1)
    if i < 0: sig, i = sig[-i:], 0
    sig = sig[: N - i] * gain; BUS[bus][i:i + len(sig)] += sig
def hz(m): return 440.0 * 2 ** ((m - 69) / 12)
def filt(x, lo=None, hi=None, order=4):
    X = np.fft.rfft(x, axis=0); f = np.fft.rfftfreq(len(x), 1 / SR); H = np.ones_like(f)
    if hi: H /= 1 + (f / hi) ** order
    if lo: H /= 1 + (lo / np.maximum(f, 1e-3)) ** order
    return np.fft.irfft(X * (H[:, None] if x.ndim == 2 else H), n=len(x), axis=0)
def env(n, a=0.002, r=0.08):
    e = np.ones(n); na = max(1, min(n, int(a * SR))); nr = max(1, min(n, int(r * SR)))
    e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr); return e
def euclid(k, n, rot=0):
    pat = [((i * k) // n) != (((i - 1) * k) // n) if i else True for i in range(n)]
    return pat[-rot:] + pat[:-rot] if rot else pat

KICK = euclid(4, 16)
DEMBOW = [i in (3, 6, 11, 14) for i in range(16)]
HATS = euclid(7, 16)

# ---------- instruments ----------
def epiano(m, dur=1.2, vel=1.0):
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(m); w = 2 * np.pi * f * t
    s = np.sin(w) * np.exp(-t * 1.8) + 0.5 * np.sin(2 * w) * np.exp(-t * 3.2) + 0.28 * np.sin(3.01 * w) * np.exp(-t * 5.0) + 0.22 * np.sin(7 * w) * np.exp(-t * 28)
    s *= 1 + 0.07 * np.sin(2 * np.pi * 4.6 * t)
    return s * env(n, 0.004, 0.18) * vel
def pluck_saw(m, dur=0.2, vel=1.0, cut=3200):
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(m)
    s = (2 * np.mod(np.cumsum(np.full(n, f)) / SR, 1) - 1) + (2 * np.mod(np.cumsum(np.full(n, f * 1.004)) / SR, 1) - 1)
    s = filt(s * np.exp(-t * 16), hi=cut, order=2)
    return s * env(n, 0.002, 0.04) * vel
def sub808(m, dur=0.55, vel=1.0):
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(m)
    ph = 2 * np.pi * np.cumsum(f * (1 + 0.6 * np.exp(-t * 45))) / SR
    return np.tanh(1.9 * np.sin(ph)) * np.exp(-t * 3.0) * env(n, 0.003, 0.1) * vel
def bell(m, dur=1.8, vel=1.0):
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(m)
    return sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * d) for r, a, d in ((1, 1, 1.6), (2.76, 0.35, 3.5), (5.4, 0.15, 7))) * env(n, 0.001, 0.25) * vel
def strings(notes, dur, cut=2000, att=0.35, rel=0.6):
    n = int(dur * SR); out = np.zeros((n, 2))
    for m in notes:
        for vi, d in enumerate((-0.09, -0.03, 0.03, 0.09)):
            f = hz(m) * 2 ** (d / 12); s = 2 * np.mod(np.cumsum(np.full(n, f) / SR) + rng.uniform(), 1.0) - 1; pan = (vi - 1.5) / 1.5 * 0.7
            out[:, 0] += s * np.sqrt(0.5 * (1 - pan)); out[:, 1] += s * np.sqrt(0.5 * (1 + pan))
    return filt(out, hi=cut, order=2) * env(n, att, rel)[:, None] / (len(notes) * 4) ** 0.5 / 2.4
def kick():
    n = int(0.42 * SR); t = np.arange(n) / SR
    return np.tanh(2.4 * np.sin(2 * np.pi * np.cumsum(46 + 110 * np.exp(-t * 28)) / SR) * np.exp(-t * 8)) * env(n, 0.0008, 0.05)
def clap():
    n = int(0.28 * SR); out = np.zeros(n)
    for d in (0, 0.011, 0.022):
        i = int(d * SR); k = int(0.2 * SR); t = np.arange(k) / SR
        out[i:i + k] += filt(rng.standard_normal(k), lo=900, hi=5200) * np.exp(-t * (30 if d < 0.022 else 14))
    return out * 0.8
HH = filt(rng.standard_normal(int(0.3 * SR)), lo=7000); HH /= np.abs(HH).max()
def hat(open_=False):
    n = int((0.16 if open_ else 0.04) * SR); return HH[:n] * np.exp(-np.arange(n) / SR * (22 if open_ else 100))
def crash():
    n = int(2.6 * SR); t = np.arange(n) / SR; c = filt(rng.standard_normal((n, 2)), lo=3500); return c / np.abs(c).max() * np.exp(-t * 1.5)[:, None]

# ---------- harmony and parts ----------
STEP3 = 1 / 3                                           # one triplet eighth in video beats (6 per 6/8 measure = 2 video beats)
PRE = ["Dm", "Bb", "Gm", "A", "Dm", "Bb", "Gm", "A", "Gm", "A"]
CYC = ["Dm", "Bb", "Gm", "A"]
def chord_at(b):
    bar = int((b - A0) // 4)
    return PRE[bar] if b < DROP else CYC[int((b - DROP) // 4) % 4]
OST = {"Dm": [50, 57, 62, 65, 62, 57], "Bb": [46, 53, 58, 62, 58, 53], "Gm": [43, 50, 55, 58, 55, 50], "A": [45, 52, 57, 61, 57, 52]}
SUB = {"Dm": 38, "Bb": 34, "Gm": 31, "A": 33}
PAD = {"Dm": [50, 57, 62, 65], "Bb": [46, 53, 58, 62], "Gm": [43, 50, 55, 58], "A": [45, 52, 57, 61]}
PHR = {"Dm": [(0, 62, 1.0), (1.0, 70, .667), (1.667, 69, .333), (2.0, 67, 1.0), (3.0, 69, 1.0)],       # the theme: a leap up, then steps DOWN
       "Bb": [(0, 58, 1.0), (1.0, 67, .667), (1.667, 65, .333), (2.0, 63, 1.0), (3.0, 65, 1.0)],
       "Gm": [(0, 55, 1.0), (1.0, 63, .667), (1.667, 62, .333), (2.0, 60, 1.0), (3.0, 62, 1.0)],
       "A": [(0, 57, 1.0), (1.0, 65, .667), (1.667, 64, .333), (2.0, 62, 1.0), (3.0, 61, 1.0)]}
PHR_UP = {"Dm": [(0, 62, 1.0), (1.0, 69, .667), (1.667, 70, .333), (2.0, 72, 1.0), (3.0, 74, 1.0)],      # the turn: the same leap, but the steps now climb
          "Bb": [(0, 58, 1.0), (1.0, 65, .667), (1.667, 67, .333), (2.0, 70, 1.0), (3.0, 72, 1.0)],
          "Gm": [(0, 67, 1.0), (1.0, 70, .667), (1.667, 72, .333), (2.0, 74, 1.0), (3.0, 75, 1.0)],
          "A": [(0, 69, 1.0), (1.0, 72, .667), (1.667, 73, .333), (2.0, 76, 1.0), (3.0, 77, 1.0)]}
def level(b, pts):
    xs, ys = zip(*pts); return float(np.interp(b, xs, ys))
# ---- the arc: 起 (0–12) 承 (12–30) 转 (30–44) 合 = climax (44–58), pull-back (58–68), second rise (68–82), end (82–90) ----
LV = [(0, 0.62), (12, 0.7), (20, 0.88), (30, 1.0), (41, 1.2), (44, 1.35), (54.8, 1.28), (55.2, 0.62), (58, 0.78), (60.5, 1.0), (61.8, 1.1), (62.2, 0.8), (66, 0.55)]
G_OST = [(0, 0.4), (12, 0.5), (20, 1.0), (54.8, 1.0), (55.2, 0.35), (57, 0.45), (58.5, 0.9), (61.8, 0.9), (62.2, 0.0)]
G_DRUM = [(0, 0.0), (11.8, 0.0), (12.2, 0.6), (20, 1.0), (54.8, 1.0), (55.2, 0.2), (57, 0.2), (58.5, 0.9), (61.8, 0.9), (62.2, 0.0)]
G_VLN = [(0, 0.0), (23.8, 0.0), (24.2, 1.0), (54.8, 1.0), (55.2, 1.7), (57.5, 1.7), (59, 1.0), (61.8, 1.0), (62.2, 0.0)]       # violins: they lead alone in the pull-back
G_CELLO = [(0, 1.0), (54.8, 1.0), (55.2, 0.35), (57.5, 0.5), (59, 1.0)]
G_BRASS = [(0, 0.0), (43.9, 0.0), (44, 1.0), (54.8, 1.0), (55.2, 0.0), (59.8, 0.0), (60.2, 0.9), (61.8, 0.9), (62.2, 0.0)]
def big(b): return DROP <= b < CUT or 60 <= b < OUT0
def cello(m, dur, vel=1.0, cut=2600, att=0.08):
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(m) * (1 + 0.005 * np.sin(2 * np.pi * 5.4 * t) * np.clip((t - 0.2) / 0.4, 0, 1))
    s = sum(2 * np.mod(np.cumsum(f * 2 ** (d / 12)) / SR, 1) - 1 for d in (-0.07, 0.0, 0.07))
    return filt(s, hi=cut, order=2) * env(n, att, 0.25) * vel / 3
def brass(m, dur, vel=1.0):
    n = int(dur * SR); t = np.arange(n) / SR; ph = np.cumsum(np.full(n, hz(m)) / SR)
    s = (2 * np.mod(ph, 1) - 1) + 0.5 * (2 * np.mod(2 * ph, 1) - 1)
    return filt(s, hi=1500, order=2) * env(n, 0.12, 0.3) * vel / 1.5
def tom(f0=92, dur=0.5, vel=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(f0 * (1 + 0.55 * np.exp(-t * 16))) / SR) * np.exp(-t * 6.0) * env(n, 0.002, 0.08) * vel
def spic(m, vel=1.0, dur=0.16): return pluck_saw(m, dur, vel, cut=1400)

# ---------- 0–1 s: quiet but already moving — a soft Dm ostinato, a low tom, the first cello leap ----------
add("pad", strings(PAD["Dm"], 1.8, cut=1800, att=0.05, rel=0.6), 0, gain=0.8)
add("drums", tom(88, 0.7), 0.0, gain=0.10)             # first second: same level as what follows (no loud opening drum)
for i in range(6): add("arp", spic(OST["Dm"][i], 0.7 + 0.06 * i), i / 6, pan=-0.1, gain=0.16)
add("bass", sub808(38, 1.0), 0, gain=0.35); add("bass", sub808(38, 0.4), 0.5, gain=0.2)
add("lead", cello(62, 0.5, 1.0), 0.0, gain=1.8); add("lead", cello(70, 0.9, 1.0), 0.5, gain=1.8)

# ---------- the arrangement, bar by bar ----------
bar = A0
while bar < OUT0:
    chord = chord_at(bar); end = min(bar + 4, OUT0); lv = level(bar, LV); rising = 28 <= bar < DROP
    add("pad", strings(PAD[chord], (end - bar) * VBEAT + 0.5, cut=1500 if bar < DROP else 2600, att=0.4), T(bar), gain=0.55 * lv)
    for off, m, ln in (PHR_UP if rising else PHR)[chord]:
        b = bar + off
        if BREAK0 <= b < DROP or b >= OUT0: continue
        d = ln * VBEAT + 0.25; lb = level(b, LV)
        add("lead", cello(m, d, 1.0), T(b), pan=-0.05, gain=2.0 * lb * level(b, G_CELLO))
        add("lead", pluck_saw(m, 0.28, 1.0, cut=3600), T(b), pan=0.1, gain=0.45 * lb)
        gv = level(b, G_VLN)
        if gv > 0.02: add("lead", cello(m + 12, d, 0.8, cut=3400, att=0.12), T(b), pan=0.2, gain=1.4 * lb * gv)                  # violins
        gb = level(b, G_BRASS)
        if gb > 0.02: add("lead", brass(m, d, 0.9), T(b), pan=-0.25, gain=1.0 * lb * gb); add("keys", bell(m + 12, 1.3, 0.6), T(b), pan=0.25, gain=0.3 * gb)
    hits = [0, 1, 1.667, 2, 3, 3.667] if big(bar) else [0, 1, 2, 3]
    for h in hits:
        b = bar + h
        if b >= end: continue
        add("bass", sub808(SUB[chord], 0.7), T(b), gain=(0.4 if BREAK0 <= b < DROP else 0.7) * (0.7 + 0.3 * level(b, LV)))
    bar += 4

# ---------- the 6/8 gallop: ostinato, toms, drums; builds, a cut, a fill and a second rise ----------
BUILD0 = DROP - 10                                        # a long build (beat 34): the turn
k = 0
while A0 + k * STEP3 < OUT0:
    b = A0 + k * STEP3; iu = k % 6; chord = chord_at(b); brk = BREAK0 <= b < DROP; lv = level(b, LV); go = level(b, G_OST); gd = level(b, G_DRUM); k += 1
    if brk: continue
    note = OST[chord][iu]; acc = iu in (0, 3); bg = big(b)
    add("arp", spic(note, 0.95 if acc else 0.5), T(b), pan=-0.1, gain=0.45 * lv * go)
    if bg or (b >= A0 + 16 and iu in (1, 4)): add("arp", spic(note + 12, 0.35), T(b), pan=0.15, gain=(0.22 if bg else 0.18) * lv * go)
    if gd > 0.05:
        if bg:
            if iu in (0, 3): add("drums", kick(), T(b), gain=0.9 * gd)
            if iu == 3: add("drums", clap(), T(b), gain=0.4 * gd)
            if iu in (1, 4): add("drums", tom(150, 0.3, 0.8), T(b), pan=0.1, gain=0.5 * gd)
            add("drums", hat(), T(b), pan=0.3, gain=0.1 * gd)
        else:
            if iu in (0, 3): add("drums", tom(92 if iu == 0 else 110, 0.5, 0.9), T(b), gain=0.9 * lv * gd)
            if iu == 0 and b >= 20: add("drums", kick(), T(b), gain=0.6 * gd)
    elif iu in (0, 3) and CUT <= b < 58: add("drums", tom(80, 0.5, 0.7), T(b), gain=0.5)                       # only a distant heartbeat in the pull-back
    if BUILD0 <= b < BREAK0:                                                                                   # the turn: a rising roll
        x = (b - BUILD0) / (BREAK0 - BUILD0); add("drums", hat(), T(b), pan=-0.2, gain=0.06 + 0.2 * x)
        if iu in (4, 5) or x > 0.5: add("drums", tom(130 + 30 * x, 0.25, 0.7), T(b), gain=0.3 + 0.7 * x)
    if CUT - 2 <= b < CUT and iu in (0, 2, 4): add("drums", tom(100, 0.3, 0.8), T(b), gain=0.5 + 0.4 * (b - CUT + 2) / 2)    # fill out of the climax
    if 57 <= b < 59 and iu in (0, 2, 4): add("drums", tom(100, 0.3, 0.8), T(b), gain=0.3 + 0.5 * (b - 57) / 2)    # fill into the second rise
for (t0, t1, amp) in ((T(BUILD0), T(DROP), 0.18), (T(BREAK0), T(DROP), 0.3)):                                     # risers: a long one under the build, a short loud one in the break
    nb = int((t1 - t0) * SR); u = np.arange(nb) / nb
    nz = filt(rng.standard_normal((nb, 2)), lo=1800) * (u ** 2)[:, None]
    sweep = np.sin(2 * np.pi * np.cumsum(220 + 1500 * u ** 2) / SR) * (u ** 2)
    add("fx", nz / np.abs(nz).max(), t0, gain=amp); add("fx", sweep, t0, gain=amp / 3)
add("drums", crash(), T(DROP), gain=0.6); add("drums", kick(), T(DROP), gain=1.1); add("drums", tom(70, 0.9, 1.0), T(DROP), gain=0.9)
add("bass", sub808(26, 1.4, 1.0), T(DROP), gain=0.55); add("keys", bell(74, 2.2, 1.0), T(DROP), pan=0.2, gain=0.22)
add("drums", crash(), T(CUT), gain=0.3)                                                                          # the climax rings out, then the cut

# ---------- outro: the cello alone, the phrase once, ending on D ----------
for off, m, ln in PHR["Dm"]:
    add("lead", cello(m + 12, ln * VBEAT * 1.4 + 0.5, 1.0), T(OUT0 + off), pan=-0.05, gain=1.6)
add("lead", cello(62, 4 * VBEAT + 1.6, 1.0, att=0.3), T(OUT0 + 4), pan=-0.05, gain=1.4)
add("pad", strings(PAD["Dm"], 4 * VBEAT + 0.6, cut=2000, att=0.3), T(OUT0), gain=0.8)
add("pad", strings([38, 50, 57, 62, 65], (TOTAL - OUT0 - 4) * VBEAT + 1.4, cut=2200, att=0.4, rel=1.3), T(OUT0 + 4), gain=0.9)
add("bass", sub808(38, 3.0), T(OUT0), gain=0.7); add("bass", sub808(38, 3.2), T(OUT0 + 4), gain=0.55)

# ---------- mix ----------
irn = int(1.3 * SR); it = np.arange(irn) / SR
ir = filt(rng.standard_normal((irn, 2)), lo=300, hi=7000) * np.exp(-it / 0.3)[:, None]; ir /= np.sqrt((ir ** 2).sum(axis=0))
# dotted-eighth echo on the hook
d = int(0.375 * VBEAT * SR); echo = BUS["lead"].copy()
for rpt in (1, 2, 3):
    sh = np.zeros_like(echo); sh[d * rpt:] = BUS["lead"][: N - d * rpt] * (0.38 ** rpt); echo += filt(sh, hi=3500, order=2)
BUS["lead"] = echo
send = BUS["lead"] * 0.45 + BUS["keys"] * 0.4 + BUS["pad"] * 0.3 + BUS["fx"] * 0.3 + BUS["arp"] * 0.15
nf = 1 << (N + irn - 1).bit_length()
wet = np.stack([np.fft.irfft(np.fft.rfft(send[:, c], nf) * np.fft.rfft(ir[:, c], nf), nf)[:N] for c in range(2)], 1)
LM = 0.14                                   # melody level: chosen so it sits ~4 dB above everything else in 250–3000 Hz (clear, but the bass keeps its share)
LEAD_PRES = filt(BUS["lead"], lo=1200, hi=4800, order=2)
mix = BUS["pad"] * 0.85 + (BUS["lead"] * 1.5 + LEAD_PRES * 0.7) * LM + BUS["arp"] + BUS["keys"] + BUS["drums"] + BUS["bass"] * 1.9 + BUS["fx"] + wet * 0.3
mix = filt(mix, lo=30, order=2); mix += 0.9 * filt(mix, lo=2500, order=2)
mix *= np.clip((DUR - tt) / 1.5, 0, 1)[:, None]
rms = np.sqrt(np.mean(mix ** 2)); mix *= 10 ** (-15.0 / 20) / max(rms, 1e-9)
ceil = 10 ** (-1 / 20)
mix = np.where(np.abs(mix) < 0.7 * ceil, mix, np.sign(mix) * (0.7 * ceil + 0.3 * ceil * np.tanh((np.abs(mix) - 0.7 * ceil) / (0.3 * ceil))))
def _rms(x, t0, t1):
    seg = x[int(t0 * SR):int(t1 * SR)]; return 20 * np.log10(np.sqrt(np.mean(seg ** 2)) + 1e-9)
print("bus level, first 1 s | 1–8 s (dB, before the final gain):", {k: (round(_rms(v, 0, 1), 1), round(_rms(v, 1, 8), 1)) for k, v in BUS.items()})
def _band(x, lo=250, hi=3000):
    m = x.mean(axis=1); X = np.abs(np.fft.rfft(m)) ** 2; f = np.fft.rfftfreq(len(m), 1 / SR); return X[(f >= lo) & (f < hi)].sum()
_others = sum(_band(BUS[k]) for k in ("pad", "arp", "keys", "drums", "bass", "fx")); _lead = _band((BUS["lead"] * 1.5 + LEAD_PRES * 0.7) * LM)
print(f"melody share of the 250–3000 Hz band: {100 * _lead / (_lead + _others):.0f}%  (lead vs everything else: {10 * np.log10(_lead / _others):+.1f} dB)")
outp = ROOT / "build" / os.environ.get("BGM_OUT", "bgm.wav"); outp.parent.mkdir(exist_ok=True)
with wave.open(str(outp), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes())
print(f"bgm -> {outp} ({DUR:.2f}s, peak {20*np.log10(np.abs(mix).max()):.1f} dBFS, drop at {T(DROP):.2f}s)")
