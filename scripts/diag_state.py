# diag_state.py — dump the live fb_xray_state: the 4 window corners, active/alpha/
# energy, and the chosen LEFT/RIGHT hand mapping. Confirms exact tracking.
#   exec(open(r'C:\Users\User\finger-bridge\scripts\diag_state.py').read())


def _v(b, ch):
    try: return round(float(b[ch][0]), 3)
    except Exception: return None


def diag():
    b = op('/project1/fb_xray_state')
    if not b:
        print('fb_xray_state not found — run build_all first'); return
    b.cook(force=True)
    print('=== fb_xray_state ===')
    print('left-screen hand = %s   active=%s  alpha=%s  energy=%s'
          % (b.fetch('left_is', '?'), _v(b, 'active'), _v(b, 'alpha'), _v(b, 'energy')))
    print('window corners (UV, y bottom-up):')
    for c, label in [('tl', 'TL=left index '), ('tr', 'TR=right index'),
                     ('br', 'BR=right thumb'), ('bl', 'BL=left thumb ')]:
        print('  %s  (%s, %s)' % (label, _v(b, c + 'x'), _v(b, c + 'y')))
    print('center = (%s, %s)' % (_v(b, 'cx'), _v(b, 'cy')))


diag()
