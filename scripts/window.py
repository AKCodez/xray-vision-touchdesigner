# window.py — open / move / fullscreen the CLEAN output window. It shows ONLY
# /project1/fb_out (the finished effect) — no network, no operators, no debug.
#   exec(open(r'C:\Users\User\finger-bridge\scripts\window.py').read())
#
#   show(w, h, x, y)     - draggable window (title bar): drag it to ANY monitor,
#                          drag edges to resize. Default 1280x720 at (200,120).
#   fullscreen(x,y,w,h)  - borderless, fills a region/monitor (zero chrome). For a
#                          second monitor pass its offset, e.g. fullscreen(1920,0,1920,1080).
#   move(x, y)           - reposition the window live.
#   close()              - close it.

W = op('/project1/fb_window')
W.par.winop = '/project1/fb_out'      # show only the finished effect


def show(w=1280, h=720, x=200, y=120):
    W.par.borders = True               # title bar -> drag anywhere, resize
    W.par.winw = w; W.par.winh = h
    W.par.winoffsetx = x; W.par.winoffsety = y
    W.par.winopen.pulse()
    print('window OPEN — draggable %dx%d at (%d,%d). Drag the title bar to move it.' % (w, h, x, y))


def fullscreen(x=0, y=0, w=1920, h=1080):
    W.par.borders = False              # borderless / clean
    W.par.winoffsetx = x; W.par.winoffsety = y
    W.par.winw = w; W.par.winh = h
    W.par.winopen.pulse()
    print('FULLSCREEN borderless %dx%d at (%d,%d)' % (w, h, x, y))


def move(x, y):
    W.par.winoffsetx = x; W.par.winoffsety = y
    print('moved window to (%d,%d)' % (x, y))


def close():
    W.par.winclose.pulse()
    print('window closed')


show()   # open a clean draggable window now
print('controls: show(w,h,x,y)  fullscreen(x,y,w,h)  move(x,y)  close()')
