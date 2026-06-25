// bridge_common.glsl — shared header prepended to every finger-bridge band shader.
// TouchDesigner GLSL TOPs have no #include, so build_all.py / reload_shaders.py
// concatenate this block in front of each bandN_*.frag before loading into the
// GLSL TOP's pixeldat. Do NOT declare #version (TD injects its own preamble).
//
// Conventions (confirmed from gum-gum-td/shaders/gumgum_warp.frag):
//   - single output:           layout(location = 0) out vec4 fragColor;
//   - sample inputs:           texture(sTD2DInputs[i], uv)   (camera = input 0)
//   - uv:                      vUV.st   (0..1, bottom-up)
//   - aspect-correct distance: multiply by vec2(uAspect, 1.0)
//   - always finish main with: fragColor = TDOutputSwizzle(color);
//
// Bands are LAYERS composited Over the camera downstream, so each band outputs
// straight color + alpha:  vec4(fx, bandMask*uActive*uAlpha).  Outside the band
// alpha = 0 -> the camera shows through.  Inactive band -> output vec4(0).

layout(location = 0) out vec4 fragColor;

// ---- packed uniform slots (bound by scripts/bind_uniforms.py :: bind_band) ----
// Packing keeps the binding identical for all 5 bands (6 vector slots, 0..5).
uniform vec2 uP0;        // slot 0  LEFT fingertip  (video UV, y bottom-up)
uniform vec2 uP1;        // slot 1  RIGHT fingertip (video UV)
uniform vec2 uCenter;    // slot 2  band center (cx, cy)
uniform vec2 uDistLen;   // slot 3  x = raw UV distance, y = aspect-true length
uniform vec4 uMisc;      // slot 4  x=angle(rad) y=halfThickness z=energy w=beat
uniform vec4 uState;     // slot 5  x=active(0/1) y=alpha(fade) z=time(s) w=aspect

#define uDist      uDistLen.x
#define uLength    uDistLen.y
#define uAngle     uMisc.x
#define uThickness uMisc.y
#define uEnergy    uMisc.z
#define uBeat      uMisc.w
#define uActive    uState.x
#define uAlpha     uState.y
#define uTime      uState.z
#define uAspect    uState.w

const float TAU = 6.28318530718;
const float PI  = 3.14159265359;

// neon accent palette (rave) — hex in comments
const vec3 NEON_MAGENTA = vec3(1.00, 0.07, 0.78); // #FF12C7
const vec3 NEON_CYAN    = vec3(0.05, 1.00, 0.96); // #0DFFF5
const vec3 NEON_LIME    = vec3(0.68, 1.00, 0.07); // #AEFF12
const vec3 NEON_VIOLET  = vec3(0.55, 0.16, 1.00); // #8C29FF
const vec3 NEON_ORANGE  = vec3(1.00, 0.45, 0.05); // #FF730D
const vec3 HOT_PINK     = vec3(1.00, 0.16, 0.42); // #FF296B

// ---------------------------- hashing / noise ----------------------------
float hash11(float p){ p = fract(p * 0.1031); p *= p + 33.33; p *= p + p; return fract(p); }
float hash21(vec2 p){
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}
vec2 hash22(vec2 p){
    vec3 p3 = fract(vec3(p.xyx) * vec3(0.1031, 0.1030, 0.0973));
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.xx + p3.yz) * p3.zy);
}
float vnoise(vec2 p){
    vec2 i = floor(p), f = fract(p);
    vec2 u = f * f * (3.0 - 2.0 * f);
    float a = hash21(i),            b = hash21(i + vec2(1, 0));
    float c = hash21(i + vec2(0,1)), d = hash21(i + vec2(1, 1));
    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}
float fbm(vec2 p){
    float v = 0.0, a = 0.5;
    for (int i = 0; i < 5; i++){ v += a * vnoise(p); p *= 2.02; a *= 0.5; }
    return v;
}

// --------------------------- color: palettes / hsv -----------------------
// IQ cosine palette: a + b*cos(TAU*(c*t + d))
vec3 pal(float t, vec3 a, vec3 b, vec3 c, vec3 d){ return a + b * cos(TAU * (c * t + d)); }
// saturated neon rainbow used for the shared "hue rises with your hands" behavior
vec3 neonPal(float t){
    return pal(t, vec3(0.55, 0.40, 0.55), vec3(0.50, 0.55, 0.55),
                  vec3(1.0), vec3(0.00, 0.18, 0.40));
}
vec3 rgb2hsv(vec3 c){
    vec4 K = vec4(0.0, -1.0/3.0, 2.0/3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));
    float d = q.x - min(q.w, q.y), e = 1e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}
vec3 hsv2rgb(vec3 c){
    vec3 p = abs(fract(c.xxx + vec3(0.0, 1.0/3.0, 2.0/3.0)) * 6.0 - 3.0);
    return c.z * mix(vec3(1.0), clamp(p - 1.0, 0.0, 1.0), c.y);
}
float luma(vec3 c){ return dot(c, vec3(0.299, 0.587, 0.114)); }

// Keep bright filter output as SATURATED neon instead of blowing out to white.
// Hue-preserving highlight rolloff (divide by the peak channel when >1) + a saturation
// push around luma. A pure-white input stays white; a bright orange stays bright orange.
vec3 vivid(vec3 c){
    c = max(c, vec3(0.0));
    float peak = max(max(c.r, c.g), c.b);
    if (peak > 1.0) c /= peak;                 // overbright -> full-intensity hue, not white
    float y = luma(c);
    return clamp(mix(vec3(y), c, 1.35), 0.0, 1.0);
}

// ----------------------- band-local transform (stretch) -------------------
// THE stretch/warp engine. L.x runs ALONG the bridge (tip->tip), L.y ACROSS it.
// As the fingertips separate, half.x grows, so every along-axis pattern stretches
// like a pulled ribbon. Vertical motion moves center / rotates the frame for free.
struct Band { vec2 L; vec2 hsize; vec2 center; float len; vec2 ex; vec2 ey; };

Band bandLocal(vec2 uv){
    vec2 asp = vec2(uAspect, 1.0);
    vec2 P = uv * asp, A = uP0 * asp, B = uP1 * asp;
    vec2 c = 0.5 * (A + B);
    vec2 ax = B - A;
    float len = max(length(ax), 1e-5);
    vec2 ex = ax / len;                 // +X along the bridge
    vec2 ey = vec2(-ex.y, ex.x);        // +Y across the bridge
    vec2 d = P - c;
    Band bd;
    bd.L      = vec2(dot(d, ex), dot(d, ey));
    bd.hsize   = vec2(0.5 * len, uThickness);
    bd.center = c;
    bd.len    = len;
    bd.ex     = ex;
    bd.ey     = ey;
    return bd;
}
// normalized 0..1 coords inside the band rectangle (for sampling filter patterns)
vec2 bandUV(Band b){
    return vec2(clamp(b.L.x / (b.hsize.x * 2.0) + 0.5, 0.0, 1.0),
                clamp(b.L.y / (b.hsize.y * 2.0) + 0.5, 0.0, 1.0));
}
// convert a band-local offset back to a screen UV (for re-sampling the camera warped)
vec2 bandToScreen(Band b, vec2 localOffset){
    vec2 asp = vec2(uAspect, 1.0);
    vec2 world = b.center + localOffset.x * b.ex + localOffset.y * b.ey;
    return world / asp;
}

// ------------------------------- SDFs / mask ------------------------------
float sdBox(vec2 p, vec2 b){
    vec2 d = abs(p) - b;
    return length(max(d, 0.0)) + min(max(d.x, d.y), 0.0);
}
// aspect-corrected point->segment distance (the gum-gum capsule primitive)
float distSeg(vec2 p, vec2 a, vec2 b){
    vec2 asp = vec2(uAspect, 1.0);
    vec2 P = p * asp, A = a * asp, B = b * asp;
    vec2 AB = B - A, AP = P - A;
    float ab2 = dot(AB, AB) + 1e-6;
    float t = clamp(dot(AP, AB) / ab2, 0.0, 1.0);
    return distance(P, A + t * AB);
}
// soft oriented-rectangle mask in band-local space -> 1 inside, 0 outside.
// feather breathes a little with energy so the rim "pulses".
float bandMask(Band b){
    float fe = max(uThickness * 0.55, 0.004) + 0.015 * clamp(uEnergy, 0.0, 1.0);
    return 1.0 - smoothstep(0.0, fe, sdBox(b.L, b.hsize));
}

// ------------------------------- beat / strobe ----------------------------
// Motion-only build: uBeat is bound to 0, so beat() falls back to a uTime clock
// (~132 BPM). strobe() WIDTH scales with uEnergy, so it only flashes hard when
// the hands are actually moving — calm = subtle, fast = blinding.
float beat(){
    float fb = 0.5 + 0.5 * sin(uTime * TAU * 2.2);
    return (uBeat > 0.0001) ? uBeat : fb;
}
float strobe(){
    float b = beat();
    float w = mix(0.05, 0.32, clamp(uEnergy, 0.0, 1.0));
    return smoothstep(1.0 - w, 1.0, b);
}

// final alpha for a band layer (mask gated by activity + smoothed fade)
float bandAlpha(Band b){
    return bandMask(b) * clamp(uActive, 0.0, 1.0) * clamp(uAlpha, 0.0, 1.0);
}

// PREMULTIPLIED-alpha band output. TD's Composite/Over TOP 'over' expects premultiplied
// inputs, so the colour MUST be multiplied by alpha — otherwise full-bright filter colour
// leaks everywhere the mask is 0 and washes the frame white. Always end a band with this.
vec4 bandOut(vec3 col, Band b){
    float a = bandAlpha(b);
    return vec4(vivid(col) * a, a);
}
