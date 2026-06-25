# tune.py — LIVE calibration of the X-ray window's fingertip->screen mapping.
# Paste once into the Textport, raise both hands (thumb+index framing a rectangle),
# then call the helpers and watch fb_out. The window corners update instantly (no
# rebuild). Tell Claude the winning config from status() and it gets baked in as the
# default in xray_state.py.
#
#   exec(open(r'C:\Users\User\finger-bridge\scripts\tune.py').read())
#
# Mapping:  window_uv = raw_fingertip * (sx, sy) + (ox, oy)
#   flipy()  - reverse vertical (the usual fix if the window moves the wrong way in Y)
#   flipx()  - reverse horizontal (if left/right is mirrored)
#   nudge(dox, doy)   - shift the whole window a touch (fine offset)
#   scale(dsx, dsy)   - grow/shrink the mapping around 0 (fine scale)
#   cal(sx, sy, ox, oy)  - set all four directly
#   reset()  - back to defaults (sx=1, sy=1, ox=0, oy=0)
#   smooth(mincutoff, beta) - tracking feel: lower mincutoff=steadier, higher beta=snappier
#   status() - print the current config (report this to Claude)

B = op('/project1/fb_xray_state')


def _g(k, d): return B.fetch(k, d)
def status():
    print('CAL  sx=%.3f sy=%.3f ox=%.3f oy=%.3f   |  smooth mincutoff=%.2f beta=%.2f'
          % (_g('cal_sx',1.0), _g('cal_sy',1.0), _g('cal_ox',0.0), _g('cal_oy',0.0),
             _g('cal_mincut',1.6), _g('cal_beta',0.9)))
def cal(sx, sy, ox, oy):
    B.store('cal_sx', float(sx)); B.store('cal_sy', float(sy))
    B.store('cal_ox', float(ox)); B.store('cal_oy', float(oy)); status()
def flipy():
    sy = _g('cal_sy', 1.0)
    if sy >= 0: B.store('cal_sy', -1.0); B.store('cal_oy', _g('cal_oy',0.0) + 1.0)
    else:       B.store('cal_sy', 1.0);  B.store('cal_oy', _g('cal_oy',1.0) - 1.0)
    status()
def flipx():
    sx = _g('cal_sx', 1.0)
    if sx >= 0: B.store('cal_sx', -1.0); B.store('cal_ox', _g('cal_ox',0.0) + 1.0)
    else:       B.store('cal_sx', 1.0);  B.store('cal_ox', _g('cal_ox',1.0) - 1.0)
    status()
def nudge(dox=0.0, doy=0.0):
    B.store('cal_ox', _g('cal_ox',0.0) + dox); B.store('cal_oy', _g('cal_oy',0.0) + doy); status()
def scale(dsx=0.0, dsy=0.0):
    B.store('cal_sx', _g('cal_sx',1.0) + dsx); B.store('cal_sy', _g('cal_sy',1.0) + dsy); status()
def reset():
    cal(1.0, 1.0, 0.0, 0.0)
def smooth(mincutoff=1.6, beta=0.9):
    B.store('cal_mincut', float(mincutoff)); B.store('cal_beta', float(beta)); status()


status()
print('helpers: flipy()  flipx()  nudge(dox,doy)  scale(dsx,dsy)  cal(sx,sy,ox,oy)  smooth(mc,beta)  reset()  status()')
