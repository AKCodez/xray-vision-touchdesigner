// BAND_DEBUG — geometry validator. Load this into all 5 band GLSL TOPs during bring-up
// (reload_shaders.py debug mode) to confirm, BEFORE the looks matter, that each band:
//   - sits between the correct fingertip pair,
//   - LENGTHENS when you spread that pair apart,
//   - rides UP/DOWN and tilts as you move the pair.
// Draws: soft band fill (local-UV as R/G), bright rectangle outline, the tip->tip axis
// line, and a dot at each fingertip endpoint. Camera shows through outside.

void main(){
    vec2 uv = vUV.st;
    vec3 cam = texture(sTD2DInputs[0], uv).rgb;
    if (uActive < 0.5){ fragColor = TDOutputSwizzle(vec4(cam, 1.0)); return; }

    Band B = bandLocal(uv);
    vec2 luv = bandUV(B);
    float m = bandMask(B);

    // band fill: local-U -> red, local-V -> green, so orientation is readable
    vec3 fill = vec3(luv.x, luv.y, 0.35);

    // rectangle outline (thin bright border just inside the edge)
    float edge = abs(sdBox(B.L, B.hsize));
    float outline = smoothstep(0.006, 0.0, edge);

    // tip->tip axis line
    float axis = smoothstep(0.004, 0.0, distSeg(uv, uP0, uP1) - 0.0);

    // endpoint dots
    vec2 asp = vec2(uAspect, 1.0);
    float d0 = length((uv - uP0) * asp);
    float d1 = length((uv - uP1) * asp);
    float dot0 = smoothstep(0.018, 0.0, d0);   // LEFT endpoint  (cyan)
    float dot1 = smoothstep(0.018, 0.0, d1);   // RIGHT endpoint (magenta)

    vec3 col = mix(cam, fill, m * 0.55 * clamp(uAlpha, 0.0, 1.0));
    col += outline * NEON_LIME;
    col += axis * vec3(1.0);
    col = mix(col, NEON_CYAN,    dot0);
    col = mix(col, NEON_MAGENTA, dot1);

    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
