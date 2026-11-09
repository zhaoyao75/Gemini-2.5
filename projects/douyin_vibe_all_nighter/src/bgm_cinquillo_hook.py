"""Music for 《熬一个通宵 ≈ 醉驾？》 — up-tempo Latin pop on the dembow, after the user's reference clip. numpy only, no sound effects.

Reference (measured): ~132 BPM, four-on-the-floor kick, heavy 808, F major / D minor, a sung hook on the cinquillo.
Here: the video's 77 BPM grid played double-time (154 BPM feel), so every scene change still lands on a beat.
One music bar = 16 steps = 2 video beats. Four Euclidean layers, as in the reference:
  KICK      E(4,16)  x...x...x...x...
  TRESILLO  E(3,8)   x.....x.....x...   -> 808 bass
  CINQUILLO E(5,8)   x...x.x...x.x...   -> the hook, sung by a synthetic "vocal" (formant) lead
  DEMBOW    snare    ...x..x....x..x.
Harmony: Dm – B♭ – F – C, one chord per video bar. Hook = 2 music bars: the first identical every time, the second answers.
  0–1 s   vocal chord + 808 boom;  A–B kick, 808, hook;  C +dembow snare, chord plucks;  E +16th hats, pad
  25.9 s  (picture crosses 80 mg) fill, bell, hook doubled an octave up, no gap
  I–J     drums out, F major, the hook once more, soft ending
"""
import json, os, wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
TL = json.loads((ROOT / "src" / "timeline.json").read_text())
SR, VBEAT = 44100, 60 / float(os.environ.get("VIDEO_BPM", TL["bpm"]))   # VIDEO_BPM=66 -> the music runs at 132 BPM
INTRO, TB = TL["intro_seconds"], TL["scenes_beats"]["D_title"][1]
def T(n): return n / TB * INTRO if n < TB else INTRO + (n - TB) * VBEAT
SC, TOTAL = TL["scenes_beats"], TL["total_beats"]
A0, C0, E0, F0, G0, I0, J0 = (SC[k][0] for k in ("A_hook", "C_1997", "E_convert", "F_standard", "G_crash", "I_landing", "J_end"))
DROP = F0 + 5                                    # video beat 36: the picture crosses 80 mg here
STEP = 1 / 8                                     # one 16th of the double-time bar, in video beats
DUR = T(TOTAL) + TL["tail_seconds"]
N = int(DUR * SR); tt = np.arange(N) / SR; rng = np.random.default_rng(132)
BUS = {k: np.zeros((N, 2)) for k in ("vox", "keys", "drums", "bass", "pad")}

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
    """Euclidean rhythm E(k,n): k hits spread as evenly as possible over n steps (Toussaint)"""
    pat = [((i * k) // n) != (((i - 1) * k) // n) if i else True for i in range(n)]
    return pat[-rot:] + pat[:-rot] if rot else pat

KICK = euclid(4, 16)
TRESILLO = [i % 2 == 0 and euclid(3, 8)[i // 2] for i in range(16)]
_c = euclid(5, 8); _c = _c[2:] + _c[:2]
CINQUILLO = [i % 2 == 0 and _c[i // 2] for i in range(16)]
DEMBOW = [i in (3, 6, 11, 14) for i in range(16)]
CQ_LEN = [4, 2, 4, 2, 4]                         # steps until the next cinquillo hit

# ---------- instruments ----------
VOWELS = {"a": [(800, 80, 1.0), (1150, 90, 0.5), (2900, 120, 0.25), (3900, 130, 0.12)],
          "o": [(450, 70, 1.0), (800, 80, 0.4), (2830, 100, 0.15), (3800, 120, 0.08)],
          "e": [(400, 60, 1.0), (1700, 90, 0.45), (2600, 100, 0.3), (3900, 120, 0.12)]}
def vox(m, dur, vowel="a", vib=True):
    """synthetic sung vowel: band-limited pulse train through four formant peaks"""
    n = int(dur * SR); t = np.arange(n) / SR
    f0 = hz(m) * (1 + (0.012 * np.sin(2 * np.pi * 5.6 * t) * np.clip((t - 0.12) / 0.15, 0, 1) if vib else 0)) * (1 - 0.02 * np.exp(-t * 30))
    ph = 2 * np.pi * np.cumsum(f0) / SR; src = np.zeros(n)
    for h in range(1, 40):
        if hz(m) * h > 8000: break
        src += np.sin(h * ph) / h ** 0.9
    src += 0.04 * rng.standard_normal(n)                              # breath
    X = np.fft.rfft(src); f = np.fft.rfftfreq(n, 1 / SR)
    G = sum(a / (1 + ((f - fc) / bw) ** 2) for fc, bw, a in VOWELS[vowel]) + 0.02
    s = np.fft.irfft(X * G, n=n)
    s *= env(n, 0.015, 0.06); return s / (np.abs(s).max() + 1e-9)
def pluck(m, dur=0.4, bright=1.0):
    n = int(dur * SR); t = np.arange(n) / SR; s = np.zeros(n)
    for h in range(1, 12):
        if hz(m) * h > 11000: break
        s += np.sin(2 * np.pi * hz(m) * h * t + rng.uniform(0, 6)) / h * np.exp(-t * (7 + h * 3 / bright))
    return s * env(n, 0.001, 0.04)
def bell(m, dur=3.0):
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(m)
    return sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * d) for r, a, d in ((1, 1, 1.4), (2.76, 0.4, 3), (5.4, 0.2, 6))) * env(n, 0.001, 0.2)
def kick():
    n = int(0.32 * SR); t = np.arange(n) / SR
    body = np.sin(2 * np.pi * np.cumsum(50 + 150 * np.exp(-t * 38)) / SR) * np.exp(-t * 11)
    return np.tanh(2.2 * (body + filt(rng.standard_normal(n), lo=2500) * np.exp(-t * 600) * 0.5)) * env(n, 0.0005, 0.02)
def snare():
    n = int(0.2 * SR); t = np.arange(n) / SR; nz = filt(rng.standard_normal(n), lo=1800, hi=10000)
    return nz / np.abs(nz).max() * np.exp(-t * 26) + 0.6 * np.sin(2 * np.pi * np.cumsum(230 + 90 * np.exp(-t * 60)) / SR) * np.exp(-t * 30)
def rim():
    n = int(0.05 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1750 * t) + 0.5 * np.sin(2 * np.pi * 2650 * t)) * np.exp(-t * 100)
HH = filt(rng.standard_normal(int(0.3 * SR)), lo=7000); HH /= np.abs(HH).max()
def hat(open_=False):
    n = int((0.16 if open_ else 0.04) * SR); return HH[:n] * np.exp(-np.arange(n) / SR * (18 if open_ else 90))
def b808(m, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    ph = 2 * np.pi * np.cumsum(hz(m) * (1 + 0.6 * np.exp(-t * 35))) / SR
    return np.tanh(2.0 * (np.sin(ph) + 0.15 * np.sin(2 * ph))) * np.exp(-t * 1.2) * env(n, 0.002, 0.04)
def pad(notes, dur, att=0.4):
    n = int(dur * SR); t = np.arange(n) / SR; out = np.zeros((n, 2))
    for m in notes:
        for vi, d in enumerate((-0.08, 0.08)):
            f = hz(m) * 2 ** (d / 12); s = sum(np.sin(2 * np.pi * f * h * t + rng.uniform(0, 6)) / h ** 1.5 for h in (1, 2, 3, 4))
            pan = -0.6 if vi == 0 else 0.6; out[:, 0] += s * np.sqrt(0.5 * (1 - pan)); out[:, 1] += s * np.sqrt(0.5 * (1 + pan))
    out *= env(n, att, 0.8)[:, None]; return out / (np.abs(out).max() + 1e-9)
def crash():
    n = int(2.2 * SR); t = np.arange(n) / SR; c = filt(rng.standard_normal((n, 2)), lo=4000); return c / np.abs(c).max() * np.exp(-t * 1.8)[:, None]

# ---------- harmony & hook (D minor) ----------
PROG = ["Dm", "Bb", "F", "C"]
CH = {"Dm": [62, 65, 69], "Bb": [58, 62, 65], "F": [60, 65, 69], "C": [60, 64, 67]}
ROOTS = {"Dm": 38, "Bb": 34, "F": 41, "C": 36}
CALL = [69, 69, 67, 65, 62]                                  # bar 1, the same every time
ANSWER = {"Dm": [65, 67, 69, 72, 69], "Bb": [65, 67, 69, 70, 69], "F": [65, 67, 69, 72, 74], "C": [64, 67, 69, 67, 64]}
SYL = ["a", "o", "e", "a", "o"]
def chord_at(vb): return PROG[int((vb - A0) // 4) % 4]
def level(b, pts): xs, ys = zip(*pts); return float(np.interp(b, xs, ys))

# ---------- 0–1 s: the hit ----------
add("bass", b808(38, 1.0), 0, gain=0.9); add("drums", kick(), 0, gain=0.9); add("drums", crash(), 0, gain=0.35)
for k in range(4): add("drums", snare(), T(2 + k * 0.5), gain=0.12 + 0.08 * k)          # small fill into the groove

# ---------- groove (A .. I) ----------
for k in range(int((I0 - A0) / STEP)):
    vb = A0 + k * STEP; s16 = k % 16; mbar = k // 16; c = chord_at(vb)
    after = vb >= DROP
    if KICK[s16]: add("drums", kick(), T(vb), gain=level(vb, [(A0, 0.75), (C0, 0.85), (DROP, 0.95)]))
    if TRESILLO[s16]:
        ln = 6 if s16 < 12 else 4
        add("bass", b808(ROOTS[c] + (7 if s16 == 12 and mbar % 2 else 0), ln * STEP * VBEAT * 0.95), T(vb), gain=0.8)
    if CINQUILLO[s16]:
        j = sum(CINQUILLO[:s16]); m = (CALL if mbar % 2 == 0 else ANSWER[c])[j]
        ln = CQ_LEN[j] * STEP * VBEAT * 0.92
        add("keys", pluck(m, 0.34, 1.2), T(vb), pan=-0.3, gain=level(vb, [(A0, 0.7), (C0, 0.8)]))
    if DEMBOW[s16]:
        if vb < C0: add("drums", rim(), T(vb), pan=0.2, gain=0.35)
        else: add("drums", snare(), T(vb), pan=0.05, gain=level(vb, [(C0, 0.45), (E0, 0.55)]))
    # hats: 8ths, 16ths from E, an open hat late in the bar
    if s16 % 2 == 0 or vb >= E0: add("drums", hat(), T(vb), pan=0.3, gain=(0.7 if s16 % 2 == 0 else 0.38))
    if vb >= C0 and s16 == 14: add("drums", hat(True), T(vb), pan=-0.2, gain=0.8)
    # chord plucks on the off-beats from C
    if vb >= C0 and s16 in (2, 10):
        for m in CH[c]: add("keys", pluck(m, 0.35, 1.0), T(vb), pan=0.25, gain=0.3)
# pad from E
for vb in range(E0 - (E0 - A0) % 4, I0, 4):
    c = chord_at(vb); st = max(vb, E0); end = min(vb + 4, I0)
    add("pad", pad(CH[c] + [CH[c][0] + 12], (end - st) * VBEAT + 0.5), T(st), gain=0.12 if vb < DROP else 0.17)
# fill + bell at the crossing (no gap)
for k in range(8): add("drums", snare(), T(DROP - 1 + k * STEP), gain=0.15 + 0.05 * k)
add("drums", crash(), T(DROP), gain=0.4); add("keys", bell(86), T(DROP), pan=0.2, gain=0.25)

# ---------- I–J: F major, drums out, the hook once more ----------
for vb, c, ln in ((I0, "Bb", 1.5), (I0 + 1.5, "C", 1.5), (I0 + 3, "F", TOTAL - I0 - 3)):
    add("pad", pad(CH[c] + [CH[c][1] + 12], ln * VBEAT + 1.5, att=0.2), T(vb), gain=0.2)
    add("bass", b808(ROOTS[c], ln * VBEAT), T(vb), gain=0.55)
add("drums", crash(), T(I0), gain=0.25)
END = CALL + [65, 67, 69, 72, 72]                            # call, then resolve up to F's fifth/root
for k in range(32):
    vb = I0 + k * STEP; s16 = k % 16
    if CINQUILLO[s16] and vb < TOTAL - 0.5:
        j = sum(CINQUILLO[:s16]) + 5 * (k // 16); last = j == 9
        pass
    if s16 % 2 == 0 and vb < J0 + 2: add("drums", hat(), T(vb), pan=0.3, gain=0.1)
for k, m in enumerate((53, 60, 65, 69, 72, 77)): add("keys", pluck(m, 1.8, 0.6), T(J0 + 1) + 0.05 * k, pan=-0.3 + 0.12 * k, gain=0.25)

# ---------- mix ----------
irn = int(1.6 * SR); it = np.arange(irn) / SR
ir = filt(rng.standard_normal((irn, 2)), lo=300, hi=7000) * np.exp(-it / 0.35)[:, None]; ir /= np.sqrt((ir ** 2).sum(axis=0))
send = BUS["keys"] * 0.4 + BUS["pad"] * 0.4 + BUS["drums"] * 0.05
nf = 1 << (N + irn - 1).bit_length()
wet = np.stack([np.fft.irfft(np.fft.rfft(send[:, c], nf) * np.fft.rfft(ir[:, c], nf), nf)[:N] for c in range(2)], 1)
sc = np.ones(N)                                               # light sidechain on pad/keys from the kick
for k in range(int((I0 - A0) / STEP)):
    if KICK[k % 16]:
        i = int(T(A0 + k * STEP) * SR); n = min(int(0.2 * SR), N - i); e = np.arange(n) / SR
        sc[i:i + n] = np.minimum(sc[i:i + n], 1 - 0.35 * np.exp(-e / 0.06))
for b in ("pad", "keys"): BUS[b] *= sc[:, None]
BUS["bass"] = filt(BUS["bass"], lo=30, order=2)
mix = BUS["keys"] + BUS["drums"] + BUS["bass"] * 0.7 + BUS["pad"] + wet * 0.3
mix = filt(mix, lo=28, order=2); mix += 0.9 * filt(mix, lo=2500, order=2)
mix *= np.clip((DUR - tt) / 1.5, 0, 1)[:, None]
rms = np.sqrt(np.mean(mix ** 2)); mix *= 10 ** (-15.0 / 20) / max(rms, 1e-9)
ceil = 10 ** (-1 / 20)
mix = np.where(np.abs(mix) < 0.7 * ceil, mix, np.sign(mix) * (0.7 * ceil + 0.3 * ceil * np.tanh((np.abs(mix) - 0.7 * ceil) / (0.3 * ceil))))
outp = ROOT / "build" / os.environ.get("BGM_OUT", "bgm.wav"); outp.parent.mkdir(exist_ok=True)
with wave.open(str(outp), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes())
print(f"bgm -> {outp} ({DUR:.2f}s, peak {20*np.log10(np.abs(mix).max()):.1f} dBFS, crossing at {T(DROP):.2f}s)")
