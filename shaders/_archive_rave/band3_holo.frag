// BAND 3 — IRIDESCENT HOLOGRAPHIC   (pair: middle)   input 0 = camera
// Thin-film / oil-slick interference via the cosine palette. Film "thickness" is
// driven by fbm + view angle + VERTICAL POSITION + time + energy, so raising/lowering
// the pair sweeps the whole rainbow through the band. Fresnel rim catches most of the
// spectrum; a high-freq palette adds holographic foil sparkle; a diagonal sheen sweep
// sells "tilt the hologram". The palette is modulated by camera luma so it reads as a
// coating over the real image, not a flat gradient.

vec3 oil(float t){
    return pal(t, vec3(0.5), vec3(0.5), vec3(1.0, 0.9, 0.8), vec3(0.00, 0.15, 0.30));
}

void main(){
    vec2 uv = vUV.st;
    if (uActive < 0.5){ fragColor = TDOutputSwizzle(vec4(0.0)); return; }
    Band B = bandLocal(uv);
    vec2 luv = bandUV(B);
    vec3 cam = texture(sTD2DInputs[0], uv).rgb;

    // camera-luma normal for the angle term
    vec2 px = vec2(1.5) / vec2(textureSize(sTD2DInputs[0], 0));
    float hL = luma(texture(sTD2DInputs[0], uv - vec2(px.x, 0)).rgb);
    float hR = luma(texture(sTD2DInputs[0], uv + vec2(px.x, 0)).rgb);
    float hD = luma(texture(sTD2DInputs[0], uv - vec2(0, px.y)).rgb);
    float hU = luma(texture(sTD2DInputs[0], uv + vec2(0, px.y)).rgb);
    vec3 N = normalize(vec3((hL - hR) * 4.0, (hD - hU) * 4.0, 1.0));
    float NdotV = clamp(N.z, 0.0, 1.0);
    float fres = pow(1.0 - NdotV, 5.0);

    // film thickness — the iridescence driver. luv.y => vertical motion sweeps hue.
    float thick = fbm(luv * 6.0 + uTime * 0.15)
                + (1.0 - NdotV) * 1.2
                + luv.y * 1.25 + luv.x * 0.6        // rainbow sweeps both axes
                + 0.20 * uTime
                + 0.6 * uEnergy;
    vec3 irid = oil(thick);

    // holographic foil micro-sparkle (high-freq palette gated by a hash grid)
    vec2 g = floor(luv * vec2(140.0, 90.0));
    float spk = step(0.92, hash21(g + floor(uTime * 8.0)));
    vec3 foil = oil(thick * 3.0 + 0.5) * spk * 2.0;

    // diagonal sheen sweep, position driven by the beat
    float sd = sin((luv.x * 2.0 + luv.y) * PI + beat() * TAU);
    float sheen = smoothstep(0.7, 1.0, sd);

    vec3 col = cam * 0.22 + irid * (0.95 + 0.35 * luma(cam));  // iridescence dominates
    col += fres * irid * 1.8;                                  // rim = most rainbow
    col += sheen * irid * 1.4 + foil;
    col = mix(col, col * 1.5, strobe());                      // beat brightens foil
    col *= 1.12;

    fragColor = TDOutputSwizzle(bandOut(col, B));
}
