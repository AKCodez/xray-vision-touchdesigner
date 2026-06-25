// BAND 4 — SCANLINE / CRT   (pair: ring)   input 0 = camera
// Full Y2K CRT stack in band-local space: barrel distortion, aperture-grille RGB
// triads, scanlines, chromatic separation along the bridge axis, rolling refresh bar,
// VHS glitch jitter + datablock tear, phosphor bloom. Scanlines run ACROSS the bridge,
// grille columns ALONG it, and both densities stretch with uDist.
// Reactive: uDist -> denser scanlines/grille (pull long = finer CRT); uEnergy -> glass
// bulge + wider chroma + glitch bursts; uBeat -> jitter spike + white flash; vertical -> tint.

void main(){
    vec2 uv = vUV.st;
    if (uActive < 0.5){ fragColor = TDOutputSwizzle(vec4(0.0)); return; }
    Band B = bandLocal(uv);
    vec2 luv = bandUV(B);

    // barrel distortion in local normalized space
    vec2 cc = luv * 2.0 - 1.0;
    float r2 = dot(cc, cc);
    float k = 0.18 + 0.14 * uEnergy;                  // energy bulges the glass
    vec2 cuv = cc * (1.0 + k * r2) * 0.5 + 0.5;

    // reconstruct a screen sample point from the distorted local coords
    vec2 localOff = vec2((cuv.x - 0.5) * B.hsize.x * 2.0, (cuv.y - 0.5) * B.hsize.y * 2.0);
    vec2 suv = bandToScreen(B, localOff);
    vec2 exScreen = B.ex / vec2(uAspect, 1.0);        // bridge axis in screen UV

    // per-scanline glitch jitter (uDist => denser scanlines)
    float line = floor(luv.y * (90.0 + 120.0 * uDist));
    float jit = (hash11(line + floor(uTime * 30.0)) - 0.5);
    float glAmt = 0.004 + 0.03 * uEnergy * strobe();  // glitch bursts on the beat
    suv += exScreen * jit * glAmt;
    float blk = step(0.96, hash11(floor(luv.y * 12.0) + floor(uTime * 8.0)));
    suv += exScreen * blk * 0.05 * uEnergy;           // datablock tear

    // chromatic separation along the bridge axis
    float ca = 0.002 + 0.012 * uEnergy;
    vec3 col = vec3(texture(sTD2DInputs[0], suv + exScreen * ca).r,
                    texture(sTD2DInputs[0], suv).g,
                    texture(sTD2DInputs[0], suv - exScreen * ca).b);

    // aperture-grille RGB triads ALONG the bar
    float colpx = luv.x * (180.0 + 200.0 * uDist);
    int tri = int(mod(colpx, 3.0));
    vec3 mask = (tri == 0) ? vec3(1.0, 0.35, 0.35)
              : (tri == 1) ? vec3(0.35, 1.0, 0.35)
                           : vec3(0.35, 0.35, 1.0);
    col *= mask * 1.7;
    col = col * 1.25 + 0.05;                          // lift brightness (CRT glow)

    // scanlines across the bridge
    col *= 0.5 + 0.5 * sin(luv.y * TAU * (90.0 + 120.0 * uDist));

    // rolling refresh bar
    float roll = fract(luv.y - uTime * 0.4);
    col *= 1.0 + 0.6 * smoothstep(0.0, 0.06, roll) * smoothstep(0.12, 0.06, roll);

    col += max(col - 0.45, 0.0) * 1.3;                // stronger phosphor bloom
    col *= mix(vec3(1.0), neonPal(luv.y + 0.1 * uTime), 0.5);   // hue rides height
    col += strobe() * neonPal(luv.x * 2.0) * 0.6;     // coloured beat flash

    fragColor = TDOutputSwizzle(bandOut(col, B));
}
