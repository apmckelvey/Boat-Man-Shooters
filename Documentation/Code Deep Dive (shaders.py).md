# Code Deep Dive `shaders.py`

The `vertex_shader` string is defined here, which is written using `OpenGL Shading Language` (GLSL).
```Python
vertex_shader = '''
OpenGl Code in Here...
'''
```

The `vertex_shader` OpenGL code starts by telling OpenGL to use `OpenGL Shading Language version` 3.30 (`#version 330`) and declaring a few variables: `in_vert`, `v_uv`, `v_world_pos`, `cameraPos`, and `viewportSize`.
- `in_vert` is the input vertex position
- `v_uv` is the output UV coordinate (mapped from `[-1, 1]` into `[0, 1]`)
  - A UV coordinate is just a 2D coordinate that tells the shader where you are on a texture.
- `v_world_pos` is the output world-space position for each vertex
- `cameraPos` is the camera position in the world
- `viewportSize` is how wide and tall the visible area is in world units. In `main()`, the shader computes `v_uv` and `v_world_pos` using these values, then sets `gl_Position` so the quad covers the screen.

```GLSL
#version 330
in vec2 in_vert;
out vec2 v_uv;
out vec2 v_world_pos;
uniform vec2 cameraPos;
uniform vec2 viewportSize;
```

In `main()`, the shader computes `v_uv` and `v_world_pos` using these values, then sets `gl_Position` so the quad covers the screen. A quad is a flat rectangle made from two triangles; graphics APIs including OpenGL generally only draw triangles, so you have to draw a quad using two triangles.
```GLSL
void main() {
    v_uv = in_vert * 0.5 + 0.5;
    v_world_pos = cameraPos + (in_vert * viewportSize * 0.5);
    gl_Position = vec4(in_vert, 0.0, 1.0);
}
```

Then the next shader defined is the `fragment_shader`, which is written, again, using `OpenGL Shading Language` (GLSL).
```Python
fragment_shader = '''
OpenGl Code in Here...
'''
```

It starts by defining key variables:
- `time` is the current time in seconds
- `boatPosition` is the position of the boat in world units
- `boatRotation` is the rotation of the boat in radians
- `boatVelocity` is the velocity of the boat in world units per second
- `wakeFade` is a value between 0 and 1 that determines how much the boat's wake pattern should fade out
- `boatTexture` is the texture that the boat is using
- `numOtherPlayers` is the number of other players in the game
- `otherBoatPositions` is an array of the positions of all other players in world units
- `otherBoatRotations` is an array of the rotations of all other players in radians
- `otherBoatSpeeds` is an array of the speeds of all other players in world units per second`
- `otherBoatSwayPhases` is an array of the phases of all other players' sway animations
- `otherBoatSwayAmps` is an array of the amplitudes of all other players' sway animations
- `v_uv` is the UV coordinate of the current fragment
- `v_world_pos` is the world position of the current fragment
- `fragColor` is the output color of the fragment
- `BOAT_SIZE` is the size of the boat texture in world units
```GLSL
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
```

The shader then defines a helper function, `hash()`, which returns a random number between 0 and 1 based on the input vector, `vec2`.
```GLSL
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1,311.7))) * 43758.5453);
}
```

Another helper function called `noise()` is defined, which uses `hash()` to generate a smooth noise function. Instead of returning completely random values at each point, it interpolates between nearby `hash()` values so that the output changes gradually as the input `vec2` moves, creating a continuous, “blobby” noise pattern that is useful for natural-looking effects for the waves.
```GLSL
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
```


```GLSL
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
```

```GLSL
vec2 rotate2D(vec2 p, float angle) {
    float c = cos(angle);
    float s = sin(angle);
    return vec2(p.x * c - p.y * s, p.x * s + p.y * c);
}
```

```GLSL
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
```

```GLSL
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
```

```GLSL
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
```

```GLSL
vec3 posterizeColor(vec3 color, float levels) {
    return floor(color * levels) / levels;
}
```

```GLSL
void main() {
    vec2 pos = v_world_pos * 3.0;
    float swayX = sin(time * 1.2) * 0.008;
    float swayY = sin(time * 2.0) * 0.012;
    float swayRotation = sin(time * 1.5) * 0.08;
    vec2 boatPos = boatPosition + vec2(swayX, swayY);
    float boatSpeed = length(boatVelocity);
```

```GLSL
    float wave1 = fbm(pos + vec2(time * 0.2, time * 0.15));
    float wave2 = fbm(pos * 1.3 - vec2(time * 0.15, time * 0.25));
    float wave3 = fbm(pos * 1.8 + vec2(time * 0.08, -time * 0.2));
    float waves = (wave1 + wave2 * 0.6 + wave3 * 0.4) / 2.0;
```

```GLSL
    waves += unifiedRipples(v_world_pos, boatPos, time, boatSpeed);
    float wakeStrength = smoothstep(0.0, 0.2, boatSpeed) * wakeFade * 0.6;
    waves += (wakePattern(v_world_pos, boatPos, -boatRotation, boatSpeed * 3.0, time)
             + bowWave(v_world_pos, boatPos, -boatRotation, boatSpeed * 2.5, time)) * wakeStrength;
```

```GLSL
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
```

```GLSL
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
```

```GLSL
    vec2 boatUV = v_world_pos - boatPos;
    boatUV = rotate2D(boatUV, -boatRotation + swayRotation);
    vec2 boatTex = (boatUV / BOAT_SIZE) + 0.5;
    if (boatTex.x >= 0.0 && boatTex.x <= 1.0 && boatTex.y >= 0.0 && boatTex.y <= 1.0) {
        vec4 bc = texture(boatTexture, boatTex);
        if (bc.a > 0.05) waterColor = mix(waterColor, bc.rgb, bc.a);
    }
```

```GLSL
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
```