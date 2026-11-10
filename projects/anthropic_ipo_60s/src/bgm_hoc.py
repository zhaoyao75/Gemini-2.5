"""Music for 《美国中期选举一次看懂》 — a political-thriller feel in the spirit of House of Cards. An ORIGINAL piece (no melody is taken from the score).
From published interviews (Jeff Beal, Song Exploder / 99% Invisible / Slate): built from sketches, dark and driving, layered so it does not tire the ear,
a heavier cello in season 2, jazz roots. Used here as a mood, plus one classic dark-drama device:
  lament bass     the bass walks down chromatically  A – G – F# – F – E  (one step per bar) while the upper chord tones A–C–E stay put; the E is the unresolved dominant
  melody          a long-short-long phrase that is repeated a step lower on each bar of the descent (E-D-C | D-C-B | C-B-A | B-A-G# | G#-B-E), solo cello with a violin line on top
  drive           a staccato low-string pulse in eighths (sixteenths in the chorus) over a sub bass, so it is moving from the first second
  layers          the pulse, then toms, then violins, then the full band; the build before the drop, then the release lands on Am at beat 44
  outro           the cello alone, the phrase once, held on E
(Earlier versions are kept as bgm_*.py.)
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
A0 = SC["A_what"][0]
DROP = SC["E_senate"][0] + 6               # video beat 44
BREAK0 = DROP - 2
BUILD0 = DROP - 6
OUT0 = SC["J_end"][0]
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

# 5-chord cycle (10 bars = 40 beats from beat 4 to the drop, so the cycle restarts on Am exactly at beat 44)
CYC = ["Am", "Am/G", "F#m7b5", "Fmaj7", "E"]
BASS_NOTE = {"Am": 45, "Am/G": 43, "F#m7b5": 42, "Fmaj7": 41, "E": 40}
UPPER = {"Am": [57, 60, 64], "Am/G": [57, 60, 64], "F#m7b5": [57, 60, 64], "Fmaj7": [57, 60, 64], "E": [56, 59, 64]}
# the phrase: (offset in video beats, MIDI, length) — long, short, long; moved down a step each bar
PHRASE = {"Am": [(0, 76, 1.5), (1.5, 74, .5), (2, 72, 2.0)], "Am/G": [(0, 74, 1.5), (1.5, 72, .5), (2, 71, 2.0)],
          "F#m7b5": [(0, 72, 1.5), (1.5, 71, .5), (2, 69, 2.0)], "Fmaj7": [(0, 71, 1.5), (1.5, 69, .5), (2, 68, 2.0)], "E": [(0, 68, 1.5), (1.5, 71, .5), (2, 76, 2.0)]}
def level(b, pts):
    xs, ys = zip(*pts); return float(np.interp(b, xs, ys))
CRES = [(0, 1.0), (A0, 0.95), (DROP - 3, 1.1), (DROP, 1.1), (OUT0, 1.0), (TOTAL, 0.85)]
def cello(m, dur, vel=1.0, cut=2200, att=0.1):
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(m) * (1 + 0.005 * np.sin(2 * np.pi * 5.4 * t) * np.clip((t - 0.2) / 0.4, 0, 1))
    s = sum(2 * np.mod(np.cumsum(f * 2 ** (d / 12)) / SR, 1) - 1 for d in (-0.07, 0.0, 0.07))
    return filt(s, hi=cut, order=2) * env(n, att, 0.3) * vel / 3
def tom(f0=92, dur=0.5, vel=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(f0 * (1 + 0.55 * np.exp(-t * 16))) / SR) * np.exp(-t * 6.0) * env(n, 0.002, 0.08) * vel
def spic(m, vel=1.0, dur=0.16):                              # staccato low-string stab
    return pluck_saw(m, dur, vel, cut=900)

# ---------- 0–1 s: moving at once — a staccato pulse on A, a low tom, a string swell, the first cello note ----------
add("pad", strings([45, 57, 60, 64], 1.8, cut=1800, att=0.05, rel=0.6), 0, gain=0.9)
add("drums", crash(), 0, gain=0.3); add("drums", kick(), 0, gain=1.0); add("drums", tom(88, 0.7), 0.25, gain=1.3); add("drums", tom(110, 0.5), 0.5, gain=1.2); add("drums", kick(), 0.5, gain=0.9); add("drums", tom(130, 0.3), 0.75, gain=1.1)
for i in range(8): add("arp", spic(57 if i % 2 == 0 else 45, 0.7 + 0.05 * i), i * 0.125, pan=-0.1, gain=0.8)
add("bass", sub808(45, 1.0), 0, gain=0.95); add("bass", sub808(45, 0.4), 0.5, gain=0.7)
add("lead", cello(76, 1.4, 1.0), 0.0, gain=1.6)

# ---------- the arrangement ----------
bar = A0; n_bar = 0
while bar < OUT0:
    chord = CYC[((bar - A0) // 4) % 5]; end = min(bar + 4, OUT0); chorus = bar >= DROP; lv = level(bar, CRES)
    add("pad", strings(UPPER[chord], (end - bar) * VBEAT + 0.5, cut=1500 if not chorus else 2600, att=0.4), T(bar), gain=0.55 * lv)
    # melody: solo cello; violins an octave up join after 4 bars; at the drop add the lower octave (celli/brass) and a bell
    for off, m, ln in PHRASE[chord]:
        b = bar + off
        if BREAK0 <= b < DROP or b >= OUT0: continue
        add("lead", cello(m, ln * VBEAT + 0.3, 1.0), T(b), pan=-0.05, gain=2.0 * lv)
        add("lead", pluck_saw(m, 0.28, 1.0, cut=3600), T(b), pan=0.1, gain=0.45 * lv)                          # a little bow-attack bite
        if b >= A0 + 16: add("lead", cello(m + 12, ln * VBEAT + 0.3, 0.8, cut=3400, att=0.16), T(b), pan=0.25, gain=1.2 * lv)   # violins
        if chorus:
            add("lead", cello(m - 12, ln * VBEAT + 0.3, 0.9, cut=1300), T(b), pan=-0.25, gain=1.2 * lv)
            add("keys", bell(m + 12, 1.3, 0.6), T(b), pan=0.25, gain=0.3)
    # sub bass: down the lament line, on every video beat (verse) / the tresillo (chorus)
    hits = [0, .75, 1.5, 2, 2.75, 3.25, 3.5] if chorus else [0, 1, 2, 3]
    for h in hits:
        b = bar + h
        if b >= end: continue
        add("bass", sub808(BASS_NOTE[chord], 0.7), T(b), gain=(0.4 if BREAK0 <= b < DROP else 0.7))
    bar += 4

# staccato low-string pulse, toms, drums and the build
k = 0
while A0 + k * STEP < OUT0:
    b = A0 + k * STEP; step = k % 16; chord = CYC[(int(b - A0) // 4) % 5]; chorus = b >= DROP; brk = BREAK0 <= b < DROP; lv = level(b, CRES); k += 1
    if brk: continue
    root = BASS_NOTE[chord]; acc = step in (0, 4, 6, 10, 12)
    if chorus:
        add("arp", spic(root + 12, 0.95 if acc else 0.5), T(b), pan=-0.1, gain=0.4 * lv)
        if KICK[step]: add("drums", kick(), T(b), gain=0.9)
        if DEMBOW[step]: add("drums", tom(150, 0.3, 0.8), T(b), pan=0.1, gain=0.5)
        if HATS[step]: add("drums", hat(), T(b), pan=0.3, gain=0.18)
    else:
        if step % 2 == 0: add("arp", spic(root + 12, 0.95 if step % 4 == 0 else 0.55), T(b), pan=-0.1, gain=0.42 * lv)
        if b >= A0 + 8 and step % 2 == 1: add("arp", spic(root + 24, 0.3), T(b), pan=0.15, gain=0.25 * lv)          # a second, higher stab layer enters after two bars
        if step in (0, 8): add("drums", tom(92 if step == 0 else 110, 0.5, 0.9), T(b), gain=1.1 * lv)
        if step in (0, 8) and b >= A0 + 8: add("drums", kick(), T(b), gain=0.6)
        if b >= BUILD0 and step % 2 == 1: add("drums", hat(), T(b), pan=-0.2, gain=0.08 + 0.14 * (b - BUILD0) / (BREAK0 - BUILD0))
        if b >= BUILD0 + 2 and step % 4 == 2: add("drums", tom(130, 0.25, 0.7), T(b), gain=0.4 + 0.5 * (b - BUILD0) / (BREAK0 - BUILD0))
nb = int((T(DROP) - T(BREAK0)) * SR); u = np.arange(nb) / nb
nz = filt(rng.standard_normal((nb, 2)), lo=1800) * (u ** 2)[:, None]
sweep = np.sin(2 * np.pi * np.cumsum(220 + 1500 * u ** 2) / SR) * (u ** 2)
add("fx", nz / np.abs(nz).max(), T(BREAK0), gain=0.3); add("fx", sweep, T(BREAK0), gain=0.1)
add("drums", crash(), T(DROP), gain=0.6); add("drums", kick(), T(DROP), gain=1.1); add("drums", tom(70, 0.9, 1.0), T(DROP), gain=0.9)
add("bass", sub808(33, 1.4, 1.0), T(DROP), gain=0.55); add("keys", bell(81, 2.2, 1.0), T(DROP), pan=0.2, gain=0.22)

# ---------- outro: the cello alone, the phrase once, held on E ----------
for off, m, ln in PHRASE["Am"][:2] + [(2, 72, 1.5)]:
    add("lead", cello(m, ln * VBEAT * 1.4 + 0.5, 1.0), T(OUT0 + off), pan=-0.05, gain=1.6)
add("lead", cello(76, 4 * VBEAT + 1.6, 1.0, att=0.3), T(OUT0 + 4), pan=-0.05, gain=1.4)
add("pad", strings(UPPER["Am"], 4 * VBEAT + 0.6, cut=2000, att=0.3), T(OUT0), gain=0.8)
add("pad", strings([40, 52, 57, 64, 71], (TOTAL - OUT0 - 4) * VBEAT + 1.4, cut=2200, att=0.4, rel=1.3), T(OUT0 + 4), gain=0.9)
add("bass", sub808(45, 3.0), T(OUT0), gain=0.7); add("bass", sub808(40, 3.2), T(OUT0 + 4), gain=0.55)

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
LM = 0.18                                   # melody level: chosen so it sits ~4 dB above everything else in 250–3000 Hz (clear, but the bass keeps its share)
LEAD_PRES = filt(BUS["lead"], lo=1200, hi=4800, order=2)
mix = BUS["pad"] * 0.85 + (BUS["lead"] * 1.5 + LEAD_PRES * 0.7) * LM + BUS["arp"] + BUS["keys"] + BUS["drums"] + BUS["bass"] * 1.9 + BUS["fx"] + wet * 0.3
mix = filt(mix, lo=30, order=2); mix += 0.9 * filt(mix, lo=2500, order=2)
mix *= np.clip((DUR - tt) / 1.5, 0, 1)[:, None]
rms = np.sqrt(np.mean(mix ** 2)); mix *= 10 ** (-15.0 / 20) / max(rms, 1e-9)
ceil = 10 ** (-1 / 20)
mix = np.where(np.abs(mix) < 0.7 * ceil, mix, np.sign(mix) * (0.7 * ceil + 0.3 * ceil * np.tanh((np.abs(mix) - 0.7 * ceil) / (0.3 * ceil))))
def _band(x, lo=250, hi=3000):
    m = x.mean(axis=1); X = np.abs(np.fft.rfft(m)) ** 2; f = np.fft.rfftfreq(len(m), 1 / SR); return X[(f >= lo) & (f < hi)].sum()
_others = sum(_band(BUS[k]) for k in ("pad", "arp", "keys", "drums", "bass", "fx")); _lead = _band((BUS["lead"] * 1.5 + LEAD_PRES * 0.7) * LM)
print(f"melody share of the 250–3000 Hz band: {100 * _lead / (_lead + _others):.0f}%  (lead vs everything else: {10 * np.log10(_lead / _others):+.1f} dB)")
outp = ROOT / "build" / os.environ.get("BGM_OUT", "bgm.wav"); outp.parent.mkdir(exist_ok=True)
with wave.open(str(outp), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes())
print(f"bgm -> {outp} ({DUR:.2f}s, peak {20*np.log10(np.abs(mix).max()):.1f} dBFS, drop at {T(DROP):.2f}s)")
