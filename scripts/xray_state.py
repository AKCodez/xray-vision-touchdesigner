# xray_state.py — the "brain" for the X-ray vision window (callbacks DAT for the
# fb_xray_state Script CHOP). build_all.py loads this into a Text DAT.
#
# Reads the THUMB + INDEX fingertips of BOTH hands and emits the 4 corners of a
# quad "window" (the thumb+index of each hand bound the left/right edges):
#     TL = left index   TR = right index
#     BL = left thumb    BR = right thumb
# Each corner coordinate is smoothed with a One-Euro filter (adaptive: locks when
# still, snaps when moving) for EXACT, low-latency tracking. Mirror-proof L/R by
# x-position. Reuses the proven scaffolding from the rave build: emulator hook,
# frame-gate (bypassed in emulator/test mode), hold-on-blink, alpha fade, safe reads.

import math

H1   = '/project1/hand_tracking2/h1/out1'
H2   = '/project1/hand_tracking2/h2/out1'
HELP = '/project1/hand_tracking2/helpers'

# One-Euro filter params (Hz). Lower mincutoff = smoother when still; higher beta =
# snappier when moving. Tuned for locked-on fingertips with minimal lag.
MINCUTOFF = 1.6
BETA      = 0.9
DCUTOFF   = 1.0
MAX_DT    = 0.05
HOLD_FRAMES = 6        # keep the window active briefly after a blink
ACTIVE_FADE = 9.0      # per-second alpha fade-in/out
ENERGY_SMOOTH = 0.15
ASPECT    = 1280.0 / 720.0

# corners: (name, side, finger, default_uv)  — side resolved to h1/h2 by x-position
CORNERS = [
    ('tl', 'L', 'index_finger_tip', (0.35, 0.65)),
    ('tr', 'R', 'index_finger_tip', (0.65, 0.65)),
    ('br', 'R', 'thumb_tip',        (0.65, 0.35)),
    ('bl', 'L', 'thumb_tip',        (0.35, 0.35)),
]


def _f(chop, name, default=0.0):
    try:
        return float(chop[name][0])
    except Exception:
        return default


def _tip(chop, prefix, finger):
    """(x, y, seen) for one fingertip — RAW MediaPipe coords (calibration applied later)."""
    if chop is None:
        return 0.0, 0.5, False
    x = _f(chop, '%s:%s:x' % (prefix, finger), -1.0)
    y = _f(chop, '%s:%s:y' % (prefix, finger), -1.0)
    seen = (0.0 <= x <= 1.0) and (0.0 <= y <= 1.0)
    return x, y, seen


def _hand_x(chop, prefix):
    """mean x of the thumb+index tips (the corners we use) — for L/R arbitration.
    Works for both the plugin (h?/out1) and the emulator; no pinch_midpoint needed."""
    xs = []
    for fg in ('thumb_tip', 'index_finger_tip'):
        v = _f(chop, '%s:%s:x' % (prefix, fg), -1.0)
        if 0.0 <= v <= 1.0:
            xs.append(v)
    return (sum(xs) / len(xs)) if xs else -1.0


def _alpha(dt, cutoff):
    tau = 1.0 / (2.0 * math.pi * cutoff)
    return 1.0 / (1.0 + tau / dt)


def _one_euro(so, key, x, dt, mincut, beta):
    """One-Euro filter for a single scalar; per-key state in scriptOp storage."""
    xp = so.fetch(key + '_x', None)
    if xp is None:
        so.store(key + '_x', x); so.store(key + '_dx', 0.0)
        return x
    dxp = so.fetch(key + '_dx', 0.0)
    dx = (x - xp) / dt
    edx = dxp + _alpha(dt, DCUTOFF) * (dx - dxp)
    cutoff = mincut + beta * abs(edx)
    ex = xp + _alpha(dt, cutoff) * (x - xp)
    so.store(key + '_x', ex); so.store(key + '_dx', edx)
    return ex


def onCook(scriptOp):
    so = scriptOp
    if so.isTimeSlice:
        so.isTimeSlice = False
    so.clear()
    so.numSamples = 1

    # TEST HOOK: synthetic hands from the emulator if present (scripts/emulate_hands.py)
    emu = op('/project1/fb_emu_hands')
    if emu is not None:
        h1 = h2 = hp = emu
    else:
        h1, h2, hp = op(H1), op(H2), op(HELP)

    # live calibration of fingertip -> window-UV (tune via scripts/tune.py, no rebuild):
    #   uv = raw * (SX,SY) + (OX,OY).  Default un-flips Y (SY=+1) vs MediaPipe top-down.
    SX = so.fetch('cal_sx', 1.0); OX = so.fetch('cal_ox', 0.0)
    SY = so.fetch('cal_sy', 1.0); OY = so.fetch('cal_oy', 0.0)
    MINCUT = so.fetch('cal_mincut', MINCUTOFF); BETA_ = so.fetch('cal_beta', BETA)

    # frame-gate physics in production; recompute every cook in emulator/test mode
    frame = absTime.frame
    new_frame = (frame != so.fetch('lastframe', -1)) or (emu is not None)
    if new_frame:
        so.store('lastframe', frame)
        now = absTime.seconds
        dt = min(max(now - so.fetch('last', now), 1e-4), MAX_DT)
        so.store('last', now)
        so.store('dt', dt)
    else:
        dt = so.fetch('dt', 1.0 / 60.0)

    # which physical hand is LEFT vs RIGHT (mirror-proof: smaller pinch-midpoint x = left)
    h1_on = _f(hp, 'h1:hand_active', 0.0) > 0.5
    h2_on = _f(hp, 'h2:hand_active', 0.0) > 0.5
    x1 = _hand_x(h1, 'h1') if h1_on else -1.0
    x2 = _hand_x(h2, 'h2') if h2_on else -1.0
    if x1 >= 0.0 and x2 >= 0.0:
        if x1 <= x2:
            srcL, pfxL, srcR, pfxR = h1, 'h1', h2, 'h2'
        else:
            srcL, pfxL, srcR, pfxR = h2, 'h2', h1, 'h1'
        both_hands = True
    else:
        srcL, pfxL, srcR, pfxR = h1, 'h1', h2, 'h2'
        both_hands = False
    so.store('left_is', pfxL if both_hands else '?')

    # ---- compute the 4 corners (filtered, hold-on-blink) ----
    out = []
    all_seen = both_hands
    cxsum = cysum = 0.0
    for name, side, finger, dflt in CORNERS:
        src, pfx = (srcL, pfxL) if side == 'L' else (srcR, pfxR)
        mx, my, seen = _tip(src, pfx, finger)
        seen = seen and both_hands
        x = mx * SX + OX           # calibrated window-UV
        y = my * SY + OY
        if not seen:
            all_seen = False
            fx = so.fetch(name + '_fx', dflt[0])
            fy = so.fetch(name + '_fy', dflt[1])
        elif emu is not None:
            fx, fy = x, y                              # clean data -> snap (exact tests)
            so.store(name + '_x_x', x); so.store(name + '_y_x', y)
        elif new_frame:
            fx = _one_euro(so, name + '_x', x, dt, MINCUT, BETA_)
            fy = _one_euro(so, name + '_y', y, dt, MINCUT, BETA_)
        else:
            fx = so.fetch(name + '_fx', x)
            fy = so.fetch(name + '_fy', y)
        so.store(name + '_fx', fx); so.store(name + '_fy', fy)
        cxsum += fx; cysum += fy
        out += [(name + 'x', fx), (name + 'y', fy)]

    # ---- active flag (all 4 tips) with hold-on-blink + smoothed alpha ----
    held = so.fetch('hold', 0)
    alpha = so.fetch('alpha', 0.0)
    if new_frame:
        if all_seen:
            held = HOLD_FRAMES
        elif held > 0:
            held -= 1
        so.store('hold', held)
        target = 1.0 if (all_seen or held > 0) else 0.0
        fade = 1.0 if emu is not None else min(ACTIVE_FADE * dt, 1.0)
        alpha += (target - alpha) * fade
        so.store('alpha', alpha)
    active = 1.0 if (all_seen or held > 0) else 0.0

    # ---- subtle energy from hand velocity (drives scan speed / glow pulse) ----
    e_sm = so.fetch('energy', 0.0)
    if new_frame:
        hv = max(_f(hp, 'h1:hand_velocity', 0.0), _f(hp, 'h2:hand_velocity', 0.0))
        raw = max(0.0, min(hv, 1.0))
        e_sm += (raw - e_sm) * ENERGY_SMOOTH
        so.store('energy', e_sm)

    out += [('cx', cxsum * 0.25), ('cy', cysum * 0.25),
            ('active', active), ('alpha', alpha), ('energy', e_sm),
            ('aspect', ASPECT)]
    for nm, v in out:
        so.appendChan(nm)[0] = float(v)
    return
