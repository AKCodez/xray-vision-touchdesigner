// post_chroma.frag — GLOBAL post: chromatic aberration + vignette + faint scanline
// shimmer for rave cohesion. Standalone (NOT using bridge_common). input 0 = the
// composited 5-band image. uAmount is driven by fb_bridge_state['global_energy'] so the
// whole frame RGB-splits and shimmers harder the faster the hands move.

layout(location = 0) out vec4 fragColor;
uniform float uAmount;   // 0..1 global energy
uniform float uAspect;   // width / height
uniform float uTime;     // seconds

void main(){
    vec2 uv = vUV.st;
    vec2 c = uv - 0.5;
    float r = length(c * vec2(uAspect, 1.0));

    // radial RGB split — scales with energy and grows toward the edges
    float amt = (0.0010 + 0.010 * uAmount) * (0.4 + r);
    vec2 dir = normalize(c + 1e-5);
    vec3 col;
    col.r = texture(sTD2DInputs[0], uv + dir * amt).r;
    col.g = texture(sTD2DInputs[0], uv).g;
    col.b = texture(sTD2DInputs[0], uv - dir * amt).b;

    col *= 1.0 - 0.12 * r * r;                                   // vignette
    col *= 1.0 + 0.03 * sin(uv.y * 1400.0 + uTime * 30.0) * uAmount;  // scanline shimmer

    fragColor = TDOutputSwizzle(vec4(col, 1.0));
}
