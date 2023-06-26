#version 330 core

layout (location=0) in vec2 vertexPos;

uniform uvec2 iResolution;
uniform float iFactor;
uniform float iTime;


out vec4 fragmentColor;

void main() {
  gl_Position = vec4(vertexPos, 0.0, 1.0);
  fragmentColor = vec4(0.0, 0.0, 0.0, 1.0);
}