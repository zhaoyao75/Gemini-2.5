"""Music for 《熬一个通宵 ≈ 醉驾？》 — Latin dembow groove built from Euclidean rhythms, 77 BPM, numpy only. No sound effects.

Follows the reference: four layers on a 16-step bar, each an Euclidean rhythm
  KICK      E(4,16)  x...x...x...x...
  TRESILLO  E(3,8)   x.....x.....x...   -> 808 bass (root, root, fifth)
  CINQUILLO E(5,8)   x...x.x...x.x...   -> the hook: 5 marimba notes per bar, same rhythm every bar
  DEMBOW    snare    ...x..x....x..x.
Background-friendly: steady density, no silences, no drop; layers fade in gently.
  0–1 s   kalimba run + low marimba;  A–B kick, 808, hook, rim-click dembow
  C       full dembow snare;  E kalimba doubling + pad;  25.9 s (crossing 80 mg) a bell + brighter
  I–J     drums out, C-major hook on the same cinquillo rhythm, rolled final chord
"""
import json, wave
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
TL = json.loads((ROOT / "src" / "timeline.json").read_text())
SR, BEAT = 44100, 60 / TL["bpm"]
INTRO, TB = TL["intro_seconds"], TL["scenes_beats"]["D_title"][1]
def T(n): return n / TB * INTRO if n < TB else INTRO + (n - TB) * BEAT
SC, TOTAL = TL["scenes_beats"], TL["total_beats"]
A0, C0, E0, F0, G0, I0, J0 = (SC[k][0] for k in ("A_hook", "C_1997", "E_convert", "F_standard", "G_crash", "I_landing", "J_end"))
DROP = F0 + 5                                    # beat 36: the picture crosses 80 mg here
DUR = T(TOTAL) + TL["tail_seconds"]
N = int(DUR * SR); tt = np.arange(N) / SR; rng = np.random.default_rng(716)
BUS = {k: np.zeros((N, 2)) for k in ("mallets", "perc", "bass", "pad")}

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

# ---------- instruments ----------
CLICK = filt(rng.standard_normal(int(0.012 * SR)), lo=1500, hi=6000)
def marimba(m, vel=0.8, dur=1.6):
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(m)
    s = (np.sin(2 * np.pi * f * t) * np.exp(-t * (2.2 + f / 900))
         + 0.22 * vel * np.sin(2 * np.pi * f * 3.93 * t) * np.exp(-t * 16)
         + 0.06 * vel * np.sin(2 * np.pi * f * 9.2 * t) * np.exp(-t * 40))
    k = len(CLICK); s[:k] += CLICK * 0.3 * vel * np.exp(-np.arange(k) / SR * 500)
    return s * env(n, 0.001, 0.05) * vel
def kalimba(m, vel=0.7, dur=1.4):
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(m)
    s = (np.sin(2 * np.pi * f * t) * np.exp(-t * 3.2)
         + 0.25 * np.sin(2 * np.pi * f * 5.95 * t) * np.exp(-t * 22)
         + 0.08 * np.sin(2 * np.pi * f * 2.0 * t) * np.exp(-t * 6))
    s[:int(0.004 * SR)] += filt(rng.standard_normal(int(0.004 * SR)), lo=3000) * 0.15
    return s * env(n, 0.0008, 0.05) * vel
def bell(m, dur=3.5):
    n = int(dur * SR); t = np.arange(n) / SR; f = hz(m)
    return sum(a * np.sin(2 * np.pi * f * r * t) * np.exp(-t * d) for r, a, d in ((1, 1, 1.2), (2.76, 0.4, 2.5), (5.4, 0.2, 5), (8.9, 0.1, 9))) * env(n, 0.001, 0.2)
def conga(high=True):
    n = int(0.35 * SR); t = np.arange(n) / SR; f0 = 330 if high else 215
    s = np.sin(2 * np.pi * np.cumsum(f0 * (1 + 0.15 * np.exp(-t * 40))) / SR) * np.exp(-t * (14 if high else 10))
    return s + filt(rng.standard_normal(n), lo=1500, hi=5000) * np.exp(-t * 180) * 0.25
SH = filt(rng.standard_normal(int(0.12 * SR)), lo=5000, hi=11000); SH /= np.abs(SH).max()
def shaker(acc=False):
    n = len(SH); t = np.arange(n) / SR
    return SH * np.minimum(1, t / 0.006) * np.exp(-t * (28 if acc else 45))
def rim_click():
    n = int(0.06 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1700 * t) + 0.5 * np.sin(2 * np.pi * 2600 * t)) * np.exp(-t * 90)
def kick():
    n = int(0.4 * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(52 + 60 * np.exp(-t * 28)) / SR) * np.exp(-t * 9) * env(n, 0.001, 0.03)
def snap():
    n = int(0.2 * SR); t = np.arange(n) / SR; nz = filt(rng.standard_normal(n), lo=1500, hi=6000)
    return nz / np.abs(nz).max() * np.exp(-t * 38) + 0.3 * np.sin(2 * np.pi * 1100 * t) * np.exp(-t * 60)
def bass(m, dur):
    n = int(dur * SR); t = np.arange(n) / SR; ph = 2 * np.pi * hz(m) * t
    return (np.sin(ph) + 0.3 * np.sin(2 * ph) + 0.1 * np.sin(3 * ph)) * np.exp(-t * 2.5) * env(n, 0.004, 0.06)
def pad(notes, dur, att=0.8):
    n = int(dur * SR); t = np.arange(n) / SR; out = np.zeros((n, 2))
    for m in notes:
        for vi, d in enumerate((-0.06, 0.06)):
            f = hz(m) * 2 ** (d / 12); s = sum(np.sin(2 * np.pi * f * h * t + rng.uniform(0, 6)) / h ** 1.6 for h in (1, 2, 3))
            pan = -0.5 if vi == 0 else 0.5; out[:, 0] += s * np.sqrt(0.5 * (1 - pan)); out[:, 1] += s * np.sqrt(0.5 * (1 + pan))
    out *= env(n, att, 1.0)[:, None]; return out / (np.abs(out).max() + 1e-9)

# ---------- harmony, rhythms, the hook ----------
PROG = ["Am7", "Fmaj7", "C", "G"]
CH = {"Am7": [57, 60, 64, 67], "Fmaj7": [53, 57, 60, 64], "C": [55, 60, 64, 67], "G": [55, 59, 62, 67],
      "F": [53, 57, 60, 65], "G_": [55, 59, 62, 67], "C_": [52, 55, 60, 64]}
ROOTS = {"Am7": 45, "Fmaj7": 41, "C": 48, "G": 43, "F": 41, "G_": 43, "C_": 48}
def chord_at(beat): return PROG[int((beat - A0) // 4) % 4]
def level(b, pts):                                                      # smooth fade-in curves for layers
    xs, ys = zip(*pts); return float(np.interp(b, xs, ys))

# ---------- 0–1 s: kalimba run + low marimba ----------
for k, m in enumerate((57, 60, 62, 64, 67, 69, 72, 76)):
    add("mallets", kalimba(m + 12, 0.55 + 0.04 * k, 1.6), 0.0 + k * 0.105, pan=-0.4 + 0.1 * k, gain=0.7)
add("mallets", marimba(45, 1.0, 2.5), 0, gain=0.9); add("mallets", marimba(57, 0.9, 2.0), 0, gain=0.5)
add("bass", bass(33, 1.2), 0, gain=0.6)
for k in range(8): add("perc", shaker(k % 2 == 0), T(k * 0.5), gain=0.06 + 0.03 * k)

# ---------- dembow groove (A .. I): the four Euclidean layers of the reference ----------
KICK      = euclid(4, 16)                                    # x...x...x...x...
TRESILLO  = [i % 2 == 0 and euclid(3, 8)[i // 2] for i in range(16)]           # x.....x.....x...
_c = euclid(5, 8); _c = _c[2:] + _c[:2]                     # rotate to the classic cinquillo x.xx.xx.
CINQUILLO = [i % 2 == 0 and _c[i // 2] for i in range(16)]                     # x...x.x...x.x...
DEMBOW    = [i in (3, 6, 11, 14) for i in range(16)]                           # ...x..x....x..x.
HOOK = {"Am7": [76, 79, 76, 74, 72], "Fmaj7": [76, 79, 76, 74, 72],            # 5 notes on the 5 cinquillo hits
        "C": [76, 79, 81, 79, 76], "G": [74, 79, 74, 71, 74]}
def dsnare():
    n = int(0.22 * SR); t = np.arange(n) / SR; nz = filt(rng.standard_normal(n), lo=1800, hi=9000)
    return nz / np.abs(nz).max() * np.exp(-t * 30) + 0.55 * np.sin(2 * np.pi * np.cumsum(240 + 80 * np.exp(-t * 60)) / SR) * np.exp(-t * 28)
def b808(m, dur):
    n = int(dur * SR); t = np.arange(n) / SR; ph = 2 * np.pi * np.cumsum(hz(m) * (1 + 0.25 * np.exp(-t * 40))) / SR
    return np.tanh(1.8 * (np.sin(ph) + 0.25 * np.sin(2 * ph))) * np.exp(-t * 1.8) * env(n, 0.003, 0.05)
for step in range(int((I0 - A0) * 4)):
    b = A0 + step / 4; s16 = step % 16; c = chord_at(b)
    # KICK E(4,16)
    if KICK[s16]: add("perc", kick(), T(b), gain=level(b, [(A0, 0.4), (C0, 0.6), (DROP, 0.68)]))
    # TRESILLO E(3,8) -> 808 bass: root, root, fifth
    if TRESILLO[s16]:
        m = ROOTS[c] - 12 + (7 if s16 == 12 else 0)
        add("bass", b808(m, BEAT * (1.4 if s16 < 12 else 0.95)), T(b), gain=level(b, [(A0, 0.45), (C0, 0.55)]))
    # CINQUILLO E(5,8) -> the hook on marimba (doubled an octave up after the crossing)
    if CINQUILLO[s16]:
        j = sum(CINQUILLO[:s16]); m = HOOK[c][j]
        add("mallets", marimba(m, 0.9 if j == 0 else 0.8, 1.4), T(b), pan=float(np.clip((m - 74) / 16, -0.35, 0.35)), gain=0.7)
        add("mallets", kalimba(m + 12, 0.5), T(b), pan=0.3, gain=level(b, [(A0, 0.1), (E0, 0.18), (DROP, 0.28)]))
    # DEMBOW snare (rim-click before the research section, full snare from C)
    if DEMBOW[s16]:
        if b < C0: add("perc", rim_click(), T(b), pan=0.2, gain=0.3)
        else: add("perc", dsnare(), T(b), pan=0.05, gain=level(b, [(C0, 0.32), (E0, 0.4), (DROP, 0.46)]))
    # glue: 8th-note shaker with 16th ghosts
    if s16 % 2 == 0 or b >= E0: add("perc", shaker(s16 % 4 == 2), T(b), pan=-0.3, gain=level(b, [(A0, 0.28), (C0, 0.4), (DROP, 0.5)]) * (1 if s16 % 2 == 0 else 0.5))

# pad from E, a touch brighter after the drop
for bar in range(E0 - (E0 - A0) % 4, I0, 4):
    c = chord_at(bar); end = min(bar + 4, I0); st = max(bar, E0)
    add("pad", pad(CH[c] + [CH[c][1] + 12], (end - st) * BEAT + 1.0, att=0.6), T(st), gain=0.14 if bar < DROP else 0.2)
# the crossing: one bell, no gap, no drop
add("mallets", bell(88), T(DROP), pan=0.2, gain=0.22); add("mallets", bell(81), T(DROP) + 0.02, pan=-0.2, gain=0.16)

# ---------- I–J: major, drums out, the hook once more ----------
I_SEQ = [(I0, "F", 1.5), (I0 + 1.5, "G_", 1.5), (I0 + 3, "C_", TOTAL - I0 - 3)]
for b0, c, ln in I_SEQ:
    add("pad", pad(CH[c] + [CH[c][2] + 12], ln * BEAT + 2.0, att=0.3), T(b0), gain=0.2)
    add("bass", bass(ROOTS[c] - 12, ln * BEAT + 0.6), T(b0), gain=0.5)
C_PENTA = [60, 62, 64, 67, 69, 72, 74, 76, 79, 81, 84]                   # C major pentatonic
END_HOOK = {I0: [76, 79, 76, 74, 72], J0: [76, 79, 81, 79, 72]}
for bar0 in (I0, J0):
    for step in range(16):
        b = bar0 + step / 4
        if b >= TOTAL - 0.25: continue
        if CINQUILLO[step]:
            j = sum(CINQUILLO[:step]); m = END_HOOK[bar0][j]; last = bar0 == J0 and j == 4
            add("mallets", marimba(m, 0.75, 2.4 if last else 1.4), T(b), gain=0.6 if bar0 == I0 else 0.5)
        if step % 2 == 0 and b < J0 + 2: add("perc", shaker(step % 4 == 2), T(b), pan=-0.3, gain=0.3 if bar0 == I0 else 0.18)
for k, m in enumerate((48, 55, 60, 64, 67, 72)):                         # final rolled chord
    add("mallets", marimba(m, 0.7, 2.5), T(J0 + 2.5) + 0.06 * k, pan=-0.3 + 0.12 * k, gain=0.4)

# ---------- mix ----------
irn = int(1.8 * SR); it = np.arange(irn) / SR
ir = filt(rng.standard_normal((irn, 2)), lo=300, hi=7000) * np.exp(-it / 0.4)[:, None]; ir /= np.sqrt((ir ** 2).sum(axis=0))
send = BUS["mallets"] * 0.4 + BUS["pad"] * 0.5 + BUS["perc"] * 0.15
nf = 1 << (N + irn - 1).bit_length()
wet = np.stack([np.fft.irfft(np.fft.rfft(send[:, c], nf) * np.fft.rfft(ir[:, c], nf), nf)[:N] for c in range(2)], 1)
mix = BUS["mallets"] + BUS["perc"] + BUS["bass"] * 0.7 + BUS["pad"] + wet * 0.3
mix = filt(mix, lo=35, order=2); mix += 0.7 * filt(mix, lo=2500, order=2)
mix *= np.clip((DUR - tt) / 1.5, 0, 1)[:, None]
rms = np.sqrt(np.mean(mix ** 2)); mix *= 10 ** (-16.3 / 20) / max(rms, 1e-9)
ceil = 10 ** (-1 / 20)
mix = np.where(np.abs(mix) < 0.7 * ceil, mix, np.sign(mix) * (0.7 * ceil + 0.3 * ceil * np.tanh((np.abs(mix) - 0.7 * ceil) / (0.3 * ceil))))
outp = ROOT / "build" / "bgm.wav"; outp.parent.mkdir(exist_ok=True)
with wave.open(str(outp), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes())
print(f"bgm -> {outp} ({DUR:.2f}s, peak {20*np.log10(np.abs(mix).max()):.1f} dBFS, crossing at {T(DROP):.2f}s)")
