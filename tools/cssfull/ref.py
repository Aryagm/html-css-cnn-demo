"""Float64 reference for the full CSS CNN (8x8 -> conv3x3x2 -> ReLU -> maxpool2 -> FC18x2 -> softmax).
Parameters are integer levels q in [-Q,Q]; value = q*STEP. One SGD step: q' = clip(round_half_up(q - LR*grad/STEP + EPS))."""
import math, random
Q = 16; STEP = 0.125; EPS = 0.000123
LRS = [0.1]*20 + [0.25]*38   # conv (W,c) / FC (V,d) learning rates
NW = 18; NC = 2; NV = 36; ND = 2; NP = NW + NC + NV + ND   # 58
def names():
    n = [f'W{f}{a}{b}' for f in range(2) for a in range(3) for b in range(3)]
    n += [f'c{f}' for f in range(2)]
    n += [f'V{c}{f}{I}{J}' for c in range(2) for f in range(2) for I in range(3) for J in range(3)]
    n += [f'd{c}' for c in range(2)]
    return n
NAMES = names()
def unpack(q):
    v = [x * STEP for x in q]
    W = [[[v[f*9+a*3+b] for b in range(3)] for a in range(3)] for f in range(2)]
    c = v[18:20]
    V = [[v[20 + c_*18 + k] for k in range(18)] for c_ in range(2)]
    d = v[56:58]
    return W, c, V, d
def forward(q, x):
    W, c, V, d = unpack(q)
    h = [[[sum(W[f][a][b]*x[i+a][j+b] for a in range(3) for b in range(3)) + c[f] for j in range(6)] for i in range(6)] for f in range(2)]
    r = [[[max(0, h[f][i][j]) for j in range(6)] for i in range(6)] for f in range(2)]
    P = []; win = []
    for f in range(2):
        for I in range(3):
            for J in range(3):
                cells = [(2*I, 2*J), (2*I, 2*J+1), (2*I+1, 2*J), (2*I+1, 2*J+1)]
                m = max(r[f][i][j] for i, j in cells)
                w = next(k for k, (i, j) in enumerate(cells) if r[f][i][j] == m)
                P.append(m); win.append(cells[w])
    z = [sum(V[c_][k]*P[k] for k in range(18)) + d[c_] for c_ in range(2)]
    p1 = 1 / (1 + math.exp(z[0] - z[1]))
    return dict(h=h, r=r, P=P, win=win, z=z, p1=p1)
def grads(q, x, y):
    W, c, V, d = unpack(q); F = forward(q, x); h, P, win = F['h'], F['P'], F['win']
    delta = F['p1'] - y; dz = [-delta, delta]
    gV = [dz[c_]*P[k] for c_ in range(2) for k in range(18)]
    gd = dz[:]
    gW = [0.0]*18; gc = [0.0, 0.0]
    for f in range(2):
        for I in range(3):
            for J in range(3):
                k = f*9 + I*3 + J; i, j = win[k]
                if h[f][i][j] <= 0: continue
                dP = delta * (V[1][k] - V[0][k])
                gc[f] += dP
                for a in range(3):
                    for b in range(3): gW[f*9+a*3+b] += dP * x[i+a][j+b]
    return gW + gc + gV + gd, F
def target(q, g):
    return [max(-Q, min(Q, math.floor(q[i] - LRS[i]*g[i]/STEP + EPS + 0.5))) for i in range(NP)]
def step(q, x, y):
    g, F = grads(q, x, y); return target(q, g)
def init():
    rnd = random.Random(3)
    q = [rnd.choice([-8,-7,7,8]) for _ in range(18)] + [0, 0] + [rnd.choice([-4,4]) for _ in range(36)] + [0, 0]
    return q
# ---- data: 8x8 binary X (y=0) and O (y=1) glyphs at several sizes/positions ----
def glyph(kind, size, oi, oj):
    x = [[0]*8 for _ in range(8)]
    for t in range(size):
        if kind == 'X':
            x[oi+t][oj+t] = 1; x[oi+t][oj+size-1-t] = 1
        else:
            x[oi][oj+t] = x[oi+size-1][oj+t] = x[oi+t][oj] = x[oi+t][oj+size-1] = 1
    if kind == 'O' and size >= 5:   # round the corners
        for (i, j) in [(0,0),(0,size-1),(size-1,0),(size-1,size-1)]: x[oi+i][oj+j] = 0
    return x
def dataset():
    items = []
    for kind in 'XO':
        for size in (4, 5, 6, 7):
            for oi in range(0, 9-size):
                for oj in range(0, 9-size):
                    items.append((glyph(kind, size, oi, oj), 0 if kind == 'X' else 1, f'{kind}{size}@{oi},{oj}'))
    return items
def split():
    items = dataset(); rnd = random.Random(11); rnd.shuffle(items)
    return items[:24], items[24:]
def acc(q, items): return sum((forward(q, x)['p1'] > 0.5) == (y == 1) for x, y, _ in items)
if __name__ == '__main__':
    tr, te = split(); print('train', len(tr), 'test', len(te))
    q = init(); print('init acc train', acc(q, tr), 'test', acc(q, te))
    writes = 0; steps = 0
    for ep in range(10):
        for x, y, n in tr:
            nq = step(q, x, y); writes += sum(a != b for a, b in zip(q, nq)); steps += 1; q = nq
        print('epoch', ep+1, 'train', acc(q, tr), '/', len(tr), 'test', acc(q, te), '/', len(te), 'avg writes/step', round(writes/steps, 1))
