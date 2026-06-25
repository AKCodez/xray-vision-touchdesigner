# X-ray window — TD data contract

## Plugin inputs (confirmed live)

- **Fingertips:** `/project1/hand_tracking2/h1/out1` & `/h2/out1` → `h{1,2}:thumb_tip:{x,y}`
  and `h{1,2}:index_finger_tip:{x,y}` (MediaPipe-normalized 0..1, top-down y).
- **Activity:** `/project1/hand_tracking2/helpers` → `h{1,2}:hand_active`, `h{1,2}:hand_velocity`.
- **Clean camera:** `/project1/MediaPipe/video` (1280×720) **with all overlays OFF**. The plugin
  renders its feed through an internal web view that draws detection boxes / face mesh / pose
  skeleton / confidence labels; `build_all` disables every `Generate*gui`, `Showoverlays`, and the
  unused detectors so the feed is clean (tracking DATA is unaffected).

## Brain output — `fb_xray_state` (14 channels)

`tlx tly trx try brx bry blx bly` — the 4 window corners in screen UV
(TL=left index, TR=right index, BR=right thumb, BL=left thumb); `cx cy` centroid;
`active` (all 4 tips seen, hold-on-blink); `alpha` (smoothed fade); `energy` (hand velocity);
`aspect`.

Mapping: `corner_uv = raw_fingertip * (cal_sx, cal_sy) + (cal_ox, cal_oy)`, then a One-Euro
filter (`cal_mincut`, `cal_beta`). All `cal_*` live in Script-CHOP storage and are tuned by
`scripts/tune.py` with no rebuild; defaults are baked in `xray_state.py`.

## Uniform packing — `fb_xray` GLSL TOP (6 vec slots, expression-bound)

| slot | uniform | components |
|---|---|---|
| 0 | `uTL` | tlx, tly |
| 1 | `uTR` | trx, try |
| 2 | `uBR` | brx, bry |
| 3 | `uBL` | blx, bly |
| 4 | `uState` | active, alpha, time(`absTime.seconds`), aspect(1280/720) |
| 5 | `uExtra` | energy, resX(1280), resY(720), 0 |

The shader uses Inigo Quilez `invBilinear` to map a screen pixel into quad-local `(u,v)`
(inside ⇔ `u,v ∈ [0,1]`), applies the X-ray filter to the camera inside, draws the frame +
corner brackets, and outputs **premultiplied** `vec4(col*a, a)` (transparent outside).
