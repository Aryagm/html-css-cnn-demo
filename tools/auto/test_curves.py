"""Observe-only harness for the loss readout + loss-history chart of site/index.html.
One click on Start, then only computed-style reads. Checks, at every committed step:
  - weights == ref.step(previous browser weights, image)   (the CNN is unchanged)
  - --trl on the page == float64 mean training loss of the page's current weights
  - --lossx == float64 loss of the current example
  - history slot (n mod NH) == round(L(w_{n*HS}) / HQ) after sample step n*HS commits, and no other slot moved."""
import os, sys, time, json, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cssfull'))
import ref
from playwright.sync_api import sync_playwright
PAGE = os.environ.get('PAGE') or os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'site', 'index.html'))
tr, te = ref.split(); NEX = len(tr); NH, HS, HQ, LVH = 50, 6, 0.04, 65
READ = """() => { const u = getComputedStyle(document.querySelector('.ui')); const g = n => +u.getPropertyValue('--' + n);
  const A = [], B = [], H = [];
  for (let p = 0; p < %d; p++) { A.push(g('rA' + p)); B.push(g('rB' + p)); }
  for (let k = 0; k < %d; k++) H.push(g('rH' + k));
  return {P: g('rP'), A, B, H, trl: g('trl'), lossx: g('lossx'), trlv: g('trlv'), done: g('done'), hleft: g('hleft')}; }""" % (ref.NP, NH)
def l1(q, x, y):
    p = ref.forward(q, x)['p1']; return -math.log(max(1e-300, p if y else 1 - p))
def trl(q): return sum(l1(q, x, y) for x, y, _ in tr) / NEX
def lvl(L): return min(LVH - 1, math.floor(L / HQ + 0.5))
def run(engine, steps, jank=0):
    with sync_playwright() as p:
        b = getattr(p, engine).launch(); pg = b.new_page(viewport={'width': 1200, 'height': 900}); pg.goto('file://' + PAGE)
        pg.wait_for_timeout(600)
        s = pg.evaluate(READ); cur = [a - ref.Q for a in s['A']]
        R = dict(engine=engine, version=b.version, init_exact=cur == ref.init() and s['P'] == 0 and s['H'] == [0] * NH)
        pg.click('#start'); t0 = time.time(); prevP = 0; hist = list(s['H'])
        exact = mism = skipped = trl_bad = lx_bad = slot_ok = slot_bad = other_moved = 0; maxerr = maxerr_lx = 0; samples = []; classes = []; last = time.time()
        while prevP < steps:
            if jank: pg.evaluate(f"(() => {{ const e = performance.now() + {jank}; while (performance.now() < e); }})()")
            s = pg.evaluate(READ)
            if s['P'] == prevP:
                continue_check = abs(s['trl'] - trl(cur))
                maxerr = max(maxerr, continue_check); trl_bad += continue_check > 1e-3
                x, y, _ = tr[prevP % NEX]; e2 = abs(s['lossx'] - l1(cur, x, y)); maxerr_lx = max(maxerr_lx, e2); lx_bad += e2 > 1e-3
            else:
                jump = s['P'] - prevP
                if jump != 1: skipped += jump - 1; print('P jumped by', jump, 'at', prevP, flush=True)
                exp = cur
                for k in range(prevP, s['P']):
                    x, y, _ = tr[k % NEX]
                    if k % HS == 0:        # sample step k: slot (k/HS) mod NH must now hold L(w_k)
                        n = k // HS; want = lvl(trl(exp)); got = s['H'][n % NH]
                        L = trl(exp); edge = abs(L / HQ - math.floor(L / HQ) - 0.5) < 1e-6
                        if got == want or edge: slot_ok += 1
                        else: slot_bad += 1; print('SLOT MISMATCH sample', n, 'got', got, 'want', want, 'L', L, flush=True)
                        samples.append((k, round(L, 4), got)); hist[n % NH] = got
                    exp = ref.step(exp, x, y)
                others = [i for i in range(NH) if s['H'][i] != hist[i]]
                if others: other_moved += 1; print('other slots differ', others, flush=True); hist = list(s['H'])
                new = s['A'] if s['P'] % 2 == 0 else s['B']; got = [a - ref.Q for a in new]
                if got == exp: exact += 1
                else:
                    mism += 1
                    # classify: is it an exact SGD state with one or more steps DROPPED (P overshoot, as in the pre-chart 300 ms WebKit stress)?
                    import itertools
                    ks = list(range(prevP, s['P'])); why = 'corrupt (not on any exact path)'
                    for r in range(1, len(ks)):
                        for keep in itertools.combinations(ks, len(ks) - r):
                            e2 = cur
                            for k in keep: x, y, _ = tr[k % NEX]; e2 = ref.step(e2, x, y)
                            if e2 == got: why = f'dropped step(s) {sorted(set(ks) - set(keep))}: weights still an exact SGD state'; break
                        if why[0] == 'd': break
                    if got == cur: why = 'no update applied (all steps in jump dropped)'
                    ndiff = sum(a != b for a, b in zip(got, exp))
                    print('WEIGHT MISMATCH at', prevP, '->', s['P'], 'jump', jump, 'params differing', ndiff, 'classification:', why, flush=True)
                    classes.append(why)
                cur = got; prevP = s['P']; last = time.time()
                if prevP % NEX == 0: print(engine, 'step', prevP, 'exact', exact, 'mism', mism, 'slots ok', slot_ok, 'bad', slot_bad, 'trl maxerr', f'{maxerr:.2e}', 't', round(time.time() - t0), flush=True)
            if time.time() - last > 60: raise RuntimeError(f'no commit for 60 s at P={prevP}: {s["done"]} hleft {s["hleft"]}')
        R.update(steps=prevP, seconds=round(time.time() - t0, 1), sec_per_step=round((time.time() - t0) / prevP, 2), weights_exact=exact, weight_mismatch=mism, skipped=skipped,
                 trl_reads_off=trl_bad, trl_max_abs_err=maxerr, lossx_reads_off=lx_bad, lossx_max_abs_err=maxerr_lx, history_slots_exact=slot_ok, history_slots_bad=slot_bad,
                 unsampled_slot_changes=other_moved, mismatch_classes=classes, samples=samples, jank_ms=jank)
        pg.screenshot(path=os.path.join(os.path.dirname(os.path.abspath(__file__)), f'shot-curves-{engine}.png'), full_page=True)
        b.close(); return R
if __name__ == '__main__':
    eng = sys.argv[1]; steps = int(sys.argv[2]); jank = int(sys.argv[3]) if len(sys.argv) > 3 else 0
    R = run(eng, steps, jank); print(json.dumps({k: v for k, v in R.items() if k != 'samples'}, indent=1))
    json.dump(R, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), f'result-curves-{eng}-{steps}{"-jank" + str(jank) if jank else ""}.json'), 'w'), indent=1)
