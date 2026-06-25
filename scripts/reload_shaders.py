# reload_shaders.py — hot-reload shaders/xray.frag into fb_xray and report compile
# status (GLSL errors surface as warnings -> read via an Info DAT). Inner iteration
# loop while refining the look (no full rebuild).
#   exec(open(r'C:\Users\User\finger-bridge\scripts\reload_shaders.py').read())

import td
ROOT = r'C:\Users\User\finger-bridge'
P = op('/project1')


def compile_status(g):
    w = g.warnings() or ''
    if 'compile error' not in w.lower():
        return 'OK'
    info = P.op('fb_reload_info') or P.create(td.infoDAT, 'fb_reload_info')
    info.par.op = g.path; info.cook(force=True)
    return 'COMPILE ERROR: ' + info.text.split('Pixel Shader Compile Results:')[-1].strip()[:260]


def reload_all():
    pix, g = P.op('fb_xray_pix'), P.op('fb_xray')
    if not (pix and g):
        print('fb_xray not found — run build_all first'); return
    pix.text = open(ROOT + r'\shaders\xray.frag').read()
    g.cook(force=True)
    print('xray.frag:', compile_status(g))
    if P.op('fb_reload_info'): P.op('fb_reload_info').destroy()


reload_all()
