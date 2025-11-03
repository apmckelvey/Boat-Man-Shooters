vertex_shader = '''
#version 330
in vec2 in_vert;
out vec2 v_uv;
out vec2 v_world_pos;
uniform vec2 cameraPos;
uniform vec2 viewportSize;
void main() {
    v_uv = in_vert * 0.5 + 0.5;
    v_world_pos = cameraPos + (in_vert * viewportSize * 0.5);
    gl_Position = vec4(in_vert, 0.0, 1.0);
}
'''

fragment_shader = '''
#version 330
precision highp float;

uniform float time;
uniform vec2 boatPosition;
uniform float boatRotation;
uniform vec2 boatVelocity;
uniform float wakeFade;
uniform sampler2D boatTexture;
uniform int numOtherPlayers;
uniform float otherBoatPositions[20];
uniform float otherBoatRotations[10];
uniform float otherBoatSpeeds[10];
uniform float otherBoatSwayPhases[10];
uniform float otherBoatSwayAmps[10];

in vec2 v_uv;
in vec2 v_world_pos;
out vec4 fragColor;

const float BOAT_SIZE = 0.15;

float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1,311.7))) * 43758.5453);
}
float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    float a = hash(i);
    float b = hash(i + vec2(1.0,0.0));
    float c = hash(i + vec2(0.0,1.0));
    float d = hash(i + vec2(1.0,1.0));
    return mix(mix(a,b,f.x), mix(c,d,f.x), f.y);
}
float fbm(vec2 p) {
    float v = 0.0;
    float a = 0.5;
    float f = 1.0;
    for(int i=0;i<4;i++){
        v += a * noise(p * f);
        f *= 2.0;
        a *= 0.5;
    }
    return v;
}
vec2 rotate2D(vec2 p, float angle) {
    float c = cos(angle);
    float s = sin(angle);
    return vec2(p.x * c - p.y * s, p.x * s + p.y * c);
}

float unifiedRipples(vec2 p, vec2 boatPos, float t, float speed) {
    float dist = length(p - boatPos);
    float ripple1 = sin(dist * 38.0 - t * 2.8) * 0.5 + 0.5;
    float ripple2 = sin(dist * 48.0 - t * 3.3 + 1.2) * 0.5 + 0.5;
    float ripple3 = sin(dist * 28.0 - t * 2.2 + 2.5) * 0.5 + 0.5;
    float base = ripple1 * 0.4 + ripple2 * 0.3 + ripple3 * 0.3;
    base += noise(p * 100.0 + t * 1.5) * 0.2;
    float fade = smoothstep(0.28, 0.0, dist);
    return base * fade * mix(0.5, 0.35, smoothstep(0.0, 0.5, speed));
}
float wakePattern(vec2 p, vec2 boatPos, float boatRot, float speed, float t) {
    vec2 localP = p - boatPos;
    localP = rotate2D(localP, boatRot);
    float dist = length(localP);
    float frontFade = smoothstep(0.02, -0.12, localP.x);
    float wakeAngle = abs(localP.y / (abs(localP.x) + 0.01));
    float wakeShape = smoothstep(0.6, 0.0, wakeAngle);
    float ripples = sin(dist * 25.0 - t * 5.0) * 0.3 + sin(dist * 35.0 - t * 6.5 + 1.5) * 0.2;
    ripples += noise(localP * 60.0 + t * 1.5) * 0.12;
    float foam = smoothstep(0.7, 0.85, ripples) * 0.3;
    float distanceFade = smoothstep(0.3, 0.0, dist);
    return (wakeShape * 0.3 + (ripples * 0.25 + foam * 0.3)) * distanceFade * frontFade * speed * 0.5;
}
float bowWave(vec2 p, vec2 boatPos, float boatRot, float speed, float t) {
    vec2 localP = p - boatPos;
    localP = rotate2D(localP, boatRot);
    float dist = length(localP);
    float backFade = smoothstep(-0.02, 0.12, localP.x);
    float wave = sin(dist * 30.0 - t * 8.0) * 0.5 + 0.5;
    wave += sin(dist * 40.0 - t * 10.0 + 1.5) * 0.2 + sin(abs(atan(localP.y, localP.x)) * 12.0 + t * 4.0) * 0.15;
    wave += noise(localP * 70.0 + t * 3.0) * 0.15;
    return wave * smoothstep(0.15, 0.0, dist) * backFade * 0.25 * speed;
}

vec3 posterizeColor(vec3 color, float levels) {
    return floor(color * levels) / levels;
}

void main() {
    vec2 pos = v_world_pos * 3.0;
    float swayX = sin(time * 1.2) * 0.008;
    float swayY = sin(time * 2.0) * 0.012;
    float swayRotation = sin(time * 1.5) * 0.08;
    vec2 boatPos = boatPosition + vec2(swayX, swayY);
    float boatSpeed = length(boatVelocity);

    float wave1 = fbm(pos + vec2(time * 0.2, time * 0.15));
    float wave2 = fbm(pos * 1.3 - vec2(time * 0.15, time * 0.25));
    float wave3 = fbm(pos * 1.8 + vec2(time * 0.08, -time * 0.2));
    float waves = (wave1 + wave2 * 0.6 + wave3 * 0.4) / 2.0;

    waves += unifiedRipples(v_world_pos, boatPos, time, boatSpeed);
    float wakeStrength = smoothstep(0.0, 0.2, boatSpeed) * wakeFade * 0.6;
    waves += (wakePattern(v_world_pos, boatPos, -boatRotation, boatSpeed * 3.0, time)
             + bowWave(v_world_pos, boatPos, -boatRotation, boatSpeed * 2.5, time)) * wakeStrength;

    for (int i = 0; i < numOtherPlayers; i++) {
        int idx = i * 2;
        vec2 othPos = vec2(otherBoatPositions[idx], otherBoatPositions[idx+1]);
        float othRot = otherBoatRotations[i];
        float othSpeed = otherBoatSpeeds[i];
        float phase = otherBoatSwayPhases[i];
        float amp = otherBoatSwayAmps[i];
        vec2 sway = vec2(sin(time * 1.2 + phase) * (0.008 * amp), sin(time * 2.0 + phase*1.37) * (0.012 * amp));
        vec2 othPosSway = othPos + sway;
        waves += unifiedRipples(v_world_pos, othPosSway, time, othSpeed) * 0.9;
        waves += wakePattern(v_world_pos, othPosSway, -othRot, othSpeed * 2.5, time) * 0.75;
    }

    waves = floor(waves * 6.0) / 6.0;

    vec3 deepWater = vec3(0.0, 0.35, 0.75);
    vec3 darkWater = vec3(0.05, 0.45, 0.85);
    vec3 midWater = vec3(0.15, 0.65, 0.95);
    vec3 lightWater = vec3(0.35, 0.80, 1.0);
    vec3 foamColor = vec3(1.0, 1.0, 1.0);
    vec3 waterColor;
    if (waves < 0.25) waterColor = deepWater;
    else if (waves < 0.4) waterColor = darkWater;
    else if (waves < 0.55) waterColor = midWater;
    else if (waves < 0.7) waterColor = lightWater;
    else waterColor = mix(lightWater, foamColor, (waves - 0.7) / 0.3);

    waterColor = posterizeColor(waterColor, 10.0);

    vec2 boatUV = v_world_pos - boatPos;
    boatUV = rotate2D(boatUV, -boatRotation + swayRotation);
    vec2 boatTex = (boatUV / BOAT_SIZE) + 0.5;
    if (boatTex.x >= 0.0 && boatTex.x <= 1.0 && boatTex.y >= 0.0 && boatTex.y <= 1.0) {
        vec4 bc = texture(boatTexture, boatTex);
        if (bc.a > 0.05) waterColor = mix(waterColor, bc.rgb, bc.a);
    }

    for (int i = 0; i < numOtherPlayers; i++) {
        int idx = i * 2;
        vec2 othPos = vec2(otherBoatPositions[idx], otherBoatPositions[idx+1]);
        float othRot = otherBoatRotations[i];
        float phase = otherBoatSwayPhases[i];
        float amp = otherBoatSwayAmps[i];
        vec2 sway = vec2(sin(time * 1.2 + phase) * (0.008 * amp), sin(time * 2.0 + phase*1.37) * (0.012 * amp));
        vec2 othPosSway = othPos + sway;
        vec2 othUV = v_world_pos - othPosSway;
        othUV = rotate2D(othUV, -othRot);
        vec2 othTex = (othUV / BOAT_SIZE) + 0.5;
        if (othTex.x >= 0.0 && othTex.x <= 1.0 && othTex.y >= 0.0 && othTex.y <= 1.0) {
            vec4 oc = texture(boatTexture, othTex);
            if (oc.a > 0.05) {
                vec3 tint = vec3(1.05, 0.95, 0.95);
                waterColor = mix(waterColor, oc.rgb * tint, oc.a * 0.75);
            }
        }
    }

    fragColor = vec4(waterColor, 1.0);
}
'''