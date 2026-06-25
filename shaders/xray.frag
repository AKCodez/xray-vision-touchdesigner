// xray.frag — X-ray vision window. A quad defined by 4 fingertips (thumb+index of
// both hands) frames a "window"; inside, the live camera is rendered as a pure X-ray
// (sobel edge-glow + inverted luma + electric-blue/cyan, dark bg, particles + scanline),
// bordered by a glowing blue frame with cyan corner brackets. Premultiplied output;
// transparent outside the quad. TD GLSL TOP conventions (no #version; end TDOutputSwizzle).

layout(location = 0) out vec4 fragColor;

uniform vec2 uTL, uTR, uBR, uBL;   // quad corners (video UV, y bottom-up)
uniform vec4 uState;               // x=active y=alpha z=time w=aspect
uniform vec4 uExtra;               // x=energy y=resX z=resY w=unused
#define uActive uState.x
#define uAlpha  uState.y
#define uTime   uState.z
#define uAspect uState.w
#define uEnergy uExtra.x
#define uRes    uExtra.yz

const float TAU = 6.28318530718;
const vec3  NAVY  = vec3(0.015, 0.05, 0.13);
const vec3  CYAN  = vec3(0.30, 0.92, 1.0);
const vec3  BLUE  = vec3(0.10, 0.45, 1.0);
const vec3  ICE   = vec3(0.75, 0.95, 1.0);

float luma(vec3 c){ return dot(c, vec3(0.299, 0.587, 0.114)); }
float hash21(vec2 p){
    vec3 p3 = fract(vec3(p.xyx) * 0.1031);
    p3 += dot(p3, p3.yzx + 33.33);
    return fract((p3.x + p3.y) * p3.z);
}

// ---- inverse bilinear (Inigo Quilez): screen point -> quad-local (u,v), or <0 outside ----
float cross2(vec2 a, vec2 b){ return a.x * b.y - a.y * b.x; }
vec2 invBilinear(vec2 p, vec2 a, vec2 b, vec2 c, vec2 d){
    vec2 e = b - a, f = d - a, g = a - b + c - d, h = p - a;
    float k2 = cross2(g, f);
    float k1 = cross2(e, f) + cross2(h, g);
    float k0 = cross2(h, e);
    if (abs(k2) < 1e-5){                                   // edges parallel -> linear
        float v = -k0 / k1;
        float u = (h.x - f.x * v) / (e.x + g.x * v);
        return vec2(u, v);
    }
    float w = k1 * k1 - 4.0 * k0 * k2;
    if (w < 0.0) return vec2(-1.0);
    w = sqrt(w);
    float v1 = (-k1 - w) / (2.0 * k2);
    float v2 = (-k1 + w) / (2.0 * k2);
    float u1 = (h.x - f.x * v1) / (e.x + g.x * v1);
    float u2 = (h.x - f.x * v2) / (e.x + g.x * v2);
    bool b1 = v1 > 0.0 && v1 < 1.0 && u1 > 0.0 && u1 < 1.0;
    bool b2 = v2 > 0.0 && v2 < 1.0 && u2 > 0.0 && u2 < 1.0;
    if (b1 && !b2) return vec2(u1, v1);
    if (!b1 && b2) return vec2(u2, v2);
    return vec2(-1.0);
}

float camL(vec2 uv){ return luma(texture(sTD2DInputs[0], uv).rgb); }

void main(){
    vec2 uv = vUV.st;
    if (uActive < 0.5){ fragColor = TDOutputSwizzle(vec4(0.0)); return; }

    // map this pixel into quad-local (u,v): a=BL, b=BR, c=TR, d=TL
    vec2 q = invBilinear(uv, uBL, uBR, uTR, uTL);
    if (q.x < 0.0 || q.x > 1.0 || q.y < 0.0 || q.y > 1.0){
        fragColor = TDOutputSwizzle(vec4(0.0)); return;     // outside the window
    }

    // ---------------- pure X-ray filter on the camera (see-through) ----------------
    vec2 tx = 1.5 / uRes;
    float l  = camL(uv);
    // sobel edge magnitude
    float gx = camL(uv + vec2(tx.x,0)) - camL(uv - vec2(tx.x,0));
    float gy = camL(uv + vec2(0,tx.y)) - camL(uv - vec2(0,tx.y));
    float edge = clamp(length(vec2(gx, gy)) * 6.0, 0.0, 1.0);
    edge = pow(edge, 0.8);

    vec3 col = NAVY * (0.5 + 0.8 * l);                       // dark base, faint scene
    col += edge * mix(CYAN, ICE, edge) * 2.2;               // glowing bone outlines
    col += smoothstep(0.55, 0.95, l) * CYAN * 0.5;          // bright areas -> bone glow
    col += (1.0 - l) * BLUE * 0.10;                         // faint inverted fill

    // drifting particles ("dust" in the beam)
    vec2 g = floor(q * vec2(70.0, 42.0));
    float pr = hash21(g);
    float tw = fract(pr * 13.0 + uTime * (0.3 + 0.5 * pr));
    float spark = smoothstep(0.96, 1.0, pr) * (0.5 + 0.5 * sin(tw * TAU));
    col += spark * ICE * 1.4;

    // scanline sweep + faint horizontal lines
    float sweep = smoothstep(0.0, 0.04, abs(fract(q.y - uTime * (0.12 + 0.25 * uEnergy)) - 0.5) - 0.46);
    col += sweep * CYAN * 0.6;
    col *= 0.92 + 0.08 * sin(q.y * uRes.y * 0.5);           // subtle scanlines

    // inner vignette
    float vig = smoothstep(0.0, 0.35, q.x) * smoothstep(1.0, 0.65, q.x)
              * smoothstep(0.0, 0.35, q.y) * smoothstep(1.0, 0.65, q.y);
    col *= 0.45 + 0.55 * vig;

    // ---------------- glowing frame + cyan corner brackets ----------------
    float edist = min(min(q.x, 1.0 - q.x), min(q.y, 1.0 - q.y));   // dist to nearest edge
    float bw = 0.028;
    float frame = smoothstep(bw, 0.0, edist);                      // bright at the edge
    col += frame * BLUE * 2.6;
    col += smoothstep(bw * 2.2, 0.0, edist) * BLUE * 0.7;          // inner falloff glow

    float cu = min(q.x, 1.0 - q.x), cv = min(q.y, 1.0 - q.y);
    float bracketLen = 0.13;
    float corner = max(step(cu, bw) * step(cv, bracketLen),
                       step(cv, bw) * step(cu, bracketLen));
    col += corner * ICE * 3.2;                                     // bright corner brackets

    // ---------------- premultiplied output ----------------
    float a = uActive * clamp(uAlpha, 0.0, 1.0);
    a *= smoothstep(0.0, 0.004, edist);                            // hairline soft edge
    fragColor = TDOutputSwizzle(vec4(col * a, a));
}
