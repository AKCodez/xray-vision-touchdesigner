# X-ray window — build plan & notes

`build_all.py` constructs the whole effect under `/project1` (namespaced `fb_*`) in one pass,
self-cleaning (wipes prior `fb_*`, removes TD auto-companion DATs).

## Build order

1. **Plugin config** — `Gnumhands=2`, `Detectgestures=1`, `Wflip=1`; **all** `Generate*gui` +
   `Showoverlays` + unused detectors (face/pose/object/segment/image) **OFF** → clean camera feed.
2. **`fb_video`** (Null ← `MediaPipe/video`, camera-native 1280×720) · **`fb_tick`** (LFO, always-cook).
3. **`fb_xray_state`** (Script CHOP ← `xray_state.py`, input `fb_tick`) — the brain (4 corners, One-Euro).
4. **`fb_xray`** (GLSL TOP ← `xray.frag`, `rgba8fixed`) — quad mask + camera X-ray + frame; uniforms
   expression-bound to the brain via `bind_xray`.
5. **`fb_comp`** (Composite TOP `over`): in0 = `fb_xray` (top), in1 = `fb_video` (bottom).
6. **`fb_post_bloom`** (glow) → **`fb_post_grade`** (Level) → **`fb_out`** (Null) → **`fb_window`** (Window COMP).

## Verify

`selftest.py` builds fresh, drives a synthetic framing pose over a deterministic scene, and asserts
**9/9**: 14 brain channels · shader compiles · window active with 4 tips · **1280×720 (license max)** ·
**corners on fingertips < 0.01 (exact)** · quad non-degenerate · X-ray inside · scene through gaps
(premult) · non-trivial output. Restores live mode on exit.

## Output window & tuning

- `window.py` — `show()` (clean draggable window, drag to any monitor), `fullscreen(x,y,w,h)`,
  `move()`, `close()`. Shows only `fb_out`.
- `tune.py` — live calibration of fingertip→screen mapping (stored on the brain, no rebuild):
  `flipy() flipx() nudge() scale() smooth() cal() status()`.

## Gotchas discovered & fixed (live)

- **Debug overlays on the camera** — `MediaPipe/video` is rendered through an internal web view that
  draws every detector's boxes/mesh/skeleton/labels. Fix: turn off all `Generate*gui` + `Showoverlays`
  + unused detectors (tracking data is unaffected). This is the "remove the debug points" fix.
- **Resolution capped at 1280×720** — TD **Non-Commercial license** limits textures to 1280×1280, so a
  1920×1080 request silently scales to 1280×720 (even a blank Constant TOP). 1280×720 is the 16:9 max;
  the window upscales to 1080p for display. Commercial/Pro removes the cap.
- **Y reversed on the live camera** — the emulator mirrors the brain's own Y convention, so synthetic
  tests can't catch a real-camera flip. Mapping is `cal_sy`/`cal_oy` (default un-flipped); `tune.py`
  `flipy()` toggles it. Confirmed against the live feed.
- **Exact tracking** — One-Euro filter (steady when still, snappy when moving) instead of laggy EMA.
- **Composite needs premultiplied alpha + camera on the bottom input** (`vec4(col*a, a)`).
- **Float pixel formats corrupt alpha** → `rgba8fixed`. **GLSL compile errors show as warnings** →
  read via Info DAT. **`half` is a GLSL reserved word.** **Op classes/`ParMode` not global in the MCP
  exec context** → `getattr(td, ...)` / derive `ParMode` from a parameter's `.mode`.
- The frame-gate is bypassed in emulator mode so synchronous self-tests update; the
  `fb_xray_state` cook-loop warning is the harmless frame-gated one.
