"""Standalone music for 《Anthropic IPO：最新进展与展望》 — an ORIGINAL piece (no existing score's notes are used).
  key / chords   E minor, 4/4 at 132 BPM (one video beat = two music quarters):  Em | C | G | D  (two bars each; the cycle restarts on Em exactly at video beat 44)
  melody         a "3+3+2" tresillo phrase of long notes (1.5 + 1.5 + 1 video beats), arching UP then falling back:  B4-E5-D5 | C5-B4-G4-A4 | B4-D5-E5 | F#5-E5-D5-A4
                 (different from the midterms theme: no big leap + steps down, no cello, no 6/8 gallop)
  sound          felt-like e-piano arpeggios in 8ths, warm synth lead, string pad, sub bass, four-on-the-floor-ish drums with a tresillo kick; a bell on the climax
  structure      起 solo piano + pad | 承 arp, bass, kick, hats, lead enter | 转 melody climbs, 16th arps, snare roll, riser | break 2 beats | 合 beat 44 full band (the bell strike)
                 | cut at 57 and one huge boom at 58.3 (the weight lands on the scale) | quiet tension | solo piano ending on Em
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

# ---------- timeline in video beats ----------
A0 = SC["A_path"][0]; DROP = SC["E_bell"][0]; BREAK0 = DROP - 2; BUILD0 = 34; CUT = 57.0; BOOM = 58.3; OUT0 = SC["J_end"][0]
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


def synth_lead(m, dur, vel=1.0, cut=2400, att=0.03):
    n = int(dur * SR); t = np.arange(n) / SR
    f = hz(m) * (1 + 0.006 * np.sin(2 * np.pi * 5.2 * t) * np.clip((t - 0.25) / 0.4, 0, 1))
    s = sum(2 * np.mod(np.cumsum(f * 2 ** (d / 12)) / SR, 1) - 1 for d in (-0.1, 0.0, 0.1)) / 3 + 0.5 * np.sin(2 * np.pi * np.cumsum(f) / SR)
    return filt(s, hi=cut, order=2) * env(n, att, 0.3) * vel
def tom(f0=92, dur=0.5, vel=1.0):
    n = int(dur * SR); t = np.arange(n) / SR
    return np.sin(2 * np.pi * np.cumsum(f0 * (1 + 0.55 * np.exp(-t * 16))) / SR) * np.exp(-t * 6.0) * env(n, 0.002, 0.08) * vel
def snare():
    n = int(0.25 * SR); t = np.arange(n) / SR
    return (filt(rng.standard_normal(n), lo=1200, hi=7000) * np.exp(-t * 22) + 0.5 * np.sin(2 * np.pi * 190 * t) * np.exp(-t * 30)) * env(n, 0.001, 0.05)

CYC = ["Em", "C", "G", "D"]
PRE = ["Em", "C", "G", "D", "Em", "C", "G", "D", "C", "D"]          # beats 4..44, resolves to Em on the drop
def chord_at(b):
    return PRE[int((b - A0) // 4)] if b < DROP else CYC[int((b - DROP) // 4) % 4]
ARP = {"Em": [52, 59, 64, 67, 71, 67, 64, 59], "C": [48, 55, 60, 64, 67, 64, 60, 55], "G": [55, 59, 62, 67, 71, 67, 62, 59], "D": [50, 57, 62, 66, 69, 66, 62, 57]}
SUB = {"Em": 40, "C": 36, "G": 43, "D": 38}
PAD = {"Em": [52, 59, 64, 67], "C": [48, 55, 60, 64], "G": [43, 55, 59, 62], "D": [50, 57, 62, 66]}
PHR = {"Em": [(0, 71, 1.5), (1.5, 76, 1.5), (3, 74, 1.0)], "C": [(0, 72, 1.5), (1.5, 71, 1.0), (2.5, 67, 0.5), (3, 69, 1.0)],
       "G": [(0, 71, 1.5), (1.5, 74, 1.5), (3, 76, 1.0)], "D": [(0, 78, 1.5), (1.5, 76, 1.0), (2.5, 74, 0.5), (3, 69, 1.0)]}
PHR_UP = {"Em": [(0, 71, 1.5), (1.5, 74, 1.5), (3, 78, 1.0)], "C": [(0, 72, 1.5), (1.5, 76, 1.5), (3, 79, 1.0)],
          "G": [(0, 71, 1.0), (1.0, 74, 1.0), (2, 79, 2.0)], "D": [(0, 78, 1.5), (1.5, 81, 2.5)]}
def level(b, pts):
    xs, ys = zip(*pts); return float(np.interp(b, xs, ys))
LV = [(0, 0.7), (12, 0.8), (22, 0.95), (34, 1.05), (42, 1.2), (44, 1.35), (56.8, 1.3), (57.2, 0.55), (58.3, 0.8), (62, 0.6), (66, 0.5)]
G_ARP = [(0, 0.5), (12, 0.7), (20, 1.0), (56.8, 1.0), (57.2, 0.0), (58.4, 0.0), (58.6, 0.35), (61.8, 0.35), (62, 0.0)]
G_KICK = [(0, 0.0), (11.8, 0.0), (12.2, 0.5), (24, 1.0), (56.8, 1.0), (57.2, 0.0)]
G_LEAD = [(0, 0.0), (19.8, 0.0), (20.2, 0.6), (30, 0.9), (56.8, 1.0), (57.2, 0.0)]
big = lambda b: DROP <= b < CUT

# ---------- 0–1 s: the same level as later: a soft pad, a piano arpeggio, one low note ----------
add("pad", strings(PAD["Em"], 1.8, cut=1800, att=0.05, rel=0.6), 0, gain=0.4)
for i in range(8): add("arp", epiano(ARP["Em"][i], 0.5, 0.7 + 0.05 * (i % 2)), i * 0.125, pan=-0.1, gain=0.18)
add("bass", sub808(40, 1.0), 0, gain=0.3)
add("lead", epiano(71, 0.9, 1.0), 0.0, gain=1.1); add("lead", epiano(76, 0.9, 1.0), 0.5, gain=1.1)

# ---------- bar by bar ----------
bar = A0
while bar < CUT + 2:
    chord = chord_at(bar); end = min(bar + 4, CUT); lv = level(bar, LV); rising = 32 <= bar < DROP
    if bar < CUT:
        add("pad", strings(PAD[chord], (end - bar) * VBEAT + 0.5, cut=1500 if bar < DROP else 2600, att=0.4), T(bar), gain=0.55 * lv)
        for off, m, ln in (PHR_UP if rising else PHR)[chord]:
            b = bar + off
            if BREAK0 <= b < DROP or b >= CUT: continue
            d = ln * VBEAT + 0.3; lb = level(b, LV); gl = level(b, G_LEAD)
            add("lead", epiano(m, d + 0.5, 1.0), T(b), pan=-0.05, gain=(1.8 if b < 20 else 1.1) * lb)           # the piano carries the tune alone first
            if gl > 0.02:
                add("lead", synth_lead(m, d, 1.0), T(b), pan=0.05, gain=1.4 * lb * gl)
                if big(b) or rising: add("lead", synth_lead(m + 12, d, 0.8, cut=3400), T(b), pan=0.25, gain=0.8 * lb * gl)
            if big(b): add("keys", bell(m + 12, 1.3, 0.6), T(b), pan=0.25, gain=0.3)
        for h in ([0, 1.5, 3] if big(bar) else [0, 2]):
            b = bar + h
            if b < end and not (BREAK0 <= b < DROP): add("bass", sub808(SUB[chord], 0.9 if big(bar) else 1.3), T(b), gain=(0.4 + 0.3 * lv) * (0.5 if b < 12 else 1.0))
    bar += 4
# the drone through the break
add("bass", sub808(SUB["D"], 2 * VBEAT + 0.3), T(BREAK0), gain=0.4)

# ---------- arps, drums ----------
k = 0
while True:
    b = A0 + k * 0.25; k += 1                                    # 8th notes (0.25 video beat)
    if b >= 62: break
    iu = (k - 1) % 8; chord = chord_at(b); lv = level(b, LV); ga = level(b, G_ARP); gk = level(b, G_KICK)
    brk = BREAK0 <= b < DROP
    if CUT <= b < 58.4: continue
    if not brk and ga > 0.03:
        add("arp", epiano(ARP[chord][iu], 0.35, 0.8 if iu % 4 == 0 else 0.55), T(b), pan=-0.15 + 0.3 * (iu % 2), gain=0.5 * lv * ga)
        if b >= BUILD0 or big(b): add("arp", pluck_saw(ARP[chord][iu] + 12, 0.14, 0.5, cut=3000), T(b + 0.125), pan=0.2, gain=0.15 * lv * ga)   # 16th shimmer
    if brk or gk < 0.03: continue
    q = (b - (A0 if b < DROP else DROP)) % 4                      # position inside the 4-beat block, in video beats
    if big(b):
        if q in (0.0, 1.5, 3.0): add("drums", kick(), T(b), gain=0.9 * gk)                                   # tresillo kick
        if abs(q - 1.0) < 1e-6 or abs(q - 3.0) < 1e-6: add("drums", clap(), T(b), gain=0.42 * gk)
        add("drums", hat(abs(q % 1 - 0.5) < 1e-6 and iu % 4 == 2), T(b), pan=0.3, gain=0.12 * gk)
    else:
        if abs(q % 2) < 1e-6: add("drums", kick(), T(b), gain=0.55 * gk)                                     # every other beat while building
        if b >= 24 and abs(q % 2 - 1) < 1e-6: add("drums", snare(), T(b), gain=0.3 * gk)
        if b >= 20: add("drums", hat(), T(b), pan=0.3, gain=0.08 * gk)
# the turn: a snare roll that speeds up, then the break
x = BUILD0 + 4
while x < BREAK0:
    p = (x - (BUILD0 + 4)) / (BREAK0 - BUILD0 - 4); add("drums", snare(), T(x), gain=0.2 + 0.45 * p); x += 0.5 - 0.3 * p
x = BREAK0
while x < DROP: add("drums", tom(120 + 40 * (x - BREAK0) / 2, 0.25, 0.8), T(x), gain=0.3 + 0.5 * (x - BREAK0) / 2); x += 0.25
for (t0, t1, amp) in ((T(BUILD0), T(DROP), 0.16), (T(BREAK0), T(DROP), 0.28)):
    nb = int((t1 - t0) * SR); u = np.arange(nb) / nb
    nz = filt(rng.standard_normal((nb, 2)), lo=1800) * (u ** 2)[:, None]
    sweep = np.sin(2 * np.pi * np.cumsum(220 + 1500 * u ** 2) / SR) * (u ** 2)
    add("fx", nz / np.abs(nz).max(), t0, gain=amp); add("fx", sweep, t0, gain=amp / 3)
add("drums", crash(), T(DROP), gain=0.6); add("drums", kick(), T(DROP), gain=1.1); add("drums", tom(70, 0.9, 1.0), T(DROP), gain=0.9)
add("bass", sub808(28, 1.4, 1.0), T(DROP), gain=0.55); add("keys", bell(76, 2.2, 1.0), T(DROP), pan=0.2, gain=0.25)
# cut at 57: only the pad and a distant heartbeat; then ONE huge boom as the weight lands
add("drums", crash(), T(CUT), gain=0.25)
add("pad", strings(PAD["D"], (BOOM - CUT) * VBEAT + 0.5, cut=1500, att=0.05), T(CUT), gain=0.5)
for hb in (57.3, 57.7): add("drums", tom(78, 0.5, 0.8), T(hb), gain=0.45)
add("drums", kick(), T(BOOM), gain=1.1); add("drums", tom(62, 1.0, 1.0), T(BOOM), gain=1.0); add("bass", sub808(28, 2.0, 1.0), T(BOOM), gain=0.7); add("drums", crash(), T(BOOM), gain=0.35)
# tension 58.3–62: Em pad, a drone, the piano tune once, low heartbeat
add("pad", strings(PAD["Em"], (OUT0 - BOOM) * VBEAT + 0.5, cut=1700, att=0.3), T(BOOM), gain=0.55)
for off, m, ln in PHR["Em"]: add("lead", epiano(m, ln * VBEAT + 0.8, 1.0), T(59.0 + off), pan=-0.05, gain=1.8)
for hb in (59.5, 60.5, 61.5): add("drums", tom(80, 0.5, 0.7), T(hb), gain=0.4)
# outro: solo piano, the phrase once more, ending on Em
for off, m, ln in PHR_UP["Em"]: add("lead", epiano(m, ln * VBEAT * 1.4 + 1.0, 1.0), T(OUT0 + off), pan=-0.05, gain=1.8)
add("pad", strings([40, 52, 59, 64, 67], (TOTAL - OUT0) * VBEAT + 1.2, cut=2200, att=0.4, rel=1.3), T(OUT0), gain=0.9)
add("bass", sub808(40, 3.5), T(OUT0), gain=0.6)
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
LM = 0.2                                   # melody level: chosen so it sits ~4 dB above everything else in 250–3000 Hz (clear, but the bass keeps its share)
LEAD_PRES = filt(BUS["lead"], lo=1200, hi=4800, order=2)
mix = BUS["pad"] * 0.85 + (BUS["lead"] * 1.5 + LEAD_PRES * 0.7) * LM + BUS["arp"] + BUS["keys"] + BUS["drums"] + BUS["bass"] * 2.2 + BUS["fx"] + wet * 0.3
mix = filt(mix, lo=30, order=2); mix += 0.9 * filt(mix, lo=2500, order=2)
mix *= np.clip((DUR - tt) / 1.5, 0, 1)[:, None]
rms = np.sqrt(np.mean(mix ** 2)); mix *= 10 ** (-16.0 / 20) / max(rms, 1e-9)
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
