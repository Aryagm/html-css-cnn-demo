"""Hands-off, JavaScript disabled: one click on Start, no reads/input for WAIT s, then one read.
Weights must equal the float64 reference after P steps, and every completed history sample must equal the reference loss level."""
import os, sys, json, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'cssfull'))
import ref
from playwright.sync_api import sync_playwright
from test_curves import PAGE, READ, trl, lvl, HS, NH
tr, te = ref.split(); eng = sys.argv[1]; WAIT = float(sys.argv[2])
with sync_playwright() as p:
    b = p.chromium.launch(channel='chrome', headless=False) if eng == 'chrome-headed' else getattr(p, eng).launch()
    ctx = b.new_context(java_script_enabled=False, viewport={'width': 1200, 'height': 900}); pg = ctx.new_page()
    pg.goto('file://' + PAGE); pg.wait_for_timeout(500); pg.click('#start')
    pg.wait_for_timeout(WAIT * 1000)
    s = pg.evaluate(READ); P = s['P']; got = [a - ref.Q for a in (s['A'] if P % 2 == 0 else s['B'])]
    q = ref.init(); want = {}
    for k in range(P):
        if k % HS == 0: want[(k // HS) % NH] = lvl(trl(q))
        x, y, _ = tr[k % len(tr)]; q = ref.step(q, x, y)
    bad = [k for k, v in want.items() if s['H'][k] != v]
    R = dict(engine=eng, version=b.version, js_enabled=False, hands_off_seconds=WAIT, steps_committed=P, weights_equal_reference=got == q,
             history_samples_checked=len(want), history_samples_wrong=bad, trl_page=s['trl'], trl_ref=trl(q), ref_train_acc=f'{ref.acc(q, tr)}/24', ref_test_acc=f'{ref.acc(q, te)}/84')
    pr = pg.evaluate("""() => [...document.querySelectorAll('.probeset')].map(s => [...s.querySelectorAll('.fwd')].map(d => +getComputedStyle(d).getPropertyValue('--isO')))""")
    R['css_train_acc'] = f"{sum((v > .5) == (y == 1) for v, (_, y, _) in zip(pr[0], tr))}/24"; R['css_test_acc'] = f"{sum((v > .5) == (y == 1) for v, (_, y, _) in zip(pr[1], te))}/84"
    pg.screenshot(path=f'shot-curves-handsoff-{eng}.png', full_page=True)
    print(json.dumps(R, indent=1)); json.dump(R, open(f'result-curves-handsoff-{eng}.json', 'w'), indent=1); b.close()
