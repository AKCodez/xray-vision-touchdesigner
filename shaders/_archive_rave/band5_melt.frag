// BAND 5 — MOTION-BLUR TRAILS + PIXEL-MELT   (pair: pinky)
//   input 0 = camera,  input 1 = FEEDBACK of this TOP's own output (fb_b5_feedback)
// Samples last frame's output and mixes with the current camera-derived look via a
// decay -> persistent neon trails. Adds a directional smear along the bridge axis, a
// vertical pixel-melt/drip, and datamosh block-slip. Persisted trail hue rotates in HSV
// for rave color rivers.
// Reactive: uEnergy -> longer trails, heavier melt, bigger blocks, faster hue drift;
// uDist -> longer smear + comet tails; uBeat -> rhythmic clear-frame stutter.

void main(){
    vec2 uv = vUV.st;
    if (uActive < 0.5){ fragColor = TDOutputSwizzle(vec4(0.0)); return; }
    Band B = bandLocal(uv);
    vec2 luv = bandUV(B);
    vec2 exScreen = B.ex / vec2(uAspect, 1.0);     // bridge axis in screen UV
    vec2 eyScreen = B.ey / vec2(uAspect, 1.0);     // across axis in screen UV

    // datamosh block melt: quantize UV into sliding blocks at high energy
    float grid = mix(220.0, 40.0, clamp(uEnergy, 0.0, 1.0));   // bigger blocks when hot
    vec2 blockUV = floor(uv * grid) / grid;
    float slip = step(0.85, hash21(floor(uv * grid) + floor(uTime * 6.0)));
    vec2 muv = mix(uv, blockUV + exScreen * slip * 0.04, uEnergy * 0.7);

    // vertical pixel-melt / drip: push samples DOWN the across-axis
    float colId = floor(luv.x * 120.0);
    float drip = fbm(vec2(colId * 0.13, uTime * 0.5));
    vec2 smuv = muv - eyScreen * (drip * (0.05 + 0.18 * uEnergy));

    // directional smear along the bridge (motion blur); longer bar smears more
    vec2 vel = exScreen * (0.01 + 0.06 * uDist) * (0.4 + uEnergy);
    vec3 curr = vec3(0.0);
    for (int i = 0; i < 8; i++) curr += texture(sTD2DInputs[0], smuv - vel * float(i) / 8.0).rgb;
    curr /= 8.0;

    // feedback trails (shifted read => flowing trail)
    vec3 fb = texture(sTD2DInputs[1], uv - vel * 0.5).rgb;
    float decay = mix(0.55, 0.92, clamp(uEnergy, 0.0, 1.0));   // hotter = longer trails
    decay *= (1.0 - 0.4 * strobe());                           // beat punches a clear frame
    vec3 fhsv = rgb2hsv(fb);
    fhsv.x = fract(fhsv.x + 0.08 + 0.15 * uEnergy);            // hue drift
    fhsv.y = min(fhsv.y * 1.3 + 0.1, 1.0);                     // pump saturation
    fb = hsv2rgb(fhsv);

    vec3 col = mix(curr, fb, decay);
    // recolour the melt into neon by luma, so even a neutral scene drips colour.
    float ly = luma(col);
    vec3 neon = neonPal(ly * 1.3 + luv.x * 0.45 + drip * 0.4 + uTime * 0.08);
    col = mix(col, (0.25 + col) * neon * 1.9, 0.8);       // melt into neon rivers
    col += max(ly - 0.35, 0.0) * neon * 1.6;              // hot drips glow
    col += smoothstep(0.6, 0.95, fract(luv.y * 8.0 - uTime)) * neon * 0.35 * uEnergy; // drip streaks
    col += strobe() * neon * 0.5;

    fragColor = TDOutputSwizzle(bandOut(col, B));
}
