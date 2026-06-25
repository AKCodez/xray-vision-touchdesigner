# emulate_hands.py — synthetic fingertip emulator for driving/verifying the effect
# WITHOUT a webcam or real hands. Creates a Script CHOP `fb_emu_hands` that outputs the
# exact channels the brain reads (h1/h2:<finger>:x/y + helpers). The brain auto-switches
# to it when present (see the TEST HOOK in bridge_state.py). Delete fb_emu_hands to return
# to the live webcam.
#   exec(open(r'C:\Users\User\finger-bridge\scripts\emulate_hands.py').read())
# Then call e.g.  pose(sep=0.5, hgt=0.45, spr=1.1);  animate(amp=1.0);  still();  remove()

import td
P = op('/project1')

EMU_CODE = r'''# fb_emu_hands — synthetic two-hands pose (image space, y top-down like MediaPipe).
import math
FINGERS = ['thumb_tip','index_finger_tip','middle_finger_tip','ring_finger_tip','pinky_tip']
# per-finger offsets for a RIGHT hand, palm out, fingers up (dx right+, dy down+).
# X-RAY framing pose: each hand's thumb (lower) + index (upper) sit at the same inner
# x, forming a clean vertical edge -> the 4 tips bound a rectangular window. (middle/
# ring/pinky are emitted but unused by the X-ray brain.)
OFF = {'thumb_tip':(-0.11, 0.17), 'index_finger_tip':(-0.11, -0.17),
       'middle_finger_tip':(-0.04,-0.20), 'ring_finger_tip':(0.04,-0.18),
       'pinky_tip':(0.10,-0.13)}

def onCook(scriptOp):
    if scriptOp.isTimeSlice: scriptOp.isTimeSlice = False
    scriptOp.clear(); scriptOp.numSamples = 1
    f = scriptOp.fetch
    sep = f('sep',0.45); hgt = f('hgt',0.45); spr = f('spr',1.0)
    amp = f('amp',0.0); spd = f('spd',1.0); on = 1.0 if f('on',1.0) > 0.5 else 0.0
    t = absTime.seconds * spd
    sepA = sep + amp*0.16*math.sin(t*1.3)
    hgtA = hgt + amp*0.09*math.sin(t*0.9)
    cxL, cxR = 0.5 - sepA*0.5, 0.5 + sepA*0.5
    def emit(prefix, cx, mirror):
        for i,fg in enumerate(FINGERS):
            dx,dy = OFF[fg]
            if mirror: dx = -dx
            x = cx + dx*spr + amp*0.014*math.sin(t*4.0 + i*1.7)
            y = hgtA + dy*spr + amp*0.012*math.cos(t*3.1 + i)
            scriptOp.appendChan('%s:%s:x'%(prefix,fg))[0] = min(max(x,0.0),1.0)
            scriptOp.appendChan('%s:%s:y'%(prefix,fg))[0] = min(max(y,0.0),1.0)
    emit('h1', cxL, True)    # h1 = LEFT-screen hand (mirror of the right-hand template)
    emit('h2', cxR, False)   # h2 = RIGHT-screen hand (template as-is: thumb inner)
    vel = amp*(0.35 + 0.65*abs(math.sin(t*1.3)))
    for nm,v in [('h1:hand_active',on),('h2:hand_active',on),
                 ('h1:hand_velocity',vel),('h2:hand_velocity',vel),
                 ('hand_distance',abs(cxR-cxL)),
                 ('h1:Leftness',1.0),('h1:Rightness',0.0),
                 ('h2:Leftness',0.0),('h2:Rightness',1.0)]:
        scriptOp.appendChan(nm)[0] = v
    return
'''

code = P.op('fb_emu_code') or P.create(td.textDAT, 'fb_emu_code')
code.text = EMU_CODE; code.nodeX, code.nodeY = -1100, -250
emu = P.op('fb_emu_hands') or P.create(td.scriptCHOP, 'fb_emu_hands')
emu.par.callbacks = code.path; emu.nodeX, emu.nodeY = -900, -250
tick = P.op('fb_tick')
if tick: emu.inputConnectors[0].connect(tick)     # always-cooking so it animates live
for k, v in [('sep',0.45),('hgt',0.45),('spr',1.0),('amp',0.0),('spd',1.0),('on',1.0)]:
    if emu.fetch(k, None) is None: emu.store(k, v)


def pose(sep=None, hgt=None, spr=None):
    e = op('/project1/fb_emu_hands')
    if sep is not None: e.store('sep', sep)
    if hgt is not None: e.store('hgt', hgt)
    if spr is not None: e.store('spr', spr)
    print('pose sep=%s hgt=%s spr=%s' % (e.fetch('sep',0), e.fetch('hgt',0), e.fetch('spr',0)))

def animate(amp=1.0, spd=1.0):
    e = op('/project1/fb_emu_hands'); e.store('amp', amp); e.store('spd', spd)
    print('animate amp=%s spd=%s' % (amp, spd))

def still():
    op('/project1/fb_emu_hands').store('amp', 0.0); print('still (amp=0)')

def hands_off():
    op('/project1/fb_emu_hands').store('on', 0.0); print('hands off (inactive)')

def hands_on():
    op('/project1/fb_emu_hands').store('on', 1.0); print('hands on')

def remove():
    for n in ['fb_emu_hands', 'fb_emu_code']:
        o = op('/project1/' + n)
        if o: o.destroy()
    print('emulator removed -> back to live webcam')


emu.cook(force=True)
print('fb_emu_hands ready. brain now reads synthetic hands.')
print('controls: pose(sep,hgt,spr)  animate(amp,spd)  still()  hands_off()  remove()')
