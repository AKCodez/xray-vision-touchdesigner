<div align="center">

# 🩻 X-Ray Vision Window

### Frame a rectangle with your hands — see *through* it to a glowing real-time X-ray.

<img src="captures/demo.gif" width="300" alt="X-ray vision window — live demo" />

**▶️ [Watch the full demo with sound](captures/demo.mp4)**

![TouchDesigner](https://img.shields.io/badge/TouchDesigner-2025.32820-5B2C8D)
![Python](https://img.shields.io/badge/Python-3.11-3776AB)
![MediaPipe](https://img.shields.io/badge/MediaPipe-hands-00C7B7)
![Realtime](https://img.shields.io/badge/realtime-60_fps-FF2D78)
![Tests](https://img.shields.io/badge/self--test-9%2F9_passing-2EA043)

</div>

---

The **thumb + index fingertips of both hands** define the four corners of a floating
"window." Inside it, the live camera is rendered as a pure **X-ray** — inverted luminance,
glowing cyan edge-outlines, dark background, drifting particles and a scanning line —
wrapped in a glowing blue frame with bright corner brackets. Move your hands and the window
tracks your fingertips **exactly** (One-Euro filtered, sub-frame lag). Outside the window,
the normal scene shows through.

It's driven entirely by **MediaPipe hand tracking → a TouchDesigner GLSL pipeline**, built and
verified through the TouchDesigner MCP with a synthetic fingertip emulator and a 9/9 self-test.

## ✨ Highlights

- **Gesture-framed** — only your two **thumbs + index fingers** define and activate the window.
- **Exact tracking** — corners sit on your fingertips (self-test asserts < 0.01 error), One-Euro
  smoothing locks them steady when still and snaps when you move.
- **Pure X-ray filter** — Sobel edge-glow + inverted luma + electric-blue/cyan, particles, scanline.
- **Clean feed** — every MediaPipe debug overlay (boxes, mesh, skeleton, labels) is disabled.
- **Movable output window** — a borderless/draggable window you can throw on any monitor.
- **Robust** — mirror-proof L/R hand assignment, hold-on-blink, premultiplied compositing.

## 🚀 Run it

Open `finger_bridge.toe`, then in the Textport (`Alt+T`):

```python
exec(open(r'C:\Users\User\finger-bridge\scripts\build_all.py').read())   # turnkey, self-cleaning
```

Raise both hands so thumb + index of each frame a rectangle, and watch `/project1/fb_out`.

### 🪟 Clean output window — move it anywhere
```python
exec(open(r'C:\Users\User\finger-bridge\scripts\window.py').read())
```
Shows **only the effect** (no network, no operators):
`show(w,h,x,y)` draggable window → drag to any monitor · `fullscreen(x,y,w,h)` borderless ·
`move(x,y)` · `close()`.

### 🎯 Tune the tracking (live, no rebuild)
```python
exec(open(r'C:\Users\User\finger-bridge\scripts\tune.py').read())
```
`flipy()` / `flipx()` mirror fixes · `nudge(dox,doy)` offset · `scale(dsx,dsy)` span ·
`smooth(mincutoff,beta)` steady↔snappy · `status()`.

### ✅ Verify
```python
exec(open(r'C:\Users\User\finger-bridge\scripts\selftest.py').read())   # 9/9: compile, exact corners, masking…
```

## 🧠 How it works

```
Webcam → MediaPipe plugin (2 hands, gestures on, ALL overlays OFF → clean feed)
   ├─ hand_tracking2/h1/out1, /h2/out1   thumb_tip + index_finger_tip per hand
   └─ MediaPipe/video → fb_video         clean 1280×720 camera
fb_xray_state  (Script CHOP brain)
   reads 4 fingertips · mirror-proof L/R · One-Euro filter · live calibration
   → emits 4 quad corners (TL=Lindex TR=Rindex BR=Rthumb BL=Lthumb)
fb_xray  (GLSL TOP)
   inverse-bilinear quad mask · pure camera X-ray · glowing frame + corner brackets
   → premultiplied (transparent outside the quad)
fb_comp (X-ray over camera) → fb_post_bloom → fb_post_grade → fb_out → fb_window
```

## 📁 Layout

```
shaders/   xray.frag · bridge_common.glsl                _archive_rave/  (earlier 5-band rave effect)
scripts/   build_all.py · xray_state.py (brain) · window.py · tune.py
           emulate_hands.py · selftest.py · bind_uniforms.py · reload_shaders.py · diag_state.py
docs/      build-plan.md · td-data-map.md                captures/  demo.gif · demo.mp4 · stills
finger_bridge.toe
```

## 📝 Notes

- **Resolution:** TouchDesigner **Non-Commercial** caps textures at 1280×1280, so the 16:9 ceiling
  is **1280×720** (the window upscales to 1080p for display). A Commercial/Pro license removes the cap.
- The MediaPipe **plugin** (torin-blankensmith v0.5.2) isn't included here — install it separately;
  `build_all.py` then wires the effect on top of it.
- `shaders/_archive_rave/` keeps the original 5-band "rave filter" version of this project.

<div align="center"><sub>Built with Claude Code via the TouchDesigner MCP.</sub></div>
