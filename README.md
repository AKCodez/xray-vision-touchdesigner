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

It's driven entirely by **MediaPipe hand tracking → a TouchDesigner GLSL pipeline**.

> ### 🧭 Two ways to use this
> **① Just run the effect** — you only need TouchDesigner + the MediaPipe plugin + a webcam.
> **No AI, no Node.js, no MCP required.** Jump to [Quick Start](#-quick-start--just-run-the-effect).
> **② Drive / rebuild it with an AI agent** — the way this project was built. Add the
> **TouchDesigner MCP** so Claude can build, emulate hands, and self-test it for you.
> See [Connect the TouchDesigner MCP](#-connect-the-touchdesigner-mcp-optional).

---

## ✨ Highlights

- **Gesture-framed** — only your two **thumbs + index fingers** define and activate the window.
- **Exact tracking** — corners sit on your fingertips (self-test asserts < 0.01 error), One-Euro
  smoothing locks them steady when still and snaps when you move.
- **Pure X-ray filter** — Sobel edge-glow + inverted luma + electric-blue/cyan, particles, scanline.
- **Clean feed** — every MediaPipe debug overlay (boxes, mesh, skeleton, labels) is disabled.
- **Movable output window** — a borderless/draggable window you can throw on any monitor.
- **Robust** — mirror-proof L/R hand assignment, hold-on-blink, premultiplied compositing.

---

## 🧰 What you'll need

### To run the effect

| # | Requirement | Version | Where to get it | Why |
|---|---|---|---|---|
| 1 | **TouchDesigner** | 2025.x (any recent). **Non-Commercial (free)** is fine | [derivative.ca/download](https://derivative.ca/download) | the host app the whole thing runs in |
| 2 | **A webcam** | any | built-in or USB | the camera the hand tracking reads |
| 3 | **MediaPipe plugin** | v0.5.2+ | [github.com/torinmb/mediapipe-touchdesigner](https://github.com/torinmb/mediapipe-touchdesigner/releases) → grab the `.tox` | does the actual hand tracking + camera feed. **Not bundled here** (it's a separate plugin) |
| 4 | **This project** | — | `git clone https://github.com/AKCodez/xray-vision-touchdesigner` | the effect itself (`.toe` + scripts + shaders) |

> 💡 **New to TouchDesigner?** The **Textport** is TD's built-in Python console — open it with
> **`Alt + T`** (or *Dialogs → Textport*). Every command below that starts with `exec(...)` gets
> pasted there and run with **Enter**.

### Extra, only for the AI / MCP path (optional)

| # | Requirement | Version | Where to get it | Why |
|---|---|---|---|---|
| 5 | **Node.js** | 18.x or later | [nodejs.org](https://nodejs.org) | runs the MCP server via `npx` |
| 6 | **TouchDesigner MCP** | latest | [github.com/8beeeaaat/touchdesigner-mcp](https://github.com/8beeeaaat/touchdesigner-mcp/releases) | lets an AI agent control TouchDesigner |
| 7 | **Claude Code** (or Claude Desktop) | — | [claude.com/code](https://claude.com/code) | the AI agent that talks to the MCP |

---

## 🚀 Quick Start — just run the effect

> 📁 In the commands below, replace **`<REPO>`** with the folder you cloned into,
> e.g. `C:\Users\You\xray-vision-touchdesigner`.

**1. Install TouchDesigner** (free Non-Commercial license is fine) and **plug in a webcam**.

**2. Install the MediaPipe plugin** — download the latest `.tox` from the
[torinmb/mediapipe-touchdesigner releases](https://github.com/torinmb/mediapipe-touchdesigner/releases).

**3. Get this project:**
```bash
git clone https://github.com/AKCodez/xray-vision-touchdesigner.git
```

**4. ⚙️ Point the scripts at your folder** *(one-time, important — skip this and you'll get
`FileNotFoundError`)*. Open `scripts/build_all.py` and edit the path near the top:
```python
ROOT = r'C:\Users\User\finger-bridge'      # ← change to your <REPO> folder
```
Do the same in `scripts/selftest.py` and `scripts/reload_shaders.py` if you plan to use them.

**5. Open `finger_bridge.toe`** in TouchDesigner. *(The `.toe` keeps its original name from when
this project started life as "finger-bridge" — same file, current X-ray effect.)*

**6. Add the MediaPipe plugin to the project.** Drag the MediaPipe `.tox` into the network and
choose **"Enable External .tox"** (keeps the `.toe` small), then use its auto-connect button to
generate the helper components. The build expects the plugin to provide
`/project1/MediaPipe` and `/project1/hand_tracking2`.

**7. Check the feed is wired** — in the Textport (`Alt+T`), with both hands up:
```python
exec(open(r'<REPO>\scripts\preflight.py').read())
```
It prints `READY to build_all` when the camera + both hands are detected (or tells you exactly
what's missing).

**8. Build the effect:**
```python
exec(open(r'<REPO>\scripts\build_all.py').read())   # turnkey, self-cleaning
```

**9. Raise both hands** so thumb + index of each frame a rectangle, and watch `/project1/fb_out`.

---

## 🤖 Connect the TouchDesigner MCP *(optional)*

This is how the project was actually built — an AI agent (Claude) driving TouchDesigner through the
[**8beeeaaat/touchdesigner-mcp**](https://github.com/8beeeaaat/touchdesigner-mcp) server. With it
connected, the agent can run `build_all.py`, **emulate synthetic hands**, and run the **9/9 self-test**
for you. You don't need this to use the effect — only to rebuild or modify it with AI.

It has **two halves** that must both be running: a small **component inside TouchDesigner** (a web
server on port `9981`) and the **MCP server** (Node) that your AI agent launches and talks to.

### Step 1 — Install Node.js 18+
Download from [nodejs.org](https://nodejs.org), then confirm in a terminal:
```bash
node --version      # should print v18.x or higher
```

### Step 2 — Register the MCP server with your agent

**Claude Code** (one command):
```bash
claude mcp add -s user touchdesigner -- npx -y touchdesigner-mcp-server@latest --stdio
```

<details>
<summary>…or configure it by hand (Claude Code <code>~/.claude.json</code> / Claude Desktop <code>claude_desktop_config.json</code>)</summary>

```json
{
  "mcpServers": {
    "touchdesigner": {
      "command": "npx",
      "args": ["-y", "touchdesigner-mcp-server@latest", "--stdio"]
    }
  }
}
```
*(Claude Desktop also offers a one-click `touchdesigner-mcp.mcpb` bundle — double-click to install.)*
</details>

### Step 3 — Add the TouchDesigner-side component
1. On the [latest release](https://github.com/8beeeaaat/touchdesigner-mcp/releases), download
   **`touchdesigner-mcp-td.zip`** and **extract it**.
2. ⚠️ **Don't move or rename anything inside the extracted folder** — `mcp_webserver_base.tox`
   loads files from its `modules/` folder by relative path.
3. In TouchDesigner, **import `mcp_webserver_base.tox`** and drop it at
   **`/project1/mcp_webserver_base`** (or anywhere you like).
4. It starts a Web Server DAT listening on **`http://127.0.0.1:9981`** — the default the MCP
   server connects to.

### Step 4 — Verify the connection
1. Make sure TouchDesigner is open with `mcp_webserver_base.tox` running.
2. (Re)start Claude Code / Claude Desktop.
3. In Claude Code, run **`/mcp`** — **`touchdesigner`** should show as **connected**.
4. Quick sanity check from a terminal: `curl http://127.0.0.1:9981` should respond.

> If it's not connected: confirm Node 18+, confirm the `.tox` is running on `9981`
> (TD isn't running on a different port), then restart the agent. See
> [Troubleshooting](#️-troubleshooting).

### What it unlocks
```python
exec(open(r'<REPO>\scripts\emulate_hands.py').read())   # synthetic hands — no webcam needed
exec(open(r'<REPO>\scripts\selftest.py').read())        # 9/9: compile, exact corners, masking…
```
The agent can now build, tune, and verify the effect end-to-end on its own.

---

## 🪟 Output window — move it anywhere
```python
exec(open(r'<REPO>\scripts\window.py').read())
```
Shows **only the effect** (no network, no operators):
`show(w,h,x,y)` draggable window → drag to any monitor · `fullscreen(x,y,w,h)` borderless ·
`move(x,y)` · `close()`.

## 🎯 Tune the tracking (live, no rebuild)
```python
exec(open(r'<REPO>\scripts\tune.py').read())
```
`flipy()` / `flipx()` mirror fixes · `nudge(dox,doy)` offset · `scale(dsx,dsy)` span ·
`smooth(mincutoff,beta)` steady↔snappy · `status()`.

## ✅ Verify
```python
exec(open(r'<REPO>\scripts\selftest.py').read())   # 9/9: compile, exact corners, masking…
```

---

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
scripts/   build_all.py  (turnkey builder)               xray_state.py   (the brain)
           preflight.py  (check the feed)                emulate_hands.py (synthetic hands)
           selftest.py   (9/9 checks)                    window.py · tune.py
           bind_uniforms.py · reload_shaders.py · diag_state.py
docs/      build-plan.md · td-data-map.md                captures/  demo.gif · demo.mp4 · stills
finger_bridge.toe
```

---

## 🛠️ Troubleshooting

| Symptom | Likely fix |
|---|---|
| **`FileNotFoundError`** when running `build_all.py` | You skipped step 4 — set `ROOT` at the top of `build_all.py` (and `selftest.py` / `reload_shaders.py`) to your clone folder. |
| **Window never appears** / nothing activates | All **four** fingertips (both thumbs + both index fingers) must be visible to the camera. Run `preflight.py` to confirm both hands are detected. |
| **Camera is black** / "camera in use" | Another app or TD project owns the webcam — only one can. Close the other one and re-cook. |
| **`preflight.py` says MediaPipe nodes are missing** | The plugin isn't added (or is in the wrong place). Make sure the MediaPipe `.tox` provides `/project1/MediaPipe` and `/project1/hand_tracking2`. |
| **Tracking is offset or the Y axis feels reversed** | Run `tune.py`, then `flipy()` / `nudge()` / `scale()`, and `status()` to confirm — no rebuild needed. |
| **Output looks soft / isn't true 1080p** | Non-Commercial license caps textures at 1280×720; the window upscales for display. A Commercial/Pro license removes the cap. |
| **`touchdesigner` MCP won't connect** | Node 18+? Is `mcp_webserver_base.tox` open and running on `:9981`? Restart Claude Code and check `/mcp`. `curl http://127.0.0.1:9981` should answer. |

---

## 📝 Notes

- **Resolution:** TouchDesigner **Non-Commercial** caps textures at 1280×1280, so the 16:9 ceiling
  is **1280×720** (the window upscales to 1080p for display). A Commercial/Pro license removes the cap.
- The MediaPipe **plugin** ([torinmb/mediapipe-touchdesigner](https://github.com/torinmb/mediapipe-touchdesigner))
  isn't included here — install it separately; `build_all.py` then wires the effect on top of it.
- `shaders/_archive_rave/` keeps the original 5-band "rave filter" version of this project.

<div align="center"><sub>Built with Claude Code via the TouchDesigner MCP.</sub></div>
