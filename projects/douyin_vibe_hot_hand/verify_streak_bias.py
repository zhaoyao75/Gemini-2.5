"""Independent check of the numbers used in the hot-hand video (Miller & Sanjurjo, Econometrica 2018).

1) Exact enumeration: fair coin, n flips; in each sequence take the proportion of heads among flips that
   immediately follow a head (sequences with no such flip are discarded); average over sequences.
2) Monte Carlo: n=100 flips, p=.5 -- proportion of hits after 3 hits minus after 3 misses (GVT's statistic).
Run:  python3 verify_streak_bias.py
"""
from fractions import Fraction
from itertools import product
import numpy as np

print("== 1) exact: E[proportion of H right after an H] ==")
for n in (3, 4, 5, 6):
    props = []
    for seq in product("HT", repeat=n):
        after = [seq[i + 1] for i in range(n - 1) if seq[i] == "H"]
        if after:
            props.append(Fraction(after.count("H"), len(after)))
    m = sum(props) / len(props)
    print(f"n={n}: {len(props):>2} usable sequences  ->  {m} = {float(m):.4f}")

print("\n== 2) Monte Carlo: n=100, p=.5, streak k=3 (GVT's design target) ==")
rng = np.random.default_rng(2018)
SIMS, N, K = 200_000, 100, 3
x = rng.random((SIMS, N)) < 0.5
def after_streak(x, val):
    # indicator: the K flips before position j are all `val`
    ok = np.ones((x.shape[0], N - K), dtype=bool)
    for d in range(K):
        ok &= (x[:, d:N - K + d] == val)
    nxt = x[:, K:]
    cnt = ok.sum(axis=1)
    hits = (ok & nxt).sum(axis=1)
    return hits, cnt
h1, c1 = after_streak(x, True)    # after 3 hits
h0, c0 = after_streak(x, False)   # after 3 misses
valid = (c1 > 0) & (c0 > 0)
p_h = h1[valid] / c1[valid]; p_m = h0[valid] / c0[valid]
print(f"usable sequences: {valid.mean():.3f} of all")
print(f"mean P(hit | 3 hits)   = {p_h.mean():.4f}")
print(f"mean P(hit | 3 misses) = {p_m.mean():.4f}")
print(f"mean difference        = {(p_h - p_m).mean()*100:+.1f} percentage points  (paper: about -8 pp)")
