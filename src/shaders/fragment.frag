#version 330 core

#ifndef SHADERTOY
  // #include "shadertoy.glsl"
  // out vec4 fragmentColor;
  // uniform float iFactor;
#else
  #iUniform float iFactor = 8.0 in {0.1, 100.0}
#endif


const float PI = 3.14;



vec3 palette(float t) {
  vec3 a = vec3(.5, .5, .5);
  vec3 b = vec3(.5, .5, .5);
  vec3 c = vec3(1., 1., 1.);
  vec3 d = vec3(.1, .2, .3);

  return a + b * cos(6.28318 * (c * t + d));
}


void mainImage(out vec4 fragColor, in vec2 fragCoord) {
  vec2 uv = (fragCoord * 2. - iResolution.xy) / iResolution.y;
  vec2 uv0 = uv;
  float d0 = length(uv0);

  vec3 accColor = vec3(0, 0, 0);

  for (int i = 0; i < 4; i++) {
    uv = fract(uv * 1.5) - .5;

    float d  = length(uv) * exp(-d0);

    vec3 col = palette(d0 + float(i) * .4 + iTime * .4);

    d = sin(d * iFactor + iTime) / iFactor;
    d = abs(d);

    // d = smoothstep(.1, .11, d);
    d = pow(.01 / d, 1.2);

    accColor += col * d;
  }

  fragColor = vec4(accColor, 1.0);
}

void main() {
#ifndef SHADERTOY
  mainImage(gl_FragColor, gl_FragCoord.xy);
#else
  mainImage(fragmentColor, gl_FragCoord.xy);
#endif
}