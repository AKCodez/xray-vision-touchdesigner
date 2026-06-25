# bind_uniforms.py — (re)bind the fb_xray GLSL TOP uniforms to fb_xray_state.
# Use if the expression bindings ever drop, or after a uniform-name change.
#   exec(open(r'C:\Users\User\finger-bridge\scripts\bind_uniforms.py').read())

S = "op('/project1/fb_xray_state')"


def bind_xray():
    g = op('/project1/fb_xray')
    if not g:
        print('no fb_xray (run build_all first)'); return
    try: PM = ParMode
    except NameError: PM = type(g.par.vec0valuex.mode)
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
    nm(5, 'uExtra'); ex(5, 'x', S+"['energy']"); co(5, 'y', 1280.0); co(5, 'z', 720.0); co(5, 'w', 0.0)
    print('bound fb_xray uniforms -> fb_xray_state')


bind_xray()
