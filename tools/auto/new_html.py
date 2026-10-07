# ---- presentation added for the loss readout, loss-history chart, update map and explanations ----
LMAX = (LVH - 1) * HQ                       # top of the chart's loss axis (2.56)
extra = [f"""
@counter-style pad3 {{ system: extends decimal; pad: 3 "0"; }}
.dec::after {{ content: counter(a) "." counter(b, pad3); }}
.d-trl {{ counter-reset: a var(--trli) b var(--trlf); }} .d-lx {{ counter-reset: a var(--lxi) b var(--lxf); }}
.d-dl {{ counter-reset: a var(--dli) b var(--dlf); }} .c-pc {{ counter-reset: v var(--pc); }}
.c-hs0 {{ counter-reset: v var(--hs0); }} .c-hs1 {{ counter-reset: v var(--hs1); }}
.sgn {{ display: inline-block; overflow: hidden; vertical-align: bottom; max-width: calc(var(--dneg) * 1em); }}
.big {{ font: 700 26px/1.1 ui-monospace, monospace; }}
.lead {{ margin: 0 0 8px; }}
.card p.m {{ margin: 6px 0; }}
.card .m b, .card p b {{ color: var(--ink); }}
.ui > h1 {{ margin-bottom: 20px; }}
.card p.help {{ margin: 0 0 16px; color: var(--muted); font-size: 13px; line-height: 1.6; max-width: 76ch; }}
.card p.help.after {{ margin: 14px 0 0; }}
.card p.help b {{ color: var(--ink); }}
.how-steps {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 16px 28px; margin: 16px 0 22px; padding-left: 24px; }}
.how-steps li {{ padding-left: 4px; color: var(--muted); font-size: 13px; line-height: 1.6; }}
.how-steps li::marker {{ color: var(--pos-c); font-weight: 700; }}
.how-steps b {{ display: block; color: var(--ink); }}
.how-details {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px 28px; border-top: 1px solid var(--line); padding-top: 18px; }}
.how-details h3 {{ margin: 0 0 8px; font-size: 14px; }}
.how-details p.help {{ margin-bottom: 0; }}
@media (max-width: 760px) {{ .how-steps, .how-details {{ grid-template-columns: minmax(0, 1fr); }} }}
.forward-stages {{ display: grid; gap: 16px; }}
.forward-stage .stage-label {{ margin: 0 0 6px; font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); }}
.forward-stage .row {{ margin: 0; }}
.prediction-block {{ display: grid; gap: 8px; margin-top: 18px; }}
.prediction-block .verdict {{ margin: 0; }}
.loop {{ list-style: none; display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 8px; margin: 0 0 14px; padding: 0; }}
.loop li {{ background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 8px 10px; font-size: 12.5px; color: var(--muted); }}
.loop li b {{ display: block; font-size: 13.5px; color: var(--ink); }}
.loop li.w {{ background: color-mix(in oklab, var(--pos-c) calc(var(--go) * (1 - var(--done)) * 20%), var(--card)); }}
.loop li.c {{ background: color-mix(in oklab, var(--pos-c) calc(var(--go) * var(--done) * 20%), var(--card)); }}
.lossgrid {{ display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1.9fr); gap: 22px; align-items: start; }}
@media (max-width: 760px) {{ .lossgrid {{ grid-template-columns: minmax(0, 1fr); }} }}
.readout {{ border-top: 1px solid var(--line); padding-top: 10px; margin-top: 10px; }}
.readout:first-child {{ border-top: 0; padding-top: 0; margin-top: 0; }}
.scale {{ display: grid; grid-template-columns: 1fr 1fr 1fr; font-size: 11.5px; color: var(--muted); margin-top: 6px; }}
.scale span:nth-child(2) {{ text-align: center; }} .scale span:nth-child(3) {{ text-align: right; }}
.scalebar {{ height: 6px; border-radius: 3px; background: linear-gradient(90deg, var(--pos-c), var(--line) 50%, var(--neg-c)); position: relative; margin-top: 4px; }}
.scalebar i {{ position: absolute; top: -4px; width: 3px; height: 14px; border-radius: 2px; background: var(--ink);
  left: calc(min(1, var(--lossx) / 1.386) * 100% - 1.5px); }}
.chart {{ padding: 24px 14px 34px 40px; }}
.plot {{ position: relative; height: 220px; container-type: size; border-left: 1px solid var(--line); border-bottom: 1px solid var(--line); }}
.gl {{ position: absolute; left: 0; right: 0; height: 0; border-top: 1px solid color-mix(in oklab, var(--line) 55%, transparent); }}
.gl span {{ position: absolute; right: calc(100% + 6px); transform: translateY(-50%); font: 11px ui-monospace, monospace; color: var(--muted); }}
.gl.chance {{ border-top: 1.5px dashed color-mix(in oklab, var(--neg-c) 70%, transparent); }}
.gl.chance em {{ position: absolute; right: 2px; bottom: 2px; font: 11px ui-sans-serif, system-ui, sans-serif; color: var(--neg-c); font-style: normal; }}
.ylab {{ position: absolute; left: -38px; top: -24px; font-size: 11px; color: var(--muted); }}
.tk {{ position: absolute; top: 0; bottom: 0; left: calc(var(--cx) / {NH - 1} * 100%); width: 0;
  border-left: 1px solid color-mix(in oklab, var(--line) calc(var(--ct) * 70%), transparent); counter-reset: v var(--ce); }}
.tk::after {{ content: counter(v); position: absolute; top: calc(100% + 4px); transform: translateX(-50%); font: 10.5px ui-monospace, monospace; color: var(--muted); opacity: var(--cl); }}
.hp {{ position: absolute; width: 0; height: 0; left: calc(var(--cx) / {NH - 1} * 100%); bottom: calc(var(--cy) / {LVH - 1} * 100%); }}
.hp s {{ position: absolute; left: 0; top: -1px; height: 2px; border-radius: 1px; background: var(--pos-c); transform-origin: 0 50%;
  --sdx: calc(100cqw / {NH - 1}); --sdy: calc((var(--cpy) - var(--cy)) / {LVH - 1} * 100cqh);
  width: hypot(var(--sdx), var(--sdy)); transform: rotate(atan2(calc(-1 * var(--sdy)), calc(-1 * var(--sdx))));
  opacity: calc(var(--cv) * min(1, var(--cx)) * .6); }}
.hp b {{ position: absolute; left: -3.5px; top: -3.5px; width: 7px; height: 7px; border-radius: 50%; background: var(--pos-c); opacity: var(--cv);
  box-shadow: 0 0 0 calc(var(--cw) * 4px) color-mix(in oklab, var(--neg-c) 55%, transparent); }}
.nowm {{ position: absolute; right: -11px; width: 0; height: 0; border: 5px solid transparent; border-right: 7px solid var(--ink); transform: translateY(50%);
  bottom: calc(min(1, var(--trl) / {LMAX:g}) * 100%); }}
.xcap {{ display: flex; justify-content: space-between; font-size: 11.5px; color: var(--muted); margin: 26px 0 0; gap: 10px; flex-wrap: wrap; }}
.legend {{ font-size: 12px; color: var(--muted); margin: 8px 0 0; }}
.legend i {{ display: inline-block; vertical-align: middle; margin: 0 4px 0 10px; }}
.legend i.dot {{ width: 7px; height: 7px; border-radius: 50%; background: var(--pos-c); }}
.legend i.ring {{ width: 7px; height: 7px; border-radius: 50%; background: var(--pos-c); box-shadow: 0 0 0 3px color-mix(in oklab, var(--neg-c) 55%, transparent); }}
.legend i.tri {{ border: 4px solid transparent; border-right: 6px solid var(--ink); }}
.legend i.dash {{ width: 16px; border-top: 1.5px dashed var(--neg-c); }}
.upd {{ display: flex; gap: 14px; flex-wrap: wrap; align-items: flex-end; }}
.upd .m {{ font-size: 12px; }}
.kd {{ grid-template-columns: repeat(3, 26px); }} .kd i {{ width: 26px; height: 26px; font: 600 10px ui-monospace, monospace; display: grid; place-items: center; font-style: normal; }}
.b2 {{ grid-template-columns: repeat(2, 26px); }} .b2 i {{ width: 26px; height: 26px; font: 600 10px ui-monospace, monospace; display: grid; place-items: center; font-style: normal; }}
.f18 {{ grid-template-columns: repeat(18, 12px); }} .f18 i {{ width: 12px; height: 12px; }}
.dn::after {{ content: counter(v); }}
.bank.H {{ display: flex; gap: 1px; padding: 4px; border-radius: 6px; background: color-mix(in oklab, var(--neg-c) 8%, transparent); }}
.tapecap {{ display: flex; gap: 14px; flex-wrap: wrap; font-size: 12px; color: var(--muted); margin: 8px 0 0; }}
.tapecap b {{ color: var(--ink); }}
code {{ font-size: .92em; }}
"""]
for k in range(NH):
    j = (k - 1) % NH
    extra.append(f'.s{k} {{ --cx: var(--hx{k}); --cy: var(--hy{k}); --cpy: var(--hy{j}); --cv: var(--hv{k}); --cw: var(--hsel{k}); '
                 f'--ce: var(--he{k}); --ct: calc(1 - min(1, mod(var(--hi{k}), 4))); --cl: calc(1 - min(1, mod(var(--hi{k}), 8))); }}')
for p in range(NP):
    extra.append(f'.du{p} {{ {heat(f"var(--du{p})", 2)} counter-reset: v var(--du{p}); }}')

style += '\n' + '\n'.join(extra)

cell = lambda p, cls='': f'<i class="{"dn " if cls else ""}du{p}"></i>'
upd = (f'<div class="upd">'
       f'<div><div class="m">kernel 1</div><span class="map kd">{"".join(cell(iW(0,a,b), " du") for a in range(3) for b in range(3))}</span></div>'
       f'<div><div class="m">kernel 2</div><span class="map kd">{"".join(cell(iW(1,a,b), " du") for a in range(3) for b in range(3))}</span></div>'
       f'<div><div class="m">conv biases</div><span class="map b2">{cell(ic(0), " du")}{cell(ic(1), " du")}</span></div>'
       f'<div><div class="m">FC weights (X row, O row)</div><span class="map f18">{"".join(cell(iV(c_,k)) for c_ in range(2) for k in range(18))}</span></div>'
       f'<div><div class="m">output biases</div><span class="map b2">{cell(idd(0), " du")}{cell(idd(1), " du")}</span></div></div>')
grid_lines = ''.join(f'<div class="gl" style="bottom:{v / LMAX * 100:.3f}%"><span>{v:g}</span></div>' for v in (0.5, 1, 1.5, 2, 2.5))
chart = (f'<div class="chart"><div class="plot"><span class="ylab">loss</span>{grid_lines}'
         f'<div class="gl chance" style="bottom:{0.6931 / LMAX * 100:.3f}%"><em>coin-flip guess (0.69)</em></div>'
         + ''.join(f'<span class="tk s{k}"></span>' for k in range(NH))
         + ''.join(f'<span class="hp s{k}"><s></s><b></b></span>' for k in range(NH))
         + '<span class="nowm"></span></div>'
         f'<div class="xcap"><span>epochs of training (a gridline every 24 steps)</span><span>showing steps <span class="num cnt c-hs0"></span>–<span class="num cnt c-hs1"></span></span></div></div>')
hreg = ('<div class="bank H">' + ''.join(f'<div class="wH{k}"><div class="reg gH gH{k}" title="loss-history register {k}"><div class="sc"><i></i></div></div></div>' for k in range(NH)) + '</div>')


html = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; script-src 'none'">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Training a Neural Network in Pure HTML and CSS</title>
<style>
{style}
</style>
</head>
<body>
<div class="scope">
<input class="mode" type="radio" name="mode" id="m-stop" checked>
<input class="mode" type="radio" name="mode" id="m-run">
<input class="mode" type="radio" name="mode" id="m-reset">
<main class="ui fwd">
<h1>Training a Neural Network in Pure HTML and CSS</h1>
<div class="row" style="margin-bottom:14px">
<label class="btn run" for="m-run" id="start">▶ Start</label>
<label class="btn stop" for="m-stop">❚❚ Pause</label>
<label class="btn reset" for="m-reset">⟲ Reset weights</label>
<span class="m">SGD step <span class="num cnt c-step"></span> · epoch <span class="num cnt c-epoch"></span> · example #<span class="num cnt c-ex"></span> · current bank <span class="num cnt c-ph"></span></span>
</div>
<ol class="loop">
<li><b>1 · Input</b></li>
<li><b>2 · Prediction</b></li>
<li><b>3 · Loss</b></li>
<li><b>4 · Gradients</b></li>
<li class="w"><b>5 · Write weights</b></li>
<li class="c"><b>6 · Commit</b></li>
</ol>
<div class="grid">
<section class="card">
<h2>1 · The input: current training example</h2>
<p class="help">Each image is an 8×8 grid: an inked pixel is 1 and a blank pixel is 0. The page cycles through {NEX} fixed X and O examples. The <b>truth</b> label is the correct answer used to check the network's guess; one full pass through these images is an <b>epoch</b>.</p>
<div class="canvas">{canvas}</div>
<p class="m tru">truth: <b class="o">O</b><b class="x">X</b> · image #<span class="num cnt c-ex"></span> of {NEX}</p>
</section>
<section class="card">
<h2>2 · The guess: forward pass</h2>
<p class="help">Each 3×3 kernel slides over the image, multiplying its nine weights by the pixels underneath and adding a bias. The <b>same weights are reused at every position</b>, producing one 6×6 feature map per kernel. ReLU sets negative results to zero; max pooling keeps the largest value in each 2×2 block, leaving two 3×3 maps.</p>
<div class="forward-stages">
<div class="forward-stage"><div class="stage-label">3×3 kernels</div><div class="row">{kern(0)}{kern(1)}</div></div>
<div class="forward-stage"><div class="stage-label">6×6 feature maps</div><div class="row">{fmap(0)}{fmap(1)}</div></div>
<div class="forward-stage"><div class="stage-label">3×3 pooled maps</div><div class="row">{pool(0)}{pool(1)}</div></div>
<div class="forward-stage"><div class="stage-label">Dense weights</div><div class="row">{fcw(0)}{fcw(1)}</div></div>
</div>
<div class="prediction-block">
<p class="verdict">prediction: <b class="o">O</b><b class="x">X</b> <span class="m">p(O) = <span class="cnt c-pct"></span>%</span></p>
<div class="pbar"><i></i></div>
</div>
<p class="help after">The dense layer combines the 18 pooled values into an X score and an O score. Softmax converts them to probabilities that add up to 100%; <b>p(O)</b> is the probability of O. Blue in the bar means O, orange means X. The map outlines mark the cells selected by max pooling.</p>
</section>
</div>
<section class="card" style="margin-top:14px">
<h2>3 · The score: loss (how wrong was the guess?)</h2>
<p class="help">Cross-entropy is <b>−ln(probability of the correct answer)</b>: a confident correct guess has low loss, while a confident wrong guess has high loss. The first readout scores the current image. The second evaluates all {NEX} training images with the current weights, and the curve stores that average every {HS} updates.</p>
<div class="lossgrid">
<div>
<div class="readout">
<p class="m lead">Probability the network gave to the <b>correct</b> answer for this image: <b class="num cnt c-pc"></b><b class="num">%</b></p>
<p class="m lead">Loss on this image = −ln(that probability)</p>
<div class="big dec d-lx"></div>
<div class="scalebar"><i></i></div>
<div class="scale"><span>0 = sure &amp; right</span><span>0.69 = coin flip</span><span>≥ 1.39 = mostly wrong</span></div>
</div>
<div class="readout">
<p class="m lead">Average loss over <b>all {NEX} training images</b>, with the weights as they are right now:</p>
<div class="big dec d-trl" style="color:var(--pos-c)"></div>
</div>
</div>
<div>
<p class="m lead"><b>Training loss over time</b>, sampled every {HS} SGD steps</p>
{chart}
<p class="legend"><i class="dot"></i>stored sample <i class="ring"></i>being written now <i class="tri"></i>current value <i class="dash"></i>score of a 50/50 guess</p>
<p class="help after">The curve keeps the latest {NH} samples; its dots are rounded to {HQ} and capped at {LMAX:g}. The numerical readout shows the live loss to three decimals. Individual updates can make loss rise temporarily, so watch the trend over several epochs.</p>
</div>
</div>
</section>
<div class="grid" style="margin-top:14px">
<section class="card">
<h2>4 · The blame: backprop + SGD update</h2>
<p class="help"><b>Backpropagation</b> works backward through the network to calculate a gradient for each of its {NP} trainable parameters: how a small change would affect loss. <b>SGD</b> updates each value using old value − learning rate × gradient, then rounds to increments of {STEP}. Blue cells below indicate an increase; orange cells indicate a decrease.</p>
<p class="m">Output error = p(O) − truth = <b class="num"><span class="sgn">−</span><span class="dec d-dl"></span></b></p>
<p class="m">Weight change, units of {STEP} (blue = up, orange = down)</p>
{upd}
<p class="m">This step changes <b class="num cnt c-moves"></b> of {NP} weights.</p>
</section>
<section class="card">
<h2>5 · Automatic step advance: the clock</h2>
<p class="help">Press <b>Start</b> once. CSS calculates the next weights and writes them into the spare bank. When every weight—and any scheduled loss sample—has reached its target, a commit timer waits {TAUC:g} seconds, then advances the step counter. That switches banks and selects the next image. <b>Pause</b> freezes progress; <b>Reset</b> restores the starting state.</p>
<p class="m" style="margin-top:10px">
<span class="st busy"><b style="color:var(--neg-c)">Writing:</b> <span class="num cnt c-left"></span> weight registers are still moving towards their targets.</span>
<span class="st done"><b style="color:var(--pos-c)">Step written:</b> committing and loading the next example.</span>
<span class="st off"><b>Paused.</b> Press Start; no further input is needed.</span></p>
</section>
</div>
<section class="card" style="margin-top:14px">
<h2>6 · Weight memory: where the numbers live</h2>
<p class="help">Each parameter is stored in the elapsed time of paused CSS animations. To change it, an animation runs toward its target and pauses again. A marker moves with that stored value; a <b>view timeline</b> reads its position back into the calculations. Bank A holds the current weights while B is written, then they swap roles, so an update reads a consistent set of weights.</p>
<div class="row" style="align-items:flex-start">{tape}{reg('P')}<div class="wC"><div class="gC" title="commit timer"><div class="sc"><i></i></div></div></div>{hreg}</div>
<p class="tapecap"><span><b>Banks A and B</b> ({NP} weights each). The highlighted bank holds the current weights and stays still; the other is being written.</span>
<span><b>Blue:</b> step counter.</span> <span><b>Red:</b> commit timer.</span> <span><b>Orange tint:</b> the {NH} loss-history registers behind the chart (65 levels of {HQ}).</span></p>
</section>
<section class="card" style="margin-top:14px">
<h2>How good is it? Live accuracy from the current weights</h2>
<p class="help">Every thumbnail makes its own live prediction using the current weights. <b>Training accuracy</b> measures the examples used for learning. The <b>held-out test set</b> contains glyphs never used for weight updates and checks whether learning carries over to other shapes. A red border marks a wrong answer; the bar below each image shows p(O).</p>
{probeset(tr, 'training set')}
{probeset(te, 'held-out test set')}
</section>
<section class="card" style="margin-top:14px">
<h2>How it works: one complete training step</h2>
<p class="help">The browser repeats this sequence using HTML and CSS. The images are fixed, but the predictions, gradients, stored weights, and loss samples are computed as the experiment runs.</p>
<ol class="how-steps">
<li><b>Read an image.</b>The step counter selects an 8×8 glyph and its X or O label from the training set.</li>
<li><b>Make a prediction.</b>The shared convolution filters, ReLU, pooling, and dense layer turn the pixels into two probabilities.</li>
<li><b>Measure the error.</b>The correct label tells the loss formula how much probability the network should have assigned to that answer.</li>
<li><b>Calculate a change.</b>Backpropagation follows the chain rule through the layers. For each shared kernel weight, it adds contributions from every position where that weight was used. SGD uses these gradients to choose the next parameter values.</li>
<li><b>Store the next state.</b>The spare animation bank moves to those values. Every {HS} steps, a history register also stores the current average training loss for the curve.</li>
<li><b>Commit and repeat.</b>Once the writes finish, the CSS clock advances. The new bank becomes current, the next image is selected, and the calculation starts again.</li>
</ol>
<div class="how-details">
<div><h3>What HTML and CSS each do</h3><p class="help">HTML provides the elements, controls, and fixed data. CSS custom properties carry numbers; arithmetic functions compute the forward pass, loss, and gradients. CSS conditions control when animations run. Animation time supplies persistent state, and view timelines feed that state back into the next calculation. Together these pieces form the automatic training loop.</p></div>
<div><h3>Why this is a real trainable CNN</h3><p class="help">The two kernels reuse their weights across the image, and backpropagation updates those kernel weights along with the dense layer. The weights start from initial values and change during training. The output is computed from the current weights, and the loss curve reads stored samples from the run.</p></div>
</div>
</section>
</main>
</div>
</body>
</html>
"""
