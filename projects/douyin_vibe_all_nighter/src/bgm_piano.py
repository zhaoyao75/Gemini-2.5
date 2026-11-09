"""Music for 《熬一个通宵 ≈ 醉驾？》 — emotional piano with a building beat, 77 BPM, numpy only. No sound effects.

  0–1 s     low piano octaves + chord crash down with a sub boom and a cymbal
  A–B       solo piano hook (A minor, Am–F–C–G)
  C–D       heartbeat kick ("lub-dub"), low strings, bass
  E         claps on 2 & 4, driving piano eighths, strings swell
  F         drums pull out: accelerating snare roll + rising strings -> the DROP on beat 36,
            exactly when the breathalyser crosses the drunk-driving line
  drop–G    full drums, cymbals, bass, big strings, hook up an octave in octaves
  I–J       piano alone again, the harmony turns major (F–G–C) as the sun comes up; long final chord
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
DROP = F0 + 5                                    # = beat 36, a bar line; the picture crosses 80 mg here
DUR = T(TOTAL) + TL["tail_seconds"]
N = int(DUR * SR); tt = np.arange(N) / SR; rng = np.random.default_rng(36)
BUS = {k: np.zeros((N, 2)) for k in ("piano", "strings", "drums", "bass")}

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
    e = np.ones(n); na = max(1, int(a * SR)); nr = max(1, min(n, int(r * SR)))
    e[:na] = np.linspace(0, 1, na); e[-nr:] *= np.linspace(1, 0, nr); return e

# ---------- instruments ----------
HAM = filt(rng.standard_normal(int(0.02 * SR)), lo=800, hi=5000)
def piano(m, dur, vel=0.7):
    n = int(dur * SR); t = np.arange(n) / SR; f0 = hz(m); s = np.zeros(n)
    for h in range(1, 13):
        fh = f0 * h * np.sqrt(1 + 0.00035 * h * h)
        if fh > 11000: break
        a = (0.35 + 0.65 * vel) ** (h - 1) / h ** 1.05
        dec = 0.5 + 0.28 * h + f0 / 700
        s += a * np.sin(2 * np.pi * fh * t + rng.uniform(0, 6.28)) * (0.65 * np.exp(-t * dec * 2.5) + 0.35 * np.exp(-t * dec * 0.45))
    k = min(n, len(HAM)); s[:k] += HAM[:k] * 0.25 * vel * np.exp(-np.arange(k) / SR * 300)
    s *= env(n, 0.002, 0.12) * vel
    pan = np.clip((m - 64) / 30, -0.6, 0.6)
    return np.stack([s * np.sqrt(0.5 * (1 - pan)), s * np.sqrt(0.5 * (1 + pan))], 1)
def strings(notes, dur, att=0.6, bright=5000):
    n = int(dur * SR); t = np.arange(n) / SR; out = np.zeros((n, 2))
    for m in notes:
        for vi, d in enumerate((-0.07, 0.0, 0.07)):
            f = hz(m) * 2 ** (d / 12) * (1 + 0.0035 * np.sin(2 * np.pi * 5.1 * t + vi)); ph = 2 * np.pi * np.cumsum(f) / SR; s = np.zeros(n)
            for h in range(1, 9):
                if hz(m) * h > bright: break
                s += np.sin(h * ph) / h * (1 / (1 + (hz(m) * h / bright) ** 2))
            pan = (vi - 1) * 0.6; out[:, 0] += s * np.sqrt(0.5 * (1 - pan)); out[:, 1] += s * np.sqrt(0.5 * (1 + pan))
    out *= env(n, att, 0.7)[:, None]; return out / (np.abs(out).max() + 1e-9)
def kick(deep=1.0):
    n = int(0.6 * SR); t = np.arange(n) / SR
    return np.tanh(1.5 * (np.sin(2 * np.pi * np.cumsum(42 + 100 * np.exp(-t * 26)) / SR) * np.exp(-t * (5 / deep)) + 0.3 * rng.standard_normal(n) * np.exp(-t * 400)))
def clap(big=1.0):
    n = int(0.5 * SR); t = np.arange(n) / SR; nz = filt(rng.standard_normal(n), lo=900, hi=7000)
    e = sum(np.exp(-np.maximum(t - d, 0) * 60) * (t >= d) for d in (0, 0.01, 0.02)) + 0.7 * np.exp(-np.maximum(t - 0.03, 0) * (9 / big)) * (t >= 0.03)
    return nz / np.abs(nz).max() * e + 0.5 * np.sin(2 * np.pi * 180 * t) * np.exp(-t * 25)
def snare(v=1.0):
    n = int(0.18 * SR); t = np.arange(n) / SR; nz = filt(rng.standard_normal(n), lo=1200, hi=8000)
    return (nz / np.abs(nz).max() * np.exp(-t * 28) + 0.6 * np.sin(2 * np.pi * 200 * t) * np.exp(-t * 40)) * v
HH = filt(rng.standard_normal(int(0.3 * SR)), lo=7000); HH /= np.abs(HH).max()
def hat(): n = int(0.05 * SR); return HH[:n] * np.exp(-np.arange(n) / SR * 70)
def crash():
    n = int(2.5 * SR); t = np.arange(n) / SR; c = filt(rng.standard_normal((n, 2)), lo=4000); return c / np.abs(c).max() * np.exp(-t * 1.6)[:, None]
def sub(m, dur):
    n = int(dur * SR); t = np.arange(n) / SR; ph = 2 * np.pi * hz(m) * t
    return np.tanh(1.6 * (np.sin(ph) + 0.35 * np.sin(2 * ph))) * env(n, 0.006, 0.08) * np.exp(-t * 0.8)

# ---------- harmony & the hook ----------
CH = {"Am": [57, 60, 64], "F": [53, 57, 60], "C": [55, 60, 64], "G": [55, 59, 62]}
ROOTS = {"Am": 45, "F": 41, "C": 48, "G": 43}
PROG = ["Am", "F", "C", "G"]
HOOK = [[(0, 76, 1.5), (1.5, 74, .5), (2, 72, 1), (3, 71, .5), (3.5, 72, .5)],
        [(0, 69, 1.5), (1.5, 72, .5), (2, 77, 1.5), (3.5, 76, .5)],
        [(0, 76, 1), (1, 79, 1), (2, 76, .5), (2.5, 74, .5), (3, 72, 1)],
        [(0, 74, 1.5), (1.5, 71, .5), (2, 67, 1), (3, 74, 1)]]
def chord_at(beat): return PROG[int((beat - A0) // 4) % 4]

# ---------- 0–1 s: the hit ----------
for m, v in ((33, 0.9), (45, 0.9), (57, 0.8), (60, 0.8), (64, 0.8), (69, 0.7)): add("piano", piano(m, 3.0, v), 0.0, gain=0.9)
n = int(2.0 * SR); t = np.arange(n) / SR
add("drums", np.sin(2 * np.pi * np.cumsum(34 + 60 * np.exp(-t * 8)) / SR) * np.exp(-t * 2.2), 0, gain=0.9)
add("drums", crash(), 0, gain=0.35)
add("piano", piano(64, 0.6, 0.55), T(2.0)); add("piano", piano(67, 0.6, 0.6), T(3.0))           # pickup into the hook

# ---------- body (A .. G) ----------
for bar in range(A0, I0, 4):
    c = chord_at(bar); hk = HOOK[PROG.index(c)]
    climax = bar >= DROP
    end = min(bar + 4, I0)
    # left hand / chords
    if climax:
        for p in range(4):
            if bar + p < I0:
                for m in CH[c] + [ROOTS[c] - 12, ROOTS[c]]: add("piano", piano(m, BEAT * 1.1, 0.8), T(bar + p), gain=0.35)
    else:
        for m in [ROOTS[c] - 12, ROOTS[c]] + CH[c]: add("piano", piano(m, (end - bar) * BEAT + 0.4, 0.55), T(bar), gain=0.5)
    # hook (an octave up, in octaves, at the climax)
    for pos, m, ln in hk:
        if bar + pos >= I0: continue
        if climax:
            add("piano", piano(m + 12, ln * BEAT + 0.6, 0.95), T(bar + pos), gain=0.6); add("piano", piano(m, ln * BEAT + 0.6, 0.85), T(bar + pos), gain=0.45)
        else:
            add("piano", piano(m, ln * BEAT + 0.6, 0.78 if bar >= E0 else 0.72), T(bar + pos), gain=0.62)
    # driving eighths from E on (until the build strips it back)
    if E0 <= bar or (bar < E0 < end):
        tones = [ROOTS[c], CH[c][0], CH[c][1] + 12 if False else CH[c][1], CH[c][2]]
        for k in range(8):
            b8 = bar + k / 2
            if b8 < E0 or b8 >= I0: continue
            add("piano", piano(tones[k % 4], 0.5, 0.5 if not climax else 0.62), T(b8), gain=0.3)
    # strings
    if bar >= C0 - 3:
        lvl = 0.25 if bar < E0 else 0.45 if bar < F0 else 0.6 if bar < DROP else 0.9
        add("strings", strings([m - 12 for m in CH[c]] + ([m for m in CH[c]] if bar >= E0 else []), (end - bar) * BEAT + 0.6, att=0.5 if bar < DROP else 0.08), T(bar), gain=lvl)
    # bass
    if bar >= C0 - 3:
        if climax:
            for k in range(8):
                if bar + k / 2 < I0: add("bass", sub(ROOTS[c] - 12, 0.42), T(bar + k / 2), gain=0.55)
        else:
            add("bass", sub(ROOTS[c] - 12, (end - bar) * BEAT), T(bar), gain=0.45)
# rising strings over the build (F .. DROP)
nb = int((T(DROP) - T(F0)) * SR); tb = np.arange(nb) / SR; sw = np.zeros((nb, 2))
for m0 in (57, 64, 69):
    f = hz(m0) * 2 ** ((tb / tb[-1]) * 12 / 12 * 1.0); ph = 2 * np.pi * np.cumsum(f) / SR
    s = sum(np.sin(h * ph) / h for h in range(1, 7)) * (tb / tb[-1]) ** 1.6
    sw[:, 0] += s; sw[:, 1] += s
add("strings", sw / np.abs(sw).max(), T(F0), gain=0.55)

# ---------- drums ----------
for beat in range(C0, I0):
    rel = (beat - A0) % 4
    if beat < E0:                                    # heartbeat: lub-dub on 1 and 3
        if rel in (0, 2): add("drums", kick(1.3), T(beat), gain=0.7); add("drums", kick(1.0), T(beat + 0.3), gain=0.4)
    elif beat < F0:                                  # groove
        if rel in (0, 2): add("drums", kick(), T(beat), gain=0.8)
        if rel == 3: add("drums", kick(), T(beat + 0.5), gain=0.5)
        if rel in (1, 3): add("drums", clap(), T(beat), gain=0.5)
        for h in (0, 0.5): add("drums", hat(), T(beat + h), pan=0.3, gain=0.22 if h else 0.3)
    elif beat >= DROP:                               # climax
        if rel in (0, 2): add("drums", kick(), T(beat), gain=0.95)
        if rel in (0,) or beat == DROP: pass
        if rel in (1, 3): add("drums", clap(1.6), T(beat), gain=0.65)
        if rel == 2: add("drums", kick(), T(beat + 0.75), gain=0.55)
        for h in (0, 0.5): add("drums", hat(), T(beat + h), pan=0.3, gain=0.3 if h else 0.38)
for b0 in (C0 - 3, DROP, DROP + 4):
    if b0 < I0: add("drums", crash(), T(max(b0, A0)), gain=0.4 if b0 >= DROP else 0.22)
# snare roll: quarter -> eighth -> sixteenth -> 32nd, crescendo into the drop
roll = []
for b0, b1, step in ((F0, F0 + 2, 1.0), (F0 + 2, F0 + 3.5, 0.5), (F0 + 3.5, F0 + 4.5, 0.25), (F0 + 4.5, DROP, 0.125)):
    x = b0
    while x < b1 - 1e-9: roll.append(x); x += step
for x in roll: add("drums", snare(0.25 + 0.75 * ((x - F0) / (DROP - F0)) ** 1.5), T(x), pan=0.05, gain=0.55)

# ---------- I–J: sunrise, major key, piano alone ----------
I_SEQ = [(I0, "F", 1.5), (I0 + 1.5, "G", 1.5), (I0 + 3, "C", TOTAL - I0 - 3)]
for b0, c, ln in I_SEQ:
    for m in [ROOTS[c] - 12, ROOTS[c]] + CH[c] + ([67, 72] if c == "C" else []): add("piano", piano(m, ln * BEAT + 2.5, 0.6), T(b0), gain=0.5)
    add("strings", strings([m - 12 for m in CH[c]] + CH[c], ln * BEAT + 1.0, att=0.4, bright=6000), T(b0), gain=0.35)
for b0, m, ln in ((I0, 69, 1), (I0 + 1, 72, .5), (I0 + 1.5, 71, 1), (I0 + 2.5, 74, .5), (I0 + 3, 76, 2), (J0, 79, 1), (J0 + 1, 76, 1), (J0 + 2, 72, 2.5)):
    add("piano", piano(m, ln * BEAT + 1.2, 0.75), T(b0), gain=0.62)
for k, m in enumerate((84, 88, 91, 96)): add("piano", piano(m, 2.0, 0.5), T(I0 + 3.2) + 0.14 * k, pan=0.3, gain=0.3)   # sunrise sparkle

# ---------- mix ----------
irn = int(2.6 * SR); it = np.arange(irn) / SR
ir = filt(rng.standard_normal((irn, 2)), lo=200, hi=7000) * np.exp(-it / 0.75)[:, None]; ir /= np.sqrt((ir ** 2).sum(axis=0))
send = BUS["piano"] * 0.45 + BUS["strings"] * 0.6 + BUS["drums"] * 0.12
nf = 1 << (N + irn - 1).bit_length()
wet = np.stack([np.fft.irfft(np.fft.rfft(send[:, c], nf) * np.fft.rfft(ir[:, c], nf), nf)[:N] for c in range(2)], 1)
mix = BUS["piano"] + BUS["strings"] * 0.55 + BUS["drums"] + BUS["bass"] * 0.8 + wet * 0.35
mix = filt(mix, lo=30, order=2); mix += 0.4 * filt(mix, lo=3500, order=2)
mix *= np.clip((DUR - tt) / 1.5, 0, 1)[:, None]
rms = np.sqrt(np.mean(mix ** 2)); mix *= 10 ** (-15.5 / 20) / max(rms, 1e-9)
ceil = 10 ** (-1 / 20)
mix = np.where(np.abs(mix) < 0.7 * ceil, mix, np.sign(mix) * (0.7 * ceil + 0.3 * ceil * np.tanh((np.abs(mix) - 0.7 * ceil) / (0.3 * ceil))))
outp = ROOT / "build" / "bgm.wav"; outp.parent.mkdir(exist_ok=True)
with wave.open(str(outp), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes())
print(f"bgm -> {outp} ({DUR:.2f}s, peak {20*np.log10(np.abs(mix).max()):.1f} dBFS, drop at {T(DROP):.2f}s)")
