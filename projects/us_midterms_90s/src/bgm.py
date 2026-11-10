"""Music for 《美国中期选举一次看懂》 — an election-night / documentary-explainer feel: A minor, electric piano, plucked-synth arpeggio,
808 sub bass and a Euclidean groove. numpy only, no sound effects, no vocals.
(The earlier bright G-major marimba version is kept in bgm_bright_g.py — the user found it childish.)

Layout (video beat = 60/66 s, music runs at double time = 132 BPM; one chord per 4-beat video bar):
  chords   Am – F – C – G
  hook     a 4-bar line on an electric piano in the mid register (D4–E5), built on the tresillo 3+3+2, mostly long notes, with a dotted-eighth echo
  arp      a plucked-synth arpeggio underneath: eighths in the verse, sixteenths with accents in the chorus
  bass     808 sub: on the beat in the verse, on the tresillo hits in the chorus
  drums    verse: kick on every video beat, soft clap on the dembow steps, hats;  chorus: kick E(4,16), dembow claps, E(7,16) hats
  build    the four beats before the drop get a rising hat roll
  DROP     video beat 44 (the Senate scale tips): two beats of breakdown (drums and hook out, pad + bass stay, riser) then crash + 808 hit + full groove
  outro    drums out, the hook once slowly, a last open Am chord with a bell
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

PROG = ["Am", "F", "C", "G"]
PAD = {"Am": [45, 57, 60, 64], "F": [41, 57, 60, 65], "C": [48, 55, 60, 64], "G": [43, 55, 59, 62]}
ARP = {"Am": [57, 60, 64, 69], "F": [57, 60, 65, 69], "C": [55, 60, 64, 67], "G": [55, 59, 62, 67]}      # chord tones around A3–A4 for the pluck arpeggio
ROOT_NOTE = {"Am": 45, "F": 41, "C": 48, "G": 43}
# hook on the tresillo 3+3+2 (offsets in video beats within a 4-beat bar): mostly long notes, mid register
HOOK = [
    [(0, 76, .75), (.75, 74, .75), (1.5, 72, .5), (2, 69, 1.5), (3.5, 71, .5)],
    [(0, 72, .75), (.75, 69, .75), (1.5, 72, .5), (2, 65, 1.5), (3.5, 67, .5)],
    [(0, 76, .75), (.75, 72, .75), (1.5, 76, .5), (2, 74, 1.5), (3.5, 72, .5)],
    [(0, 74, .75), (.75, 71, .75), (1.5, 67, .5), (2, 71, .75), (2.75, 74, .75), (3.5, 72, .5)],
]
OUTRO = [(0, 76, 1), (1, 72, 1), (2, 69, 2)]

# ---------- 0–1 s: a run-up that is already moving (808 pulse climbing into beat 4, kick, rising hats and a pluck run) ----------
add("pad", strings(PAD["Am"], 1.8, cut=3200, att=0.02, rel=0.6), 0, gain=1.0)
add("drums", crash(), 0, gain=0.3)
for i, m in enumerate((45, 45, 48, 52)): add("bass", sub808(m, 0.3, 1.0), i * 0.25, gain=0.95)           # 808 on every 16th-group of the second
for i, m in enumerate((57, 60, 64, 69, 64, 69, 72, 76)): add("arp", pluck_saw(m, 0.14, 0.5 + 0.06 * i, cut=3600), i * 0.125, pan=-0.3 + 0.08 * i, gain=0.4)
for i in (0, 4): add("drums", kick(), i * 0.125, gain=0.95)
for i in range(8): add("drums", hat(), i * 0.125 + 0.06, pan=0.3, gain=0.1 + 0.03 * i)
add("lead", epiano(76, 1.0), 0.0, pan=-0.1, gain=0.9); add("lead", epiano(74, 0.9), 0.5, pan=-0.1, gain=0.85)

# ---------- the groove, bar by bar ----------
bar = A0
while bar < OUT0:
    bi = ((bar - A0) // 4) % 4; chord = PROG[bi]; end = min(bar + 4, OUT0)
    chorus = bar >= DROP
    add("pad", strings(PAD[chord], (end - bar) * VBEAT + 0.4, cut=1700 if not chorus else 2800, att=0.25), T(bar), gain=0.75 if not chorus else 0.95)
    for off, m, ln in HOOK[bi]:
        b = bar + off
        if BREAK0 <= b < DROP or b >= OUT0: continue
        add("lead", epiano(m, max(0.5, ln * VBEAT * 1.4)), T(b), pan=-0.1, gain=0.9)
        if chorus: add("lead", bell(m + 12, 1.0, 0.5), T(b), pan=0.25, gain=0.25)
    # 808 bass: on every video beat in the verse, on the tresillo (0, .75, 1.5 | 2, 2.75, 3.5) in the chorus
    hits = [0, .75, 1.5, 2, 2.75, 3.25, 3.5] if chorus else [0, 1.5, 2, 3.5]
    for h in hits:
        b = bar + h
        if b >= end: continue
        low = BREAK0 <= b < DROP
        rn = ROOT_NOTE[chord] + (12 if (chorus and h in (.75, 2.75)) else 0)
        add("bass", sub808(rn, 0.7), T(b), gain=0.6 if low else 1.0)
        add("bass", pluck_saw(rn + 12, 0.28, 0.9, cut=650), T(b), gain=0.3 if low else 0.5)      # mid-bass layer (200–600 Hz) for phone speakers
    bar += 4

# ---------- arpeggio, drums, build ----------
k = 0
while A0 + k * STEP < OUT0:
    b = A0 + k * STEP; step = k % 16; k += 1
    chord = PROG[(int(b - A0) // 4) % 4]; chorus = b >= DROP; brk = BREAK0 <= b < DROP
    if brk: continue
    tones = ARP[chord]
    if chorus:
        idx = (k - 1) % 4
        add("arp", pluck_saw(tones[idx] + (12 if (k - 1) % 8 >= 4 else 0), 0.16, 0.9 if (k - 1) % 4 == 0 else 0.55, cut=4200), T(b), pan=-0.3 + 0.15 * idx, gain=0.4)
        if KICK[step]: add("drums", kick(), T(b), gain=0.95)
        if DEMBOW[step]: add("drums", clap(), T(b), pan=0.1, gain=0.42)
        if HATS[step]: add("drums", hat(), T(b), pan=0.3, gain=0.3)
        elif step % 2 == 1: add("drums", hat(), T(b), pan=-0.3, gain=0.1)
    else:
        if (k - 1) % 2 == 0: add("arp", pluck_saw(tones[((k - 1) // 2) % 4], 0.2, 0.6, cut=2200), T(b), pan=-0.2 + 0.1 * (((k - 1) // 2) % 4), gain=0.3)
        if (step in (0, 8)) if b < SC["C_balloons"][0] else KICK[step]: add("drums", kick(), T(b), gain=0.85)
        if DEMBOW[step] and b >= A0 + 8: add("drums", clap(), T(b), pan=0.2, gain=0.22)
        if step % 4 == 2: add("drums", hat(), T(b), pan=0.3, gain=0.16)
        if b >= BUILD0 and step % 2 == 1: add("drums", hat(), T(b), pan=-0.2, gain=0.1 + 0.12 * (b - BUILD0) / (BREAK0 - BUILD0))      # rising hat roll into the break
# riser and the re-entry
nb = int((T(DROP) - T(BREAK0)) * SR); u = np.arange(nb) / nb
nz = filt(rng.standard_normal((nb, 2)), lo=1800) * (u ** 2)[:, None]
sweep = np.sin(2 * np.pi * np.cumsum(220 + 1500 * u ** 2) / SR) * (u ** 2)
add("fx", nz / np.abs(nz).max(), T(BREAK0), gain=0.28); add("fx", sweep, T(BREAK0), gain=0.1)
add("drums", crash(), T(DROP), gain=0.55); add("drums", kick(), T(DROP), gain=1.1); add("bass", sub808(33, 1.2, 1.0), T(DROP), gain=0.7); add("keys", bell(81, 2.0, 1.0), T(DROP), pan=0.2, gain=0.22)

# ---------- outro ----------
for off, m, ln in OUTRO:
    add("lead", epiano(m, ln * VBEAT * 1.6 + 0.8), T(OUT0 + off), pan=-0.1, gain=0.85)
add("pad", strings(PAD["Am"], 4 * VBEAT + 0.6, cut=2200, att=0.3), T(OUT0), gain=0.9)
add("pad", strings([45, 57, 64, 71, 76], (TOTAL - OUT0 - 4) * VBEAT + 1.4, cut=2400, att=0.4, rel=1.3), T(OUT0 + 4), gain=1.0)
add("bass", sub808(45, 3.0), T(OUT0), gain=0.75); add("bass", sub808(45, 3.2), T(OUT0 + 4), gain=0.6)
add("keys", bell(88, 3.0, 1.0), T(OUT0 + 4), pan=0.2, gain=0.2)

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
mix = BUS["pad"] * 0.85 + BUS["lead"] * 1.1 + BUS["arp"] + BUS["keys"] + BUS["drums"] + BUS["bass"] * 1.9 + BUS["fx"] + wet * 0.3
mix = filt(mix, lo=30, order=2); mix += 0.9 * filt(mix, lo=2500, order=2)
mix *= np.clip((DUR - tt) / 1.5, 0, 1)[:, None]
rms = np.sqrt(np.mean(mix ** 2)); mix *= 10 ** (-15.0 / 20) / max(rms, 1e-9)
ceil = 10 ** (-1 / 20)
mix = np.where(np.abs(mix) < 0.7 * ceil, mix, np.sign(mix) * (0.7 * ceil + 0.3 * ceil * np.tanh((np.abs(mix) - 0.7 * ceil) / (0.3 * ceil))))
outp = ROOT / "build" / os.environ.get("BGM_OUT", "bgm.wav"); outp.parent.mkdir(exist_ok=True)
with wave.open(str(outp), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes())
print(f"bgm -> {outp} ({DUR:.2f}s, peak {20*np.log10(np.abs(mix).max()):.1f} dBFS, drop at {T(DROP):.2f}s)")
