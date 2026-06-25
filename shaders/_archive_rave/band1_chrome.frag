// BAND 1 — CHROME / LIQUID METAL   (pair: thumbs)   input 0 = camera
// Camera luma -> height -> perturbed normal; a procedural neon "studio" environment
// is reflected off it (no matcap asset needed); fresnel rim, anisotropic glint
// stretched ALONG the bridge, fbm molten flow, and a beat shockwave ring.
// Reactive: uDist stretches the flow/reflection; uEnergy = glossier + brighter +
// faster churn (satin steel -> screaming mercury); uBeat -> shockwave; vertical -> hue.

// procedural chrome environment sampled by the reflected-normal xy.
vec3 chromeEnv(vec3 n, float t){
    // vertical studio gradient: bright top, dark floor, bright horizon kick
    float v = n.y * 0.5 + 0.5;
    vec3 sky   = mix(vec3(0.02,0.03,0.06), vec3(0.55,0.65,0.85), smoothstep(0.35,1.0,v));
    vec3 floorc= mix(vec3(0.01,0.01,0.02), vec3(0.20,0.16,0.24), smoothstep(0.35,0.0,v));
    vec3 env   = mix(floorc, sky, smoothstep(0.42,0.58,v));
    env += pow(max(1.0 - abs(n.y),0.0), 6.0) * vec3(1.1,0.9,0.7) * 0.6;   // horizon band
    // a few neon area-lights swept by time -> colored chrome highlights
    for (int i = 0; i < 3; i++){
        float fi = float(i);
        vec2 lp = vec2(sin(t*0.6 + fi*2.1), cos(t*0.5 + fi*1.7)) * 0.8;
        vec3 lc = (i==0)? NEON_CYAN : (i==1)? NEON_MAGENTA : NEON_LIME;
        float d = length(n.xy - lp);
        env += lc * pow(max(1.0 - d, 0.0), 8.0) * 1.6;
    }
    return env;
}

void main(){
    vec2 uv = vUV.st;
    if (uActive < 0.5){ fragColor = TDOutputSwizzle(vec4(0.0)); return; }
    Band B = bandLocal(uv);
    vec2 luv = bandUV(B);

    // liquid flow: advect the sample coords by scrolling fbm ALONG +X
    float flow = uTime * (0.5 + 1.6 * uEnergy);
    vec2 warp = vec2(fbm(luv * 6.0 + vec2(flow, 0.0)),
                     fbm(luv * 6.0 + vec2(0.0, flow * 0.7))) - 0.5;
    warp *= (0.010 + 0.055 * uEnergy);
    vec2 suv = uv + warp;

    // height field -> normal (finite differences on camera luma)
    vec2 px = vec2(1.5) / vec2(textureSize(sTD2DInputs[0], 0));
    float hL = luma(texture(sTD2DInputs[0], suv - vec2(px.x, 0)).rgb);
    float hR = luma(texture(sTD2DInputs[0], suv + vec2(px.x, 0)).rgb);
    float hD = luma(texture(sTD2DInputs[0], suv - vec2(0, px.y)).rgb);
    float hU = luma(texture(sTD2DInputs[0], suv + vec2(0, px.y)).rgb);
    float bump = 2.0 + 7.0 * uEnergy;                       // glossier with energy
    vec3 N = normalize(vec3((hL - hR) * bump, (hD - hU) * bump, 1.0));

    // reflect a view dir (0,0,1) about N -> environment lookup
    vec3 R = reflect(vec3(0.0, 0.0, -1.0), N);
    vec3 chrome = chromeEnv(R, uTime);

    float fres = pow(1.0 - clamp(N.z, 0.0, 1.0), 5.0);       // fresnel rim
    float aniso = exp(-pow(N.y * 4.0, 2.0)) * pow(max(N.x, 0.0), 1.5); // streak along bridge
    aniso *= 0.6 + 0.9 * uEnergy;
    vec3 tint = neonPal(0.15 * uTime + luv.y * 0.6 + N.x * 0.25);      // hue rides height

    vec3 col = chrome * 1.2;
    col = mix(col, col * tint * 1.8, 0.45);                  // colored chrome
    col = (col - 0.5) * 1.3 + 0.5;                           // crank contrast -> metallic
    col += fres * tint * (1.2 + 1.6 * uEnergy);              // neon fresnel rim
    col += aniso * vec3(1.0);                                // white anisotropic glint
    float spec = pow(max(dot(R, normalize(vec3(0.4, 0.5, 0.75))), 0.0), 64.0);
    col += spec * vec3(1.0) * 2.2;                           // sharp chrome sun hotspot

    // beat shockwave: a bright ring sweeping along the bar
    float sw = abs(fract(luv.x - beat()) - 0.5);
    col += smoothstep(0.035, 0.0, sw) * strobe() * 1.5 * tint;

    fragColor = TDOutputSwizzle(bandOut(col, B));
}
