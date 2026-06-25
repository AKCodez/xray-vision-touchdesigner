# selftest.py — automated integration test for the X-RAY VISION WINDOW. Builds fresh,
# drives synthetic hands over a deterministic scene, asserts compile / channels / EXACT
# corner tracking / premultiplied masking / 1080p, then restores live webcam mode.
#   exec(open(r'C:\Users\User\finger-bridge\scripts\selftest.py').read())

import td, math
ROOT = r'C:\Users\User\finger-bridge'
P = op('/project1')
checks = []
def check(name, cond, detail=''):
    checks.append((name, bool(cond), detail))

# 1. fresh build
exec(open(ROOT + r'\scripts\build_all.py').read())

# 2. deterministic scene + synthetic framing hands
bg = P.op('fb_testbg') or P.create(td.noiseTOP, 'fb_testbg')
for pn, pv in [('type','perlin2d'),('period',2.5),('mono',1),('amp',0.4),('offset',0.5),
               ('outputresolution','custom'),('resolutionw',1280),('resolutionh',720)]:
    try: getattr(bg.par, pn).val = pv
    except Exception: pass
op('/project1/fb_video').inputConnectors[0].connect(bg)
exec(open(ROOT + r'\scripts\emulate_hands.py').read())
emu = op('/project1/fb_emu_hands')
for k, v in [('sep',0.7),('hgt',0.5),('spr',1.0),('amp',0.0),('spd',1.0)]: emu.store(k, v)
for _ in range(3):
    emu.cook(force=True); op('/project1/fb_xray_state').cook(force=True)
op('/project1/fb_out').cook(force=True)

b = op('/project1/fb_xray_state'); g = op('/project1/fb_xray')
comp = op('/project1/fb_comp'); vid = op('/project1/fb_video')

# 3. assertions
chans = [c.name for c in b.chans()]
need = ['tlx','tly','trx','try','brx','bry','blx','bly','cx','cy','active','alpha','energy','aspect']
check('brain emits all 14 channels', all(n in chans for n in need), str([n for n in need if n not in chans]))
check('X-ray shader compiles', 'compile error' not in (g.warnings() or '').lower(), (g.warnings() or '')[:60])
check('window active with 4 tips', b['active'][0] > 0.5)
check('output at 1280x720 (license max)', g.width == 1280 and g.height == 720, '%dx%d' % (g.width, g.height))

# EXACT tracking: every brain corner sits on an emulator thumb/index tip (y flipped)
def emt(pfx, fg):  # default calibration is identity (cal_sx=cal_sy=1, offsets 0)
    return (float(emu['%s:%s:x' % (pfx, fg)][0]), float(emu['%s:%s:y' % (pfx, fg)][0]))
tips = [emt('h1','thumb_tip'), emt('h1','index_finger_tip'), emt('h2','thumb_tip'), emt('h2','index_finger_tip')]
corners = [(b['tlx'][0],b['tly'][0]),(b['trx'][0],b['try'][0]),(b['brx'][0],b['bry'][0]),(b['blx'][0],b['bly'][0])]
maxerr = 0.0
for cx, cy in corners:
    d = min(math.hypot(cx-tx, cy-ty) for tx, ty in tips)
    maxerr = max(maxerr, d)
check('corners sit exactly on fingertips (<0.01)', maxerr < 0.01, 'max err=%.4f' % maxerr)
check('quad non-degenerate (TR right of TL)', b['trx'][0] > b['tlx'][0] + 0.1)

# premultiplied masking: X-ray inside, scene shows through outside
cx, cy = b['cx'][0], b['cy'][0]
inP = [round(v,3) for v in comp.sample(u=cx, v=cy)[:3]]
inB = [round(v,3) for v in vid.sample(u=cx, v=cy)[:3]]
check('X-ray renders inside window', inP != inB, 'comp%s vs bg%s' % (inP, inB))
gx, gy = 0.04, 0.04
outP = [round(v,3) for v in comp.sample(u=gx, v=gy)[:3]]
outB = [round(v,3) for v in vid.sample(u=gx, v=gy)[:3]]
check('scene shows through outside (premult)', outP == outB, '%s vs %s' % (outP, outB))
xpx = g.sample(u=cx, v=cy)
check('X-ray pixel non-trivial', 0.02 < (xpx[0]+xpx[1]+xpx[2])/3.0)

# 4. report
npass = sum(1 for _, ok, _ in checks if ok)
print('\n=== X-RAY selftest: %d / %d passed ===' % (npass, len(checks)))
for name, ok, detail in checks:
    print('  [%s] %s%s' % ('PASS' if ok else 'FAIL', name, (' -- ' + detail) if (detail and not ok) else ''))

# 5. restore LIVE webcam mode
op('/project1/fb_video').inputConnectors[0].connect(op('/project1/MediaPipe/video'))
for nn in ['fb_emu_hands', 'fb_emu_code', 'fb_testbg']:
    o = P.op(nn)
    if o: o.destroy()
print('\n%s  (restored live webcam mode)' % ('ALL PASS' if npass == len(checks) else '*** SOME CHECKS FAILED ***'))
