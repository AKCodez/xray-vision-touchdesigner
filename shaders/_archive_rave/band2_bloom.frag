// BAND 2 — LENS FLARE / BLOOM   (pair: index)   input 0 = camera
// Bright-pass threshold -> anamorphic horizontal streak + aperture star + halo rings
// + god-ray shimmer. Self-contained single pass (the global fb_post_bloom adds extra
// cohesive glow downstream). Reactive: uEnergy lowers threshold + boosts every glow
// term; uDist lengthens the anamorphic streak into long cinematic bars; uBeat = white
// flash; vertical/time = cyan<->gold streak tint.

vec3 tap(vec2 uv){ return texture(sTD2DInputs[0], uv).rgb; }
vec3 bright(vec3 c, float t){ return max(c - t, 0.0) / max(1.0 - t, 1e-3); }

void main(){
    vec2 uv = vUV.st;
    if (uActive < 0.5){ fragColor = TDOutputSwizzle(vec4(0.0)); return; }
    Band B = bandLocal(uv);
    vec2 luv = bandUV(B);
    vec3 base = tap(uv);

    float thr = mix(0.72, 0.46, clamp(uEnergy, 0.0, 1.0));   // energy lowers threshold

    // anamorphic horizontal streak; length scales with uDist + uEnergy
    float len = (0.05 + 0.12 * uDist) * (0.6 + 1.5 * uEnergy);
    vec3 streak = vec3(0.0); float wsum = 0.0;
    for (int i = -24; i <= 24; i++){
        float t = float(i) / 24.0;
        float w = exp(-t * t * 3.0);
        streak += bright(tap(uv + vec2(t * len, 0.0)), thr) * w;
        wsum += w;
    }
    streak /= wsum;
    vec3 cyanGold = mix(NEON_CYAN, NEON_ORANGE, 0.5 + 0.5 * sin(uTime + luv.x * 4.0));
    streak *= cyanGold * 2.6;

    // aperture star (rotated 1D blurs)
    vec3 star = vec3(0.0);
    for (int r = 0; r < 6; r++){
        float ang = TAU * float(r) / 6.0 + 0.2 * uTime;
        vec2 dir = vec2(cos(ang), sin(ang));
        for (int j = 1; j <= 10; j++){
            float t = float(j) / 10.0;
            star += bright(tap(uv + dir * t * 0.05), thr) * (1.0 - t);
        }
    }
    star *= 0.10 * (0.5 + uEnergy);

    // isotropic bloom halo (a few rings)
    vec3 halo = vec3(0.0); float hw = 0.0;
    for (int k = 0; k < 16; k++){
        float ang = TAU * float(k) / 16.0;
        vec2 d = vec2(cos(ang), sin(ang));
        for (float rad = 0.006; rad < 0.05; rad += 0.012){
            float w = 1.0 - rad * 16.0;
            halo += bright(tap(uv + d * rad), thr) * w; hw += w;
        }
    }
    halo /= max(hw, 1.0);

    // god-ray shimmer marching toward band center
    vec3 god = vec3(0.0); float illum = 0.55;
    vec2 c = luv; vec2 dstep = (luv - vec2(0.5)) / 16.0;
    for (int s = 0; s < 16; s++){
        c -= dstep;
        god += bright(tap(bandToScreen(B, (c - 0.5) * vec2(B.hsize.x * 2.0, B.hsize.y * 2.0))), thr) * illum;
        illum *= 0.96;
    }
    god *= 0.05 * (0.5 + uEnergy);

    // procedural neon lens flares — bright cores + anamorphic streaks that exist
    // regardless of how bright the scene is, so the band always reads as flare/bloom.
    vec3 flare = vec3(0.0);
    for (int i = 0; i < 3; i++){
        float fi = float(i);
        vec2 fp = vec2(0.5 + 0.34*sin(uTime*0.7 + fi*2.1), 0.5 + 0.22*cos(uTime*0.9 + fi*1.7));
        vec3 fc = (i==0)?NEON_CYAN : (i==1)?NEON_MAGENTA : NEON_ORANGE;
        float d = length((luv - fp) * vec2(1.0, 0.55));
        flare += fc * (0.010 / (d + 0.010));                                  // glow core
        flare += fc * exp(-pow((luv.y-fp.y)*42.0,2.0)) * exp(-abs(luv.x-fp.x)*2.5) * 0.8; // streak
        flare += fc * pow(max(1.0 - abs(d - 0.18)*6.0, 0.0), 2.0) * 0.4;      // halo ring
    }
    flare *= 0.6 + 1.1 * uEnergy;
    vec3 col = base * 0.45 + streak * 1.3 + star + halo * 1.7 + god + flare;
    col += strobe() * mix(NEON_CYAN, vec3(1.0), 0.5) * 0.9;  // tinted beat flash
    col *= 1.0 + 0.15 * fbm(luv * 40.0);                     // dirty-lens grain

    fragColor = TDOutputSwizzle(bandOut(col, B));
}
