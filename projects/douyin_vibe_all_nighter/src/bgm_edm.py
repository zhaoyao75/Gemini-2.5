"""Music for 《熬一个通宵 ≈ 醉驾？》 — EDM, 77 BPM grid (drop feels like 154 BPM double-time), numpy only. No sound effects.

  0–1 s     impact: sub boom + full supersaw stab + crash, then a short riser into the hook
  A–B       THE RIFF (1-bar, same rhythm every bar, repeats to the end) on a square lead, filtered chords, soft quarter kick (filter slowly opens)
  C–D       four-on-the-floor, offbeat hats, offbeat bass
  E         claps, open hats, filter wider, lead doubles the pluck
  F         build: noise riser + pitch riser + accelerating snare roll + filter sweep,
            half a beat of silence, then the DROP on beat 36 = the breathalyser crossing 80 mg
  drop–G    double-time kick, pumping supersaw chords, supersaw lead hook up an octave, reese bass
  I–J       downlifter, drums out, major F–G–C pads + pluck sparkles, soft ending
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
N = int(DUR * SR); tt = np.arange(N) / SR; rng = np.random.default_rng(154)
BUS = {k: np.zeros((N, 2)) for k in ("synth", "lead", "drums", "bass", "fx")}

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
def sweep_lp(x, cutoff_fn, order=2):
    """time-varying low-pass via STFT; cutoff_fn(seconds array) -> Hz"""
    W, H = 2048, 512; win = np.hanning(W); f = np.fft.rfftfreq(W, 1 / SR)
    pad = np.vstack([np.zeros((W, 2)), x, np.zeros((W, 2))]); out = np.zeros_like(pad); norm = np.zeros(len(pad))
    for s in range(0, len(pad) - W, H):
        fc = cutoff_fn(np.array([(s + W / 2 - W) / SR]))[0]
        G = 1 / np.sqrt(1 + (f / fc) ** (2 * order))
        seg = pad[s:s + W] * win[:, None]
        out[s:s + W] += np.fft.irfft(np.fft.rfft(seg, axis=0) * G[:, None], n=W, axis=0) * win[:, None]
        norm[s:s + W] += win ** 2
    return (out / np.maximum(norm, 1e-6)[:, None])[W:W + len(x)]

# ---------- instruments ----------
def saw(f, n, phase=0.0):
    return 2 * np.mod(np.cumsum(np.broadcast_to(f, (n,)) / SR) + phase, 1.0) - 1
def supersaw(notes, dur, att=0.005, rel=0.15, voices=7, spread=0.22, bright=9000):
    n = int(dur * SR); out = np.zeros((n, 2))
    for m in notes:
        for v in range(voices):
            d = (v - (voices - 1) / 2) / ((voices - 1) / 2) * spread
            s = saw(hz(m) * 2 ** (d / 12), n, rng.uniform())
            pan = (v - (voices - 1) / 2) / ((voices - 1) / 2) * 0.8
            out[:, 0] += s * np.sqrt(0.5 * (1 - pan)); out[:, 1] += s * np.sqrt(0.5 * (1 + pan))
    out = filt(out, hi=bright, order=2) * env(n, att, rel)[:, None]
    return out / (len(notes) * voices) ** 0.5 / 3
def pluck(m, dur=0.45, bright=1.0):
    n = int(dur * SR); t = np.arange(n) / SR; s = np.zeros(n)
    for h in range(1, 14):
        if hz(m) * h > 12000: break
        s += np.sin(2 * np.pi * hz(m) * h * t + rng.uniform(0, 6.28)) / h * np.exp(-t * (6 + h * 3.2 / bright))
    s += 0.3 * np.sin(2 * np.pi * hz(m) * 2.002 * t) * np.exp(-t * 9)
    return s * env(n, 0.001, 0.05)
def kick(punch=1.0, length=0.45):
    n = int(length * SR); t = np.arange(n) / SR
    body = np.sin(2 * np.pi * np.cumsum(48 + 140 * np.exp(-t * 32)) / SR) * np.exp(-t * 7)
    click = filt(rng.standard_normal(n), lo=2000) * np.exp(-t * 500) * 0.4
    return np.tanh(1.8 * punch * (body + click)) * env(n, 0.0005, 0.03)
def clap(big=1.0):
    n = int(0.45 * SR); t = np.arange(n) / SR; nz = filt(rng.standard_normal(n), lo=1000, hi=9000)
    e = sum(np.exp(-np.maximum(t - d, 0) * 70) * (t >= d) for d in (0, 0.009, 0.018)) + 0.8 * np.exp(-np.maximum(t - 0.027, 0) * (12 / big)) * (t >= 0.027)
    return nz / np.abs(nz).max() * e + 0.4 * np.sin(2 * np.pi * 210 * t) * np.exp(-t * 30)
def snare(v=1.0):
    n = int(0.16 * SR); t = np.arange(n) / SR; nz = filt(rng.standard_normal(n), lo=1500, hi=9000)
    return (nz / np.abs(nz).max() * np.exp(-t * 30) + 0.5 * np.sin(2 * np.pi * 220 * t) * np.exp(-t * 45)) * v
HH = filt(rng.standard_normal(int(0.5 * SR)), lo=7500); HH /= np.abs(HH).max()
def hat(open_=False):
    n = int((0.22 if open_ else 0.045) * SR); return HH[:n] * np.exp(-np.arange(n) / SR * (14 if open_ else 80))
def crash(length=2.8):
    n = int(length * SR); t = np.arange(n) / SR; c = filt(rng.standard_normal((n, 2)), lo=3500); return c / np.abs(c).max() * np.exp(-t * 1.4)[:, None]
def sub(m, dur):
    n = int(dur * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * hz(m) * t) * env(n, 0.004, 0.04)
def reese(m, dur):
    n = int(dur * SR); s = saw(hz(m) * 0.995, n, 0) + saw(hz(m) * 1.005, n, 0.5)
    s = filt(s, hi=900, order=2) * env(n, 0.004, 0.04)
    return 0.6 * s + 0.8 * sub(m, dur)
def impact():
    n = int(2.4 * SR); t = np.arange(n) / SR
    boom = np.sin(2 * np.pi * np.cumsum(30 + 90 * np.exp(-t * 10)) / SR) * np.exp(-t * 1.8)
    return np.tanh(1.4 * boom)

def euclid(k, n, rot=0):
    """Euclidean rhythm E(k,n): k hits spread as evenly as possible over n steps (Toussaint); Bresenham form gives the same necklaces as Bjorklund"""
    pat = [((i * k) // n) != (((i - 1) * k) // n) if i else True for i in range(n)]
    return pat[-rot:] + pat[:-rot] if rot else pat
E38, E58, E516, E716, E916 = euclid(3, 8), euclid(5, 8), euclid(5, 16, 2), euclid(7, 16, 1), euclid(9, 16)
def rim():
    n = int(0.08 * SR); t = np.arange(n) / SR
    return (np.sin(2 * np.pi * 1650 * t) + 0.6 * np.sin(2 * np.pi * 2450 * t)) * np.exp(-t * 70) + filt(rng.standard_normal(n), lo=2500) * np.exp(-t * 300) * 0.3

# ---------- harmony & hook ----------
CH = {"Am": [57, 60, 64], "F": [53, 57, 60], "C": [55, 60, 64], "G": [55, 59, 62]}
ROOTS = {"Am": 45, "F": 41, "C": 48, "G": 43}
PROG = ["Am", "F", "C", "G"]
# THE RIFF: one bar, the same rhythm every bar, repeated from 1 s to the end (bars 1 and 3 identical)
RHY = [(0, .5), (.5, .5), (1, .75), (1.75, .75), (2.5, .5), (3, .5), (3.5, .5)]
RIFF = {"Am": [76, 76, 79, 76, 74, 72, 74], "F": [76, 76, 79, 76, 74, 72, 69],
        "C": [76, 76, 79, 76, 74, 72, 74], "G": [74, 74, 79, 74, 72, 71, 67]}
def lead_synth(m, dur, vib=True):
    """bright square + saw lead, quick attack, a little vibrato on long notes"""
    n = int(dur * SR); t = np.arange(n) / SR
    f = hz(m) * (1 + (0.006 * np.sin(2 * np.pi * 5.5 * t) * np.clip((t - 0.15) / 0.2, 0, 1) if vib else 0))
    s1 = saw(f * 1.004, n, 0.3); s2 = saw(f * 0.996, n, 0.6)
    sq = 2 * (np.mod(np.cumsum(f) / SR, 1.0) < 0.42) - 1.0
    s = 0.5 * sq + 0.35 * (s1 + s2)
    s = filt(s, hi=6500, order=2)
    e = env(n, 0.004, 0.05) * (0.75 + 0.25 * np.exp(-t * 6))
    out = np.stack([s * e, s * e], 1); return out / 2.2
def chord_at(beat): return PROG[int((beat - A0) // 4) % 4]
def in_gap(b): return DROP - 0.5 <= b < DROP              # silence right before the drop

# ---------- 0–1 s: the hit ----------
add("drums", impact(), 0, gain=0.55)
add("drums", kick(1.3, 0.6), 0, gain=0.9)
add("drums", crash(), 0, gain=0.45)
add("synth", supersaw([45, 57, 60, 64, 69, 72, 76], 0.95, rel=0.5, bright=12000), 0, gain=3.2)
add("lead", supersaw([81, 76], 0.6, rel=0.4, voices=5, bright=12000), 0, gain=1.3)
nr = int(T(A0) * SR) - int(0.45 * SR); tr = np.arange(nr) / SR        # mini riser into the hook
add("fx", filt(rng.standard_normal((nr, 2)), lo=2500) * ((tr / tr[-1]) ** 2)[:, None], 0.45, gain=0.12)

# ---------- chords / pads / plucks (A .. I) ----------
synth_chords = np.zeros((N, 2))
for bar in range(A0, I0, 4):
    c = chord_at(bar); end = min(bar + 4, I0); drop = bar >= DROP
    if not drop:
        tones = CH[c] + [CH[c][0] + 12]
        stab = supersaw(tones, (end - bar) * BEAT + 0.3, att=0.02, rel=0.3)
        i = int(T(bar) * SR); seg = stab[: N - i]; synth_chords[i:i + len(seg)] += seg * (0.55 if bar < F0 else 0.7)
    else:                                         # pumping offbeat stabs at double time
        for k in range(int((end - bar) * 2)):
            b = bar + k / 2 + 0.25
            add("synth", supersaw(CH[c] + [CH[c][0] + 12, CH[c][1] + 12], BEAT * 0.22, att=0.003, rel=0.06), T(b), gain=1.2)
        add("synth", supersaw(CH[c] + [CH[c][2] + 12], (end - bar) * BEAT + 0.2, att=0.01, rel=0.2), T(bar), gain=0.55)
    # THE RIFF: lead synth + pluck before the drop; supersaw octaves at the drop
    for (pos, ln), m in zip(RHY, RIFF[c]):
        b = bar + pos
        if b >= I0 or in_gap(b): continue
        d = ln * BEAT * 0.92
        if drop:
            add("lead", supersaw([m + 12, m], d + 0.05, att=0.003, rel=0.06, voices=7, spread=0.2, bright=12000), T(b), gain=1.35)
            add("lead", lead_synth(m + 12, d), T(b), gain=0.5)
        else:
            lv = 0.5 if bar < C0 else 0.56 if bar < F0 else 0.56 + 0.2 * (b - F0) / 5
            add("lead", lead_synth(m, d), T(b), gain=lv)
            add("lead", pluck(m + 12, 0.4, 1.4), T(b), pan=0.25, gain=0.18 if bar < E0 else 0.28)
            if bar >= E0: add("lead", supersaw([m + 12], d, att=0.005, rel=0.05, voices=5, spread=0.14), T(b), gain=0.4)
    # 16th-note arp (from C), skipped in the gap
    if bar >= C0:
        arp = [CH[c][0] + 12, CH[c][1] + 12, CH[c][2] + 12, CH[c][1] + 12]
        for k in range(int((end - bar) * 4)):
            b = bar + k / 4
            if b < C0 or in_gap(b) or not E916[k % 16]: continue
            add("synth", pluck(arp[k % 4] + (12 if drop else 0), 0.22, 0.8), T(b), pan=0.45 * np.sin(k * 1.3), gain=0.11 if not drop else 0.12)
    # bass: Euclidean — E(3,8) tresillo before the drop, E(5,8) at the drop (8th-note grid)
    if bar >= C0 - 3:
        for k in range(int((end - bar) * 2)):
            b = bar + k / 2
            if b < C0 - 3 or in_gap(b): continue
            if drop:
                if E58[k % 8]: add("bass", reese(ROOTS[c] - 12, BEAT * 0.45), T(b), gain=0.65)
            elif bar >= C0:
                if E38[k % 8]: add("bass", sub(ROOTS[c] - 12, BEAT * (0.7 if k % 8 != 6 else 0.45)), T(b), gain=0.6)
            elif k % 4 == 0: add("bass", sub(ROOTS[c] - 12, BEAT * 1.8), T(b), gain=0.4)

# filter: closed in A–B, opens through C–E, dips at the start of the build, sweeps fully open at the drop
def cutoff(s):
    b = np.interp(s, [T(x) for x in range(TOTAL + 1)], np.arange(TOTAL + 1))
    return np.interp(b, [0, 0.3, A0, C0, E0, F0, F0 + 0.5, DROP - 0.5, DROP, I0, TOTAL],
                        [9000, 2500, 700, 1300, 2600, 5000, 900, 9000, 14000, 14000, 14000])
BUS["synth"] += sweep_lp(synth_chords, cutoff)

# ---------- drums ----------
for beat in range(A0, I0):
    rel = (beat - A0) % 4
    for half in (0, 0.5):
        b = beat + half
        if in_gap(b): continue
        if beat < C0:
            if half == 0: add("drums", kick(0.8), T(b), gain=0.45)
        elif beat < F0:
            if half == 0: add("drums", kick(), T(b), gain=0.8)
            else: add("drums", hat(beat >= E0), T(b), pan=0.25, gain=0.28 if beat >= E0 else 0.3)
            if beat >= E0 and half == 0 and rel in (1, 3): add("drums", clap(), T(b), gain=0.5)
        elif beat < DROP:                            # build: kick quarters, then eighths in the last bar
            if half == 0 or beat >= F0 + 3: add("drums", kick(0.9), T(b), gain=0.55 + 0.25 * (b - F0) / 5)
        else:                                        # drop: double-time four-on-the-floor
            add("drums", kick(1.15), T(b), gain=0.95)
            add("drums", hat(True), T(b + 0.25), pan=0.25, gain=0.3)
            if half == 0.5: add("drums", clap(1.5), T(b), gain=0.62)
for b0, g in ((C0, 0.25), (E0, 0.3), (DROP, 0.55), (DROP + 4, 0.4), (DROP + 8, 0.35)):
    if b0 < I0: add("drums", crash(), T(b0), gain=g)
add("drums", impact(), T(DROP), gain=0.4)
# Euclidean percussion on the 16th grid: rim E(5,16) from C, closed hats E(7,16) from E (both through the drop)
for beat in range(C0, I0):
    for q in range(4):
        b = beat + q / 4; step = int(round((b - A0) * 4)) % 16
        if in_gap(b) or (F0 <= b < DROP): continue
        if E516[step]: add("drums", rim(), T(b), pan=-0.35, gain=0.22 if b < DROP else 0.2)
        if b >= E0 and E716[step]: add("drums", hat(), T(b), pan=0.35, gain=0.16 if b < DROP else 0.18)
# snare roll: eighths -> 16ths -> 32nds, crescendo into the gap
x = F0 + 1; roll = []
for b1, step in ((F0 + 3, 0.5), (F0 + 4, 0.25), (DROP - 0.5, 0.125)):
    while x < b1 - 1e-9: roll.append(x); x += step
for x in roll: add("drums", snare(0.25 + 0.75 * ((x - F0 - 1) / (DROP - 0.5 - F0 - 1)) ** 1.4), T(x), gain=0.6)

# ---------- build FX: noise riser (stops at the gap) ----------
nb = int((T(DROP - 0.5) - T(F0)) * SR); tb = np.arange(nb) / SR; u = tb / tb[-1]
nz = rng.standard_normal((nb, 2)); riser = np.zeros((nb, 2))
for k in range(8):                                   # stepped band-pass sweep 500 Hz -> 8 kHz
    sl = slice(int(k * nb / 8), int((k + 1) * nb / 8)); fc = 500 * 16 ** (k / 7)
    riser[sl] = filt(nz, lo=fc * 0.6, hi=fc * 2.5, order=2)[sl]
add("fx", riser / np.abs(riser).max() * (u ** 2)[:, None], T(F0), gain=0.35)

# ---------- I–J: downlifter, major-key pads, plucks, no drums ----------
nd = int(2.2 * SR); td = np.arange(nd) / SR
dn = filt(rng.standard_normal((nd, 2)), lo=1500) * np.exp(-td * 2.2)[:, None]
add("fx", dn / np.abs(dn).max(), T(I0), gain=0.22)
add("drums", impact(), T(I0), gain=0.35)
I_SEQ = [(I0, "F", 1.5), (I0 + 1.5, "G", 1.5), (I0 + 3, "C", TOTAL - I0 - 3)]
for b0, c, ln in I_SEQ:
    pad = supersaw(CH[c] + [CH[c][0] + 12, ROOTS[c]], ln * BEAT + 2.0, att=0.25, rel=1.5, spread=0.15, bright=3500)
    add("synth", pad, T(b0), gain=0.55)
    add("bass", sub(ROOTS[c] - 12, ln * BEAT + 0.5), T(b0), gain=0.4)
# the riff once more, soft, over the sunrise; last note held
for bar0, notes in ((I0, RIFF["C"]), (J0, [76, 76, 79, 76, 74, 72, 72])):
    for k, ((pos, ln), m) in enumerate(zip(RHY, notes)):
        b = bar0 + pos
        if b >= TOTAL: continue
        last = bar0 == J0 and k == len(RHY) - 1
        add("lead", pluck(m, 2.5 if last else 0.6, 1.1), T(b), gain=0.5)
        add("lead", lead_synth(m, (2.0 if last else ln * BEAT * 0.9)) * env(int((2.0 if last else ln * BEAT * 0.9) * SR), 0.01, 0.6 if last else 0.05)[:, None], T(b), gain=0.28)
for k, m in enumerate((84, 88, 91, 96)): add("lead", pluck(m, 0.9, 1.5), T(I0 + 3.0) + 0.12 * k, pan=0.4 * (k % 2 * 2 - 1), gain=0.22)

# ---------- sidechain pump on synths and bass (follows the kicks) ----------
kick_beats = list(range(C0, F0)) + [b + h for b in range(DROP, I0) for h in (0, 0.5)]
sc = np.ones(N)
for b in kick_beats:
    i = int(T(b) * SR); n = int(0.28 * SR); k = np.arange(min(n, N - i)) / SR
    sc[i:i + len(k)] = np.minimum(sc[i:i + len(k)], 1 - (0.75 if b >= DROP else 0.45) * np.exp(-k / 0.07))
for bus in ("synth", "bass", "lead"):
    BUS[bus] *= (sc if bus != "lead" else 0.6 + 0.4 * sc)[:, None]

# ---------- mix ----------
irn = int(2.2 * SR); it = np.arange(irn) / SR
ir = filt(rng.standard_normal((irn, 2)), lo=300, hi=8000) * np.exp(-it / 0.55)[:, None]; ir /= np.sqrt((ir ** 2).sum(axis=0))
send = BUS["synth"] * 0.35 + BUS["lead"] * 0.45 + BUS["drums"] * 0.06 + BUS["fx"] * 0.3
nf = 1 << (N + irn - 1).bit_length()
wet = np.stack([np.fft.irfft(np.fft.rfft(send[:, c], nf) * np.fft.rfft(ir[:, c], nf), nf)[:N] for c in range(2)], 1)
BUS["bass"] = filt(BUS["bass"], lo=40, order=2)
mix = BUS["synth"] * 0.85 + BUS["lead"] * 1.4 + BUS["drums"] * 0.85 + BUS["bass"] * 0.45 + BUS["fx"] + wet * 0.3
mix = filt(mix, lo=35, order=2); mix += 0.5 * filt(mix, lo=3000, order=2)
# the cut: everything drops out for the half beat before the drop
g0, g1 = int(T(DROP - 0.5) * SR), int(T(DROP) * SR); ramp = int(0.02 * SR)
duck = np.ones(N); duck[g0:g1] = 0.06; duck[g0:g0 + ramp] = np.linspace(1, 0.06, ramp); duck[g1 - ramp // 2:g1] = np.linspace(0.06, 1, ramp // 2)
mix *= duck[:, None]
mix *= np.clip((DUR - tt) / 1.5, 0, 1)[:, None]
rms = np.sqrt(np.mean(mix ** 2)); mix *= 10 ** (-17.3 / 20) / max(rms, 1e-9)
ceil = 10 ** (-1 / 20)
mix = np.where(np.abs(mix) < 0.7 * ceil, mix, np.sign(mix) * (0.7 * ceil + 0.3 * ceil * np.tanh((np.abs(mix) - 0.7 * ceil) / (0.3 * ceil))))
outp = ROOT / "build" / "bgm.wav"; outp.parent.mkdir(exist_ok=True)
with wave.open(str(outp), "wb") as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((np.clip(mix, -1, 1) * 32767).astype("<i2").tobytes())
print(f"bgm -> {outp} ({DUR:.2f}s, peak {20*np.log10(np.abs(mix).max()):.1f} dBFS, drop at {T(DROP):.2f}s)")
