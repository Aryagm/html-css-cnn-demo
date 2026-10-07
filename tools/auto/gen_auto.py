"""Build-time generator for site/index.html: the CNN of css-cnn-full.html, trained AUTOMATICALLY
with zero JavaScript after one Start activation.

State: every parameter is a *register* = the accumulated elapsed time of two paused/running CSS animations
(an up-counter and a down-counter) on a leaf element; level = (u - d + init) mod 33. Paused animations keep
their elapsed time, so the value persists; running ones move it one level per TAU seconds.

Read-back (the upward channel): each register positions a marker inside its own tiny scroll container
(margin = level * UNIT px). The marker is the subject of a named view-timeline; an animation on the ancestor
.ui (timeline-scope on its parent) is driven by that timeline and so reproduces the level as --r<name>.
All maths (forward, backprop, SGD target) runs on .ui from those readings, exactly as in css-cnn-full.html.

Write-back: .ui computes, per register, --ud = 0 hold / 1 count up / 2 count down (shortest way to the target
on the 33-cycle) and container style queries turn that into animation-play-state on the leaf. The loop closes
through layout + timelines, so each register seeks its target and stops there.

Sequencing: two banks A/B (ping-pong) and a phase register P (up-counter). Bank ph = P mod 2 is current
(held); the other bank seeks the SGD targets computed from the current bank on example e = P mod 24.
When every write-bank register equals its target (--done) and the one-shot commit timer C (restarted on every
phase change and whenever --done drops) reads >= 1, P counts up one level: the step is committed, the banks swap
and the next example is presented."""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cssfull'))
from ref import Q, STEP, EPS, LRS, NP, init, split

LV = 2 * Q + 1                              # 33 levels per parameter
TAU = float(os.environ.get('TAU', '0.4'))   # seconds per register level
TAUP = float(os.environ.get('TAUP', TAU))   # seconds per phase level
UNIT = 6                                    # px per level in the read-back scroller
EPOCHS = 50                                 # the step counter wraps after this many epochs (training continues)
tr, te = split()
NEX = len(tr)
PLV = NEX * EPOCHS                      # phase register levels (wraps after EPOCHS epochs; training continues)
UNITP = 0.25
OUT = os.environ.get('OUT') or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'site', 'index.html')
q0 = init()
iW = lambda f, a, b: f * 9 + a * 3 + b
ic = lambda f: 18 + f
iV = lambda c, k: 20 + c * 18 + k
idd = lambda c: 56 + c
X = lambda i, j: f'var(--x{i}{j})'
qv = lambda p: f'var(--q{p})'
REGS = [f'{b}{p}' for b in 'AB' for p in range(NP)]
# ---- loss history: NH write-once-per-sample registers (a ring buffer). Every HS steps the training-set loss of the
# current weights is written into slot (sample index mod NH); the step is not committed until that write is on target.
NH = int(os.environ.get('NH', '50')); HS = int(os.environ.get('HS', '6'))
LVH = 65; HQ = 0.04                          # history levels: loss 0 .. 2.56 in steps of 0.04
TAUH = float(os.environ.get('TAUH', '0.1')); UNITH = 3
HREGS = [f'H{k}' for k in range(NH)]
ALL = REGS + ['P'] + HREGS

ints, nums, inherit = set(), set(), set()
def I(*n): ints.update(n)
def N(*n): nums.update(n)
def H(*n): inherit.update(n)
css = []

# ---- registers (leaves) ----
I('u', 'd', 'v', 'ud'); H('u', 'd', 'v', 'ud')
css.append(f'@keyframes up {{ from {{ --u: 0 }} to {{ --u: {LV} }} }} @keyframes dn {{ from {{ --d: 0 }} to {{ --d: {LV} }} }}')
css.append(f'@keyframes upP {{ from {{ --u: 0 }} to {{ --u: {PLV} }} }}')
css.append(f'@keyframes upH {{ from {{ --u: 0 }} to {{ --u: {LVH} }} }} @keyframes dnH {{ from {{ --d: 0 }} to {{ --d: {LVH} }} }}')
css.append(f""".reg {{ animation: up {LV * TAU:g}s steps({LV}) infinite, dn {LV * TAU:g}s steps({LV}) infinite; animation-play-state: paused, paused; }}
.reg.gP {{ animation: upP {PLV * TAUP:g}s steps({PLV}) infinite; animation-play-state: paused; }}
.reg.gH {{ animation: upH {LVH * TAUH:g}s steps({LVH}) infinite, dnH {LVH * TAUH:g}s steps({LVH}) infinite; animation-play-state: paused, paused; }}
@container style(--ud: 1) {{ .reg {{ animation-play-state: running, paused; }} .reg.gP {{ animation-play-state: running; }} .reg.gH {{ animation-play-state: running, paused; }} }}
@container style(--ud: 2) {{ .reg {{ animation-play-state: paused, running; }} .reg.gH {{ animation-play-state: paused, running; }} }}
#m-reset:checked ~ .ui .reg {{ animation: none; }}
.sc {{ position: relative; overflow: hidden; width: 5px; height: {LV * UNIT}px; border-radius: 2px; background: var(--line); }}
.sc i {{ display: block; height: {UNIT}px; margin-top: calc(var(--v) * {UNIT}px); background: var(--ink); border-radius: 2px; }}
.gP .sc {{ height: {PLV * UNITP}px; }} .gP .sc i {{ height: {UNITP}px; margin-top: calc(var(--v) * {UNITP}px); }}
.gH .sc {{ height: {LVH * UNITH}px; }} .gH .sc i {{ height: {UNITH}px; margin-top: calc(var(--v) * {UNITH}px); background: var(--neg-c); }}""")
for n in ALL:
    init_lv = 0 if n[0] in 'PH' else q0[int(n[1:])] + Q
    mod = PLV if n == 'P' else LVH if n[0] == 'H' else LV
    v = f'mod(var(--u) + {init_lv}, {mod})' if n == 'P' else f'mod(var(--u) - var(--d) + {init_lv + 2 * mod}, {mod})'
    css.append(f'.w{n} {{ --ud: var(--ud{n}); }} .g{n} {{ --v: {v}; }} .g{n} i {{ view-timeline: --t{n}; }}')

# ---- commit debounce: a one-shot timer leaf C, restarted whenever the phase changes or --done drops.
# It is read back through a view timeline like every register, so the commit condition (done AND C read-back >= 1)
# only uses read-backs that come from one layout. The phase register P may only run once --done has held for TAUC.
TAUC = float(os.environ.get('TAUC', '0.15'))
I('rC', 'udC'); H('udC'); N('mC')
css.append(f'@keyframes c0 {{ from {{ --u: 0 }} to {{ --u: 2 }} }} @keyframes c1 {{ from {{ --u: 0 }} to {{ --u: 2 }} }}')
css.append(f'''.gC {{ --v: var(--u); animation: none; }}
@container style(--ud: 1) {{ .gC {{ animation: c0 {2 * TAUC:g}s steps(2) forwards; }} }}
@container style(--ud: 2) {{ .gC {{ animation: c1 {2 * TAUC:g}s steps(2) forwards; }} }}
.wC {{ --ud: var(--udC); }} .gC .sc {{ height: {3 * UNIT}px; width: 8px; }} .gC .sc i {{ view-timeline: --tC; background: var(--neg-c); }}''')
css.append('@keyframes kC { from { --mC: 2 } to { --mC: 0 } }')
READERS = ALL + ['C']

# ---- read-back: timeline-driven animations on .ui ----
for n in ALL:
    top = (PLV if n == 'P' else LVH if n[0] == 'H' else LV) - 1
    css.append(f'@keyframes k{n} {{ from {{ --m{n}: {top} }} to {{ --m{n}: 0 }} }}')
    N(f'm{n}'); I(f'r{n}')
css.append(f'.scope {{ timeline-scope: {", ".join("--t" + n for n in READERS)}; }}')
css.append(f""".ui {{ animation: {", ".join(f"k{n} linear both" for n in READERS)};
  animation-timeline: {", ".join("--t" + n for n in READERS)};
  animation-range: contain 0% contain 100%; }}""")

# ---- mode ----
I('go'); H('go')
css.append('#m-run:checked ~ .ui { --go: 1; }')

# ---- controller: readings, phase, example, bank select ----
c = ['.ui {', '  --rC: calc(var(--mC));']
for n in ALL:
    c.append(f'  --r{n}: calc(var(--m{n}));')
c.append('  --ph: mod(var(--rP), 2);')
c.append(f'  --step: calc(var(--rP));')
c.append(f'  --ex: mod(var(--rP), {NEX});')
c.append(f'  --epoch: calc((var(--rP) - var(--ex)) / {NEX} + 1);')
I('ph', 'step', 'ex', 'epoch'); H('ph', 'step', 'ex', 'epoch')
for e in range(NEX):
    c.append(f'  --e{e}: calc(1 - min(1, abs(var(--ex) - {e})));')
    I(f'e{e}')
for i in range(8):
    for j in range(8):
        on = [f'var(--e{e})' for e, (x, y, _) in enumerate(tr) if x[i][j]]
        c.append(f'  --x{i}{j}: calc({" + ".join(on) if on else "0"});')
        I(f'x{i}{j}'); H(f'x{i}{j}')
ys = [f'var(--e{e})' for e, (x, y, _) in enumerate(tr) if y]
c.append(f'  --y: calc({" + ".join(ys)});'); I('y'); H('y')
for p in range(NP):
    c.append(f'  --q{p}: calc((var(--rA{p}) * (1 - var(--ph)) + var(--rB{p}) * var(--ph)) - {Q});')
    c.append(f'  --o{p}: calc(var(--rB{p}) * (1 - var(--ph)) + var(--rA{p}) * var(--ph));')
    I(f'q{p}', f'o{p}'); H(f'q{p}')
c.append('}')
css.append('\n'.join(c))

# ---- forward pass (on .ui and on every probe) — identical to css-cnn-full.html ----
fw = ['.fwd {']
for f in range(2):
    for i in range(6):
        for j in range(6):
            terms = ' + '.join(f'{qv(iW(f,a,b))} * {X(i+a,j+b)}' for a in range(3) for b in range(3))
            fw.append(f'  --h{f}{i}{j}: calc(({terms} + {qv(ic(f))}) * {STEP});')
            fw.append(f'  --r{f}{i}{j}: max(0, var(--h{f}{i}{j}));')
            N(f'h{f}{i}{j}', f'r{f}{i}{j}'); H(f'h{f}{i}{j}')
    for I_ in range(3):
        for J in range(3):
            cells = [(2*I_, 2*J), (2*I_, 2*J+1), (2*I_+1, 2*J), (2*I_+1, 2*J+1)]
            fw.append(f'  --P{f}{I_}{J}: max({", ".join(f"var(--r{f}{i}{j})" for i, j in cells)});')
            N(f'P{f}{I_}{J}'); H(f'P{f}{I_}{J}')
PK = [f'P{f}{I_}{J}' for f in range(2) for I_ in range(3) for J in range(3)]
for c_ in range(2):
    terms = ' + '.join(f'{qv(iV(c_,k))} * var(--{PK[k]})' for k in range(18))
    fw.append(f'  --z{c_}: calc(({terms} + {qv(idd(c_))}) * {STEP});')
    N(f'z{c_}')
fw.append('  --p1: calc(1 / (1 + exp(var(--z0) - var(--z1))));')
fw.append('  --pct: calc(var(--p1) * 100);')
fw.append('  --isO: clamp(0, (var(--p1) - 0.5) * 1e9, 1);')
fw.append('  --ok: calc(1 - abs(var(--isO) - var(--y)));')
N('p1', 'isO'); I('pct', 'ok'); H('p1', 'isO', 'pct')
fw.append('}')
css.append('\n'.join(fw))

# ---- backward pass + SGD targets + write control (only on .ui) ----
bw = ['.ui {', '  --delta: calc(var(--p1) - var(--y));']
N('delta')
inv = round(1 / STEP)
for f in range(2):
    for I_ in range(3):
        for J in range(3):
            k = f * 9 + I_ * 3 + J
            cells = [(2*I_, 2*J), (2*I_, 2*J+1), (2*I_+1, 2*J), (2*I_+1, 2*J+1)]
            e = [f'(1 - min(1, {inv} * (var(--P{f}{I_}{J}) - var(--r{f}{i}{j}))))' for i, j in cells]
            bw.append(f'  --s{f}{cells[0][0]}{cells[0][1]}: calc({e[0]});')
            bw.append(f'  --s{f}{cells[1][0]}{cells[1][1]}: calc({e[1]} * (1 - var(--s{f}{cells[0][0]}{cells[0][1]})));')
            prev = ' - '.join(f'var(--s{f}{i}{j})' for i, j in cells[:2])
            bw.append(f'  --s{f}{cells[2][0]}{cells[2][1]}: calc({e[2]} * (1 - {prev}));')
            prev3 = ' - '.join(f'var(--s{f}{i}{j})' for i, j in cells[:3])
            bw.append(f'  --s{f}{cells[3][0]}{cells[3][1]}: calc(1 - {prev3});')
            bw.append(f'  --dP{k}: calc(var(--delta) * ({qv(iV(1,k))} - {qv(iV(0,k))}) * {STEP});')
            N(*[f's{f}{i}{j}' for i, j in cells], f'dP{k}'); H(*[f's{f}{i}{j}' for i, j in cells])
            for i, j in cells:
                bw.append(f'  --dh{f}{i}{j}: calc(var(--dP{k}) * var(--s{f}{i}{j}) * clamp(0, {inv} * var(--h{f}{i}{j}), 1));')
                N(f'dh{f}{i}{j}')
grad = {}
for f in range(2):
    for a in range(3):
        for b in range(3):
            grad[iW(f, a, b)] = ' + '.join(f'var(--dh{f}{i}{j}) * {X(i+a,j+b)}' for i in range(6) for j in range(6))
    grad[ic(f)] = ' + '.join(f'var(--dh{f}{i}{j})' for i in range(6) for j in range(6))
for c_ in range(2):
    sign = '' if c_ else '-1 * '
    for k in range(18):
        grad[iV(c_, k)] = f'{sign}var(--delta) * var(--{PK[k]})'
    grad[idd(c_)] = f'{sign}var(--delta)'
for p in range(NP):
    bw.append(f'  --g{p}: calc({grad[p]});')
    bw.append(f'  --T{p}: clamp({-Q}, calc(var(--q{p}) - {LRS[p] / STEP} * var(--g{p}) + {EPS}), {Q});')
    # distance of the write-bank register to its target on the 33-cycle
    bw.append(f'  --D{p}: mod(calc(var(--T{p}) + {Q} - var(--o{p})), {LV});')
    bw.append(f'  --mv{p}: min(1, abs(var(--T{p}) - var(--q{p})));')
    # 1 = count up (1..16 away), 2 = count down (17..32 away, i.e. 16..1 below)
    dirn = f'min(1, var(--D{p})) * (2 - clamp(0, {LV // 2 + 1} - var(--D{p}), 1))'
    bw.append(f'  --udA{p}: calc(var(--go) * var(--ph) * {dirn});')
    bw.append(f'  --udB{p}: calc(var(--go) * (1 - var(--ph)) * {dirn});')
    N(f'g{p}'); I(f'T{p}', f'D{p}', f'mv{p}', f'udA{p}', f'udB{p}'); H(f'udA{p}', f'udB{p}', f'T{p}')
bw.append(f'  --left: calc({" + ".join(f"min(1, var(--D{p}))" for p in range(NP))});')
bw.append(f'  --moves: calc({" + ".join(f"var(--mv{p})" for p in range(NP))});')
bw.append('  --done: calc(1 - min(1, var(--left) + var(--hleft)));')
bw.append('  --udC: calc(var(--go) * var(--done) * (1 + var(--ph)));')
bw.append('  --udP: calc(var(--go) * var(--done) * min(1, var(--rC)));')
# loss on the current example: -ln p(correct class), written as softplus((z0 - z1) * (2y - 1)) so it never overflows
bw.append('  --lt: calc((var(--z0) - var(--z1)) * (2 * var(--y) - 1));')
bw.append('  --lossx: calc(max(0, var(--lt)) + log(1 + exp(-1 * abs(var(--lt)))));')
bw.append('  --pc: calc(100 * (var(--y) * var(--p1) + (1 - var(--y)) * (1 - var(--p1))));')
N('lt', 'lossx'); I('pc'); H('lossx', 'pc')
I('left', 'moves', 'done', 'udP'); H('left', 'moves', 'done', 'udP')
bw.append('}')
css.append('\n'.join(bw))

# ---- training-set loss of the CURRENT weights (all 24 images, recomputed live on .ui) + the history write ----
hl = ['.ui {']
for k in range(18):
    hl.append(f'  --dV{k}: calc({qv(iV(0,k))} - {qv(iV(1,k))});'); N(f'dV{k}')
hl.append(f'  --dd: calc({qv(idd(0))} - {qv(idd(1))});'); N('dd')
for e, (x, y, _) in enumerate(tr):
    for f in range(2):
        for I_ in range(3):
            for J in range(3):
                k = f * 9 + I_ * 3 + J
                hs = []
                for i, j in [(2*I_, 2*J), (2*I_, 2*J+1), (2*I_+1, 2*J), (2*I_+1, 2*J+1)]:
                    on = [qv(iW(f, a, b)) for a in range(3) for b in range(3) if x[i+a][j+b]]
                    hs.append(f'calc(({" + ".join(on + [qv(ic(f))])}) * {STEP})')
                hl.append(f'  --L{e}p{k}: max(0, {", ".join(hs)});'); N(f'L{e}p{k}')
    sign = '' if y else '-1 * '
    hl.append(f'  --L{e}t: calc({sign}({" + ".join(f"var(--dV{k}) * var(--L{e}p{k})" for k in range(18))} + var(--dd)) * {STEP});')
    hl.append(f'  --L{e}: calc(max(0, var(--L{e}t)) + log(1 + exp(-1 * abs(var(--L{e}t)))));'); N(f'L{e}t', f'L{e}')
hl.append(f'  --trl: calc(({" + ".join(f"var(--L{e})" for e in range(NEX))}) / {NEX});'); N('trl'); H('trl')
hl.append(f'  --trlv: min({LVH - 1}, calc(var(--trl) / {HQ}));'); I('trlv'); H('trlv')
# sample index hn (the sample of step hn*HS goes to slot hn mod NH), write flag hw (this step is a sample step)
hl.append(f'  --hn: calc((var(--rP) - mod(var(--rP), {HS})) / {HS});')
hl.append(f'  --hw: calc(1 - min(1, mod(var(--rP), {HS})));')
hl.append(f'  --hslot: mod(var(--hn), {NH});')
hl.append(f'  --ho: max(0, calc(var(--hn) + 1 - {NH}));')          # oldest sample still in the ring
hl.append(f'  --hs0: calc(var(--ho) * {HS}); --hs1: calc((var(--ho) + {NH - 1}) * {HS});')
I('hn', 'hw', 'hslot', 'ho', 'hs0', 'hs1'); H('hn', 'hw', 'hslot', 'ho', 'hs0', 'hs1')
for k in range(NH):
    hl.append(f'  --hsel{k}: calc(var(--hw) * (1 - min(1, abs(var(--hslot) - {k}))));')
    hl.append(f'  --hD{k}: mod(calc(var(--trlv) - var(--rH{k})), {LVH});')
    hl.append(f'  --udH{k}: calc(var(--go) * var(--hsel{k}) * min(1, var(--hD{k})) * (2 - clamp(0, {LVH // 2 + 1} - var(--hD{k}), 1)));')
    # chart geometry: chronological x position, visibility (slot holds a sample of this run), sample index
    hl.append(f'  --hx{k}: mod(calc({k} - var(--ho)), {NH});')
    hl.append(f'  --hv{k}: clamp(0, calc(var(--hn) - {k} + 1), 1);')
    hl.append(f'  --hy{k}: calc(var(--rH{k}));')
    hl.append(f'  --hi{k}: calc(var(--ho) + var(--hx{k}));')
    I(f'hsel{k}', f'hD{k}', f'udH{k}', f'hx{k}', f'hv{k}', f'hy{k}', f'hi{k}'); H(f'hsel{k}', f'udH{k}', f'hx{k}', f'hv{k}', f'hy{k}', f'hi{k}')
hl.append(f'  --hleft: calc({" + ".join(f"var(--hsel{k}) * min(1, var(--hD{k}))" for k in range(NH))});'); I('hleft'); H('hleft')
# display helpers: decimals for counters (int part + 3 digits), epoch labels, planned update per parameter
def dec(n, src):
    hl.append(f'  --{n}m: calc({src} * 1000); --{n}i: calc((var(--{n}m) - mod(var(--{n}m), 1000)) / 1000); --{n}f: mod(var(--{n}m), 1000);')
    I(f'{n}m', f'{n}i', f'{n}f'); H(f'{n}i', f'{n}f')
dec('trl', 'var(--trl)'); dec('lx', 'var(--lossx)'); dec('dl', 'abs(var(--delta))')
hl.append('  --dneg: clamp(0, -1e9 * var(--delta), 1);'); N('dneg'); H('dneg')
for k in range(NH):
    hl.append(f'  --he{k}: calc(var(--hi{k}) / 4);'); I(f'he{k}'); H(f'he{k}')
for p in range(NP):
    hl.append(f'  --du{p}: calc(var(--T{p}) - var(--q{p}));'); I(f'du{p}'); H(f'du{p}')
hl.append('}')
css.append('\n'.join(hl))

props = '\n'.join(
    [f"@property --{n} {{ syntax: '<integer>'; inherits: {'true' if n in inherit else 'false'}; initial-value: 0; }}" for n in sorted(ints)] +
    [f"@property --{n} {{ syntax: '<number>'; inherits: {'true' if n in inherit else 'false'}; initial-value: 0; }}" for n in sorted(nums)])

# ---- presentation ----
def heat(var, scale):
    return (f'background: color-mix(in oklab, var(--pos-c) calc(clamp(0, {var} / {scale}, 1) * 100%), '
            f'color-mix(in oklab, var(--neg-c) calc(clamp(0, -1 * {var} / {scale}, 1) * 100%), var(--card)));')
pres = [f"""
:root {{ color-scheme: light dark; --ink: #1d2433; --bg: #f6f5f1; --card: #fff; --line: #d9d6cc; --pos-c: #2f6fdd; --neg-c: #d9632b;
  --muted: #6b7080; font: 15px/1.45 ui-sans-serif, system-ui, sans-serif; }}
@media (prefers-color-scheme: dark) {{ :root {{ --ink: #e7e8ee; --bg: #15171c; --card: #1e2128; --line: #343844; --muted: #9aa0ae; }} }}
body {{ margin: 0; background: var(--bg); color: var(--ink); }}
.mode {{ position: absolute; opacity: 0; pointer-events: none; width: 0; height: 0; margin: 0; }}
.ui {{ max-width: 1120px; margin: 0 auto; padding: 22px 18px 60px; }}
h1 {{ font-size: 22px; margin: 0 0 4px; }}
h2 {{ font-size: 12.5px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); margin: 0 0 10px; }}
.sub {{ color: var(--muted); margin: 0 0 18px; max-width: 84ch; }}
.grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 14px; }}
.card {{ background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 14px 16px; }}
.m {{ color: var(--muted); font-size: 13px; }}
.row {{ display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }}
.canvas {{ display: grid; grid-template-columns: repeat(8, 26px); gap: 2px; }}
.canvas i {{ height: 26px; border-radius: 3px; border: 1px solid var(--line); }}
.map {{ display: inline-grid; gap: 1px; }}
.map i {{ width: 14px; height: 14px; border-radius: 2px; box-shadow: inset 0 0 0 1px var(--line); }}
.m6 {{ grid-template-columns: repeat(6, 14px); }} .m3 {{ grid-template-columns: repeat(3, 20px); }}
.m3 i {{ width: 20px; height: 20px; }}
.k3 {{ grid-template-columns: repeat(3, 30px); }} .k3 i {{ width: 30px; height: 30px; font: 600 10px ui-monospace, monospace; display: grid; place-items: center; font-style: normal; }}
.btn {{ padding: 8px 16px; border: 1px solid var(--line); border-radius: 999px; cursor: pointer; background: var(--card); color: var(--ink); font: inherit; font-weight: 600; }}
#m-stop:checked ~ .ui .btn.stop, #m-run:checked ~ .ui .btn.run, #m-reset:checked ~ .ui .btn.reset {{ background: var(--ink); color: var(--bg); }}
.num {{ font: 600 14px ui-monospace, monospace; }}
.cnt::after {{ content: counter(v); }}
.c-pct {{ counter-reset: v var(--pct); }} .c-left {{ counter-reset: v var(--left); }} .c-moves {{ counter-reset: v var(--moves); }}
.c-step {{ counter-reset: v var(--step); }} .c-ex {{ counter-reset: v var(--ex); }}
.c-epoch {{ counter-reset: v var(--epoch); }} .c-ph {{ counter-reset: v var(--ph); }}
.verdict {{ font-size: 20px; font-weight: 700; }}
.verdict b, .tru b {{ display: inline-block; overflow: hidden; vertical-align: bottom; }}
.fwd .verdict .o {{ max-width: calc(var(--isO) * 10em); color: var(--pos-c); }}
.fwd .verdict .x {{ max-width: calc((1 - var(--isO)) * 10em); color: var(--neg-c); }}
.tru .o {{ max-width: calc(var(--y) * 10em); }} .tru .x {{ max-width: calc((1 - var(--y)) * 10em); }}
.pbar {{ height: 10px; border-radius: 5px; background: var(--neg-c); overflow: hidden; }}
.pbar i {{ display: block; height: 100%; width: calc(var(--p1) * 100%); background: var(--pos-c); }}
.st {{ display: block; overflow: hidden; }}
.st.busy {{ max-height: calc(var(--go) * (1 - var(--done)) * 5em); }} .st.done {{ max-height: calc(var(--go) * var(--done) * 5em); }}
.st.off {{ max-height: calc((1 - var(--go)) * 5em); }}
.tape {{ display: flex; gap: 2px; align-items: flex-start; overflow-x: auto; padding-bottom: 4px; }}
.tape .bank {{ display: flex; gap: 1px; padding: 4px; border-radius: 6px; }}
.bank.A {{ background: color-mix(in oklab, var(--pos-c) calc((1 - var(--ph)) * 22%), transparent); }}
.bank.B {{ background: color-mix(in oklab, var(--pos-c) calc(var(--ph) * 22%), transparent); }}
.gP .sc {{ width: 8px; }} .gP .sc i {{ background: var(--pos-c); }}
.probe {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(62px, 1fr)); gap: 6px; }}
.probe > div {{ border: 1px solid var(--line); border-radius: 7px; padding: 4px; display: grid; justify-items: center; gap: 3px; font-size: 11px;
  counter-increment: good var(--ok); border-color: color-mix(in oklab, var(--neg-c) calc((1 - var(--ok)) * 100%), var(--line)); }}
.probe .img {{ display: grid; grid-template-columns: repeat(8, 5px); gap: 1px; }}
.probe .img i {{ height: 5px; border-radius: 1px; }}
.probe .dot {{ width: 100%; height: 5px; border-radius: 3px; background: color-mix(in oklab, var(--pos-c) calc(var(--p1) * 100%), var(--neg-c)); }}
.probeset {{ counter-reset: good; }}
.acc::after {{ content: counter(good); font: 700 15px ui-monospace, monospace; }}
"""]
pres += [f'.px{i}{j} {{ background: color-mix(in oklab, var(--ink) calc(var(--x{i}{j}) * 85%), var(--card)); }}' for i in range(8) for j in range(8)]
pres += [f'.kw{p} {{ {heat(f"var(--q{p})", Q)} counter-reset: v var(--q{p}); }}' for p in range(20)]
pres += ['.kw::after { content: counter(v); }']
pres += [f'.fm{f}{i}{j} {{ {heat(f"var(--h{f}{i}{j})", 3)} outline: 1.5px solid color-mix(in oklab, var(--ink) calc(var(--s{f}{i}{j}) * clamp(0, 8 * var(--h{f}{i}{j}), 1) * 100%), transparent); }}' for f in range(2) for i in range(6) for j in range(6)]
pres += [f'.pl{k} {{ {heat(f"var(--{PK[k]})", 3)} }}' for k in range(18)]
pres += [f'.fc{c_}{k} {{ {heat(f"var(--q{iV(c_,k)})", Q)} }}' for c_ in range(2) for k in range(18)]
css.append('\n'.join(pres))
style = props + '\n' + '\n'.join(css)

# ---- HTML ----
canvas = ''.join(f'<i class="px{i}{j}"></i>' for i in range(8) for j in range(8))
kern = lambda f: '<span class="map k3">' + ''.join(f'<i class="kw kw{iW(f,a,b)}"></i>' for a in range(3) for b in range(3)) + '</span>'
fmap = lambda f: '<span class="map m6">' + ''.join(f'<i class="fm{f}{i}{j}"></i>' for i in range(6) for j in range(6)) + '</span>'
pool = lambda f: '<span class="map m3">' + ''.join(f'<i class="pl{f*9+I_*3+J}"></i>' for I_ in range(3) for J in range(3)) + '</span>'
fcw = lambda c_: '<span class="map" style="grid-template-columns:repeat(9,14px)">' + ''.join(f'<i class="fc{c_}{k}"></i>' for k in range(18)) + '</span>'
reg = lambda n: f'<div class="w{n}"><div class="reg g{n}" title="register {n}"><div class="sc"><i></i></div></div></div>'
tape = (f'<div class="tape"><div class="bank A">{"".join(reg(f"A{p}") for p in range(NP))}</div>'
        f'<div class="bank B">{"".join(reg(f"B{p}") for p in range(NP))}</div></div>')
def probe(x, y):
    st = ';'.join(f'--x{i}{j}:{x[i][j]}' for i in range(8) for j in range(8)) + f';--y:{y}'
    img = ''.join(f'<i style="background:{"var(--ink)" if x[i][j] else "var(--line)"}"></i>' for i in range(8) for j in range(8))
    return f'<div class="fwd" style="{st}"><span class="img">{img}</span><span class="dot"></span></div>'
def probeset(items, title):
    return (f'<div class="probeset"><div class="probe">{"".join(probe(x, y) for x, y, _ in items)}</div>'
            f'<p class="m">{title}: <span class="acc"></span> / {len(items)} correct (red border = wrong)</p></div>')

exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'new_html.py')).read())
with open(OUT, 'w') as fh:
    fh.write(html)
print('wrote', os.path.abspath(OUT), len(html), 'bytes;', len(ints) + len(nums), 'registered properties; TAU', TAU)
