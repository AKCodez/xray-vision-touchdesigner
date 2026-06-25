# preflight.py — validate the MediaPipe plugin data contract BEFORE building.
# Run first, ideally with both hands up in frame.
#   Textport:  exec(open(r'C:\Users\User\finger-bridge\scripts\preflight.py').read())
#   MCP:       executed directly by Claude
# Confirms the exact CHOP addresses exist, that num_hands=2 is feeding h2, and dumps
# live fingertip / handedness values so we know the feed is sane.

H1   = '/project1/hand_tracking2/h1/out1'
H2   = '/project1/hand_tracking2/h2/out1'
HELP = '/project1/hand_tracking2/helpers'
VID  = '/project1/MediaPipe/video'
FINGERS = ['thumb_tip', 'index_finger_tip', 'middle_finger_tip', 'ring_finger_tip', 'pinky_tip']


def _f(o, ch, d=None):
    try: return round(float(o[ch][0]), 4)
    except Exception: return d


def preflight():
    out = ['=== finger-bridge preflight ===']
    ok = True
    for p in (H1, H2, HELP, VID):
        o = op(p)
        if not o:
            out.append('MISSING: ' + p); ok = False
        else:
            dims = ('%dx%d' % (o.width, o.height)) if o.isTOP else ('%d samp x %d ch' % (o.numSamples, o.numChans))
            out.append('OK  %-44s %s' % (p, dims))

    h1, h2, hp = op(H1), op(H2), op(HELP)
    for tag, o in (('h1', h1), ('h2', h2)):
        if not o:
            continue
        miss = [f for f in FINGERS if _f(o, '%s:%s:x' % (tag, f)) is None]
        out.append('%s fingertips: %s' % (tag, 'ALL 5 PRESENT' if not miss else ('MISSING ' + ','.join(miss))))
        if miss: ok = False

    if hp:
        out.append('--- live helpers (raise both hands to see non-zero) ---')
        for ch in ['h1:hand_active', 'h2:hand_active', 'h1:Leftness', 'h1:Rightness',
                   'h2:Leftness', 'h2:Rightness', 'hand_distance',
                   'h1:hand_velocity', 'h2:hand_velocity']:
            out.append('   %-22s = %s' % (ch, _f(hp, ch, 'n/a')))
    if h1:
        out.append('--- live h1 fingertips (x, y) ---')
        for f in FINGERS:
            out.append('   %-18s x=%s y=%s' % (f, _f(h1, 'h1:%s:x' % f), _f(h1, 'h1:%s:y' % f)))

    out.append('RESULT: ' + ('READY to build_all' if ok else 'FIX MISSING ITEMS FIRST'))
    msg = '\n'.join(out)
    print(msg)
    return ok


preflight()
