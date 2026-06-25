# build_all.py — turnkey builder for the X-RAY VISION WINDOW.
#   Textport:  exec(open(r'C:\Users\User\finger-bridge\scripts\build_all.py').read())
#   MCP:       executed directly by Claude
# Builds, under /project1 (namespaced fb_*):
#   fb_video (clean cam, upscaled 1080p)  fb_tick (always-cook)  fb_xray_state (brain)
#   fb_xray (GLSL TOP: quad X-ray window)  fb_comp (xray over cam)
#   fb_post_bloom -> fb_post_grade -> fb_out -> fb_window (1920x1080)
# Idempotent + self-cleaning (wipes prior fb_* first, removes TD auto-companion DATs).

import td

ROOT = r'C:\Users\User\finger-bridge'
P = op('/project1')
try:
    PM = ParMode
except NameError:
    PM = type(P.pars()[0].mode)

log = []
def L(m): log.append(m)
def C(typ): return getattr(td, typ)
def node(typ, name, x, y):
    n = P.op(name) or P.create(C(typ), name)
    n.nodeX, n.nodeY = x, y
    return n
def rd(rel): return open(ROOT + '\\' + rel).read()
def connect(src, dst, idx=0): dst.inputConnectors[idx].connect(src)
# NOTE: TouchDesigner Non-Commercial caps texture resolution at 1280x1280, so the 16:9
# ceiling is 1280x720. The chain runs camera-native (1280x720 = the max) and fb_window
# upscales to 1920x1080 for display. A Commercial/Pro license would remove the cap.
RESW, RESH = 1280, 720

# clean slate (never touches the plugin)
for _c in list(P.children):
    if _c.name.startswith('fb_'):
        try: _c.destroy()
        except Exception: pass

# 0. plugin config — 2 hands + gestures ON; every on-video overlay OFF so the camera
# feed is CLEAN (no detection boxes / face mesh / skeleton / labels = no "debug points").
mp = op('/project1/MediaPipe')
if mp:
    cfg = [('Gnumhands', 2), ('Detectgestures', 1), ('Wflip', 1),
           ('Detectfacelandmarks', 0), ('Detectfaces', 0), ('Detectposes', 0),
           ('Detectobjects', 0), ('Detectimages', 0), ('Detectsegments', 0),
           ('Showoverlays', 0), ('Generatehandgui', 0), ('Generatefacelandmarksgui', 0),
           ('Generateposegui', 0), ('Generateobjectsgui', 0), ('Geneartesimplefacegui', 0),
           ('Generateimageclasifygui', 0), ('Generateimageembeddingsgui', 0),
           ('Generateimagesegmentationgui', 0), ('Sshowmulticlassbackgroundonly', 0)]
    for pname, val in cfg:
        try: getattr(mp.par, pname).val = val
        except Exception as e: L('plugin par %s: %r' % (pname, e))
    L('plugin configured: 2 hands, gestures on, all overlays OFF (clean feed)')

# 1. source (upscaled to 1080p so the whole chain is uniform HD) + always-cook tick
fb_video = node('nullTOP', 'fb_video', -1100, 300)
connect(op('/project1/MediaPipe/video'), fb_video)   # camera-native 1280x720 (license max)
fb_tick = node('lfoCHOP', 'fb_tick', -1100, 80)
try: fb_tick.par.frequency = 0.2
except Exception: pass

# 2. brain
code = node('textDAT', 'fb_xray_state_code', -850, 0)
code.text = rd('scripts\\xray_state.py')
brain = node('scriptCHOP', 'fb_xray_state', -650, 0)
brain.par.callbacks = code.path
connect(fb_tick, brain, 0)
try: brain.unstore('*')
except Exception: pass
try: brain.cook(force=True)
except Exception as e: L('brain cook: %r' % e)

# 3. the X-ray window GLSL TOP
pix = node('textDAT', 'fb_xray_pix', -380, 0)
pix.text = rd('shaders\\xray.frag')
xray = node('glslTOP', 'fb_xray', -150, 0)
xray.par.pixeldat = pix.path
try: xray.par.format = 'rgba8fixed'
except Exception: pass
connect(fb_video, xray, 0)                            # inherits 1280x720 from fb_video

def bind_xray(g):
    S = "op('/project1/fb_xray_state')"
    g.par.vec = 6
    def nm(i, name): getattr(g.par, 'vec%dname' % i).val = name
    def ex(i, c, e):
        p = getattr(g.par, 'vec%dvalue%s' % (i, c)); p.mode = PM.EXPRESSION; p.expr = e
    def co(i, c, v):
        p = getattr(g.par, 'vec%dvalue%s' % (i, c)); p.mode = PM.CONSTANT; p.val = v
    nm(0, 'uTL'); ex(0, 'x', S+"['tlx']"); ex(0, 'y', S+"['tly']")
    nm(1, 'uTR'); ex(1, 'x', S+"['trx']"); ex(1, 'y', S+"['try']")
    nm(2, 'uBR'); ex(2, 'x', S+"['brx']"); ex(2, 'y', S+"['bry']")
    nm(3, 'uBL'); ex(3, 'x', S+"['blx']"); ex(3, 'y', S+"['bly']")
    nm(4, 'uState'); ex(4, 'x', S+"['active']"); ex(4, 'y', S+"['alpha']")
    ex(4, 'z', 'absTime.seconds'); co(4, 'w', 1280.0/720.0)
    nm(5, 'uExtra'); ex(5, 'x', S+"['energy']"); co(5, 'y', float(RESW)); co(5, 'z', float(RESH)); co(5, 'w', 0.0)
bind_xray(xray)

# 4. composite: X-ray window on top, camera on the bottom
comp = node('compositeTOP', 'fb_comp', 120, 0)
try: comp.par.operand = 'over'
except Exception as e: L('operand: %r' % e)
connect(xray, comp, 0)
connect(fb_video, comp, 1)

# 5. post: bloom (the glow) -> grade
bloom = node('bloomTOP', 'fb_post_bloom', 340, 0)
connect(comp, bloom, 0)
for pn, pv in [('bloomthreshold', 0.62), ('bloomintensity', 0.55)]:
    try: getattr(bloom.par, pn).val = pv
    except Exception: pass
grade = node('levelTOP', 'fb_post_grade', 540, 0)
connect(bloom, grade, 0)
for pn, pv in [('contrast', 1.08), ('brightness1', 1.02), ('blacklevel', 0.0)]:
    try: getattr(grade.par, pn).val = pv
    except Exception: pass

# 6. output
fb_out = node('nullTOP', 'fb_out', 740, 0)
connect(grade, fb_out)
win = node('windowCOMP', 'fb_window', 940, 0)
try:
    win.par.winop = fb_out.path
    win.par.winw = 1920; win.par.winh = 1080; win.par.borders = False
except Exception as e: L('window cfg: %r' % e)

# 6b. tidy auto-created companion DATs
for c in list(P.children):
    n = c.name
    if n.startswith('fb_') and (n.endswith('_pixel') or n.endswith('_compute')
                                or n.endswith('_info') or n.endswith('_callbacks')):
        try: c.destroy()
        except Exception: pass

# 7. report (GLSL compile errors surface as warnings -> read via Info DAT)
print('=== finger-bridge X-RAY build_all ===')
for m in log: print(' ', m)
def node_issue(o):
    if not o: return 'MISSING'
    if o.errors(): return 'ERR: ' + o.errors()
    w = o.warnings() or ''
    if 'compile error' in w.lower():
        info = P.op('fb_info') or P.create(C('infoDAT'), 'fb_info')
        info.par.op = o.path; info.cook(force=True)
        tail = info.text.split('Pixel Shader Compile Results:')[-1].strip()
        return 'GLSL: ' + tail[:300]
    if w.strip(): return 'WARN: ' + w.strip()[:140]
    return ''
issues = []
for nm in ['fb_xray_state', 'fb_xray', 'fb_comp', 'fb_out']:
    msg = node_issue(op('/project1/' + nm))
    if msg: issues.append('%s: %s' % (nm, msg))
if P.op('fb_info'): P.op('fb_info').destroy()
print('VIEW: /project1/fb_out   (fullscreen: op("/project1/fb_window").par.winopen.pulse())')
print('ISSUES:', ('\n  ' + '\n  '.join(issues)) if issues else '(none - shader compiled clean)')
