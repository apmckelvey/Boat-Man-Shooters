import moderngl
import numpy as np
import pygame
import moderngl
import numpy as np
import pygame
import pygame.freetype
import os

vertex_shader = '''
#version 330 core

in vec2 in_vert;
out vec2 v_uv;
out vec2 v_world_pos;

uniform vec2 viewportSize;
uniform vec2 cameraPos;

void main() {
    v_uv = in_vert * 0.5 + 0.5;
    v_world_pos = in_vert * viewportSize * 0.5 + cameraPos;
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
uniform sampler2D enemyTexture;
uniform int numOtherPlayers;
uniform float otherBoatPositions[20];
uniform float otherBoatRotations[10];
uniform float otherBoatSpeeds[10];
uniform float otherBoatSwayPhases[10];
uniform float otherBoatSwayAmps[10];
uniform vec2 worldSize;
uniform float boatAspect;

in vec2 v_uv;
in vec2 v_world_pos;
out vec4 fragColor;

const float BOAT_SIZE = 0.15;
const float BORDER_WIDTH = 0.3;
const float BORDER_FADE = 0.5;

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
    for(int i=0;i<6;i++){
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

// Calculate distance from world boundaries
float getDistanceFromBoundary(vec2 pos, vec2 worldSize) {
    float distLeft = pos.x;
    float distRight = worldSize.x - pos.x;
    float distBottom = pos.y;
    float distTop = worldSize.y - pos.y;
    return min(min(distLeft, distRight), min(distBottom, distTop));
}

// Enhanced ripple system with more frequency variation
float unifiedRipples(vec2 p, vec2 boatPos, float t, float speed) {
    float dist = length(p - boatPos);
    float ripple1 = sin(dist * 38.0 - t * 2.8) * 0.5 + 0.5;
    float ripple2 = sin(dist * 48.0 - t * 3.3 + 1.2) * 0.5 + 0.5;
    float ripple3 = sin(dist * 28.0 - t * 2.2 + 2.5) * 0.5 + 0.5;
    float ripple4 = sin(dist * 58.0 - t * 4.1 + 3.7) * 0.5 + 0.5;
    float base = ripple1 * 0.35 + ripple2 * 0.25 + ripple3 * 0.25 + ripple4 * 0.15;
    base += noise(p * 100.0 + t * 1.5) * 0.15;
    base += noise(p * 200.0 + t * 2.0) * 0.08;
    float fade = smoothstep(0.28, 0.0, dist);
    return base * fade * mix(0.5, 0.35, smoothstep(0.0, 0.5, speed));
}

// Improved wake with better foam generation
float wakePattern(vec2 p, vec2 boatPos, float boatRot, float speed, float t) {
    vec2 localP = p - boatPos;
    localP = rotate2D(localP, boatRot);
    float dist = length(localP);
    float frontFade = smoothstep(0.02, -0.12, localP.x);
    float wakeAngle = abs(localP.y / (abs(localP.x) + 0.01));
    float wakeShape = smoothstep(0.6, 0.0, wakeAngle);

    float ripples = sin(dist * 25.0 - t * 5.0) * 0.3;
    ripples += sin(dist * 35.0 - t * 6.5 + 1.5) * 0.2;
    ripples += sin(dist * 45.0 - t * 7.0 + 3.0) * 0.15;
    ripples += noise(localP * 60.0 + t * 1.5) * 0.12;
    ripples += noise(localP * 120.0 + t * 2.5) * 0.08;

    float foam = smoothstep(0.65, 0.9, ripples) * 0.4;
    float turbulence = fbm(localP * 80.0 + t * 2.0) * 0.2;
    foam += smoothstep(0.7, 0.95, turbulence) * 0.25;

    float distanceFade = smoothstep(0.3, 0.0, dist);
    return (wakeShape * 0.35 + (ripples * 0.3 + foam * 0.4)) * distanceFade * frontFade * speed * 0.5;
}

// Enhanced bow wave with more detail
float bowWave(vec2 p, vec2 boatPos, float boatRot, float speed, float t) {
    vec2 localP = p - boatPos;
    localP = rotate2D(localP, boatRot);
    float dist = length(localP);
    float backFade = smoothstep(-0.02, 0.12, localP.x);

    float wave = sin(dist * 30.0 - t * 8.0) * 0.5 + 0.5;
    wave += sin(dist * 40.0 - t * 10.0 + 1.5) * 0.2;
    wave += sin(dist * 50.0 - t * 12.0 + 2.5) * 0.15;
    wave += sin(abs(atan(localP.y, localP.x)) * 12.0 + t * 4.0) * 0.15;

    wave += noise(localP * 70.0 + t * 3.0) * 0.15;
    wave += noise(localP * 140.0 + t * 4.0) * 0.08;

    return wave * smoothstep(0.15, 0.0, dist) * backFade * 0.3 * speed;
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

    // Enhanced multi-layer wave system with more detail
    float wave1 = fbm(pos + vec2(time * 0.2, time * 0.15));
    float wave2 = fbm(pos * 1.3 - vec2(time * 0.15, time * 0.25));
    float wave3 = fbm(pos * 1.8 + vec2(time * 0.08, -time * 0.2));
    float wave4 = fbm(pos * 2.5 + vec2(time * 0.12, time * 0.18));
    float wave5 = fbm(pos * 3.2 - vec2(time * 0.1, -time * 0.15));

    float waves = (wave1 + wave2 * 0.6 + wave3 * 0.4 + wave4 * 0.3 + wave5 * 0.2) / 2.5;

    // Add subtle caustics effect
    float caustics = sin(pos.x * 10.0 + time * 1.5) * sin(pos.y * 10.0 + time * 1.8);
    caustics += sin(pos.x * 15.0 - time * 2.0) * sin(pos.y * 15.0 + time * 2.2);
    waves += caustics * 0.03;

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

    // Apply subtle posterization to define wave edges better
    waves = floor(waves * 16.0) / 16.0;

    // Realistic water colors with better definition
    vec3 deepWater = vec3(0.02, 0.18, 0.35);
    vec3 darkWater = vec3(0.06, 0.32, 0.52);
    vec3 midWater = vec3(0.14, 0.50, 0.68);
    vec3 lightWater = vec3(0.28, 0.68, 0.82);
    vec3 brightWater = vec3(0.48, 0.82, 0.92);
    vec3 foamColor = vec3(0.92, 0.96, 0.98);

    // Smooth blending between water colors
    vec3 waterColor;
    if (waves < 0.15) {
        waterColor = mix(deepWater, darkWater, waves / 0.15);
    } else if (waves < 0.35) {
        waterColor = mix(darkWater, midWater, (waves - 0.15) / 0.20);
    } else if (waves < 0.55) {
        waterColor = mix(midWater, lightWater, (waves - 0.35) / 0.20);
    } else if (waves < 0.75) {
        waterColor = mix(lightWater, brightWater, (waves - 0.55) / 0.20);
    } else {
        waterColor = mix(brightWater, foamColor, (waves - 0.75) / 0.25);
    }

    // Subtle color posterization for definition without harshness
    waterColor = posterizeColor(waterColor, 32.0);

    // Add depth variation based on wave height
    float depthModulation = fbm(v_world_pos * 5.0 + time * 0.05) * 0.12;
    waterColor = mix(waterColor, deepWater, depthModulation * 0.25);

    // Add specular highlights for realism
    float specular = pow(max(0.0, waves - 0.65), 4.0) * 0.35;
    waterColor += vec3(specular);

    // Add boundary visualization
    float distFromBoundary = getDistanceFromBoundary(v_world_pos, worldSize);
    
    if (distFromBoundary < BORDER_WIDTH) {
        float borderIntensity = smoothstep(BORDER_WIDTH, 0.0, distFromBoundary);
        float pulse = sin(time * 3.0) * 0.3 + 0.7;
        vec3 boundaryColor = vec3(0.8, 0.15, 0.1);
        vec3 warningColor = vec3(0.9, 0.4, 0.2);
        vec3 edgeColor = mix(warningColor, boundaryColor, borderIntensity);
        waterColor = mix(waterColor, edgeColor, borderIntensity * 0.6 * pulse);
        
        if (distFromBoundary < BORDER_WIDTH * 0.5) {
            float stripePattern = step(0.5, fract(distFromBoundary * 15.0 + time * 2.0));
            waterColor = mix(waterColor, vec3(1.0, 0.2, 0.1), stripePattern * borderIntensity * 0.4);
        }
    }
    
    if (distFromBoundary < BORDER_WIDTH + BORDER_FADE) {
        float fadeIntensity = smoothstep(BORDER_WIDTH + BORDER_FADE, BORDER_WIDTH, distFromBoundary);
        waterColor = mix(waterColor, vec3(0.9, 0.4, 0.2) * 0.6, fadeIntensity * 0.2);
    }

    vec2 boatUV = v_world_pos - boatPos;
    boatUV = rotate2D(boatUV, -boatRotation + swayRotation);
    vec2 boatTex = vec2(boatUV.x / (BOAT_SIZE * boatAspect), boatUV.y / BOAT_SIZE) + 0.5;
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
        vec2 othTex = vec2(othUV.x / (BOAT_SIZE * boatAspect), othUV.y / BOAT_SIZE) + 0.5;
        if (othTex.x >= 0.0 && othTex.x <= 1.0 && othTex.y >= 0.0 && othTex.y <= 1.0) {
            // sample enemy texture for other boats and composite fully opaque (no transparency)
            vec4 oc = texture(enemyTexture, othTex);
            // only apply if there's visible texel (alpha > small threshold)
            if (oc.a > 0.05) {
                vec3 tint = vec3(1.0, 1.0, 1.0);
                // replace water color with boat color where boat is present
                waterColor = mix(waterColor, oc.rgb * tint, 1.0);
            }
        }
    }

    fragColor = vec4(waterColor, 1.0);
}
'''


class Renderer:
    def __init__(self, ctx):
        self.ctx = ctx
        #changed aspect ratio to make map bigger - seems like a good size???
        self.viewport_width = 2.3
        self.viewport_height = 1.3

        self._load_boat_texture()
        self._compile_shaders()
        self._create_geometry()
        # overlay resources (for UI text rendered via pygame -> GL texture)
        self._create_overlay_resources()
    def world_to_screen(self, world_x, world_y, camera_x, camera_y, screen_width, screen_height):
        rel_x = world_x - camera_x
        rel_y = world_y - camera_y
        #conver to screen space
        screen_x = (rel_x / self.viewport_width) * screen_width + screen_width / 2.0
        screen_y = screen_height / 2 - (rel_y / self.viewport_height) * screen_height

        return screen_x, screen_y
    def _load_boat_texture(self):
        try:
            boat_image = pygame.image.load("../Graphics/Sprites/Boats/player.png").convert_alpha()
            self.boat_width, self.boat_height = boat_image.get_size()
            self.boat_aspect = float(self.boat_width) / float(self.boat_height) if self.boat_height else 1.0
            boat_data = pygame.image.tobytes(boat_image, "RGBA", True)
            print(f"Loaded boat.png ({self.boat_width}x{self.boat_height}), aspect={self.boat_aspect:.3f}")
        except Exception:
            print("boat.png not found — creating placeholder")
            self.boat_width, self.boat_height = 64, 64
            self.boat_aspect = 1.0
            surf = pygame.Surface((self.boat_width, self.boat_height), pygame.SRCALPHA)
            pygame.draw.polygon(surf, (139, 69, 19), [(50, 32), (10, 20), (10, 44)])
            pygame.draw.circle(surf, (255, 255, 255), (35, 32), 8)
            boat_data = pygame.image.tobytes(surf, "RGBA", True)

        self.boat_texture = self.ctx.texture((self.boat_width, self.boat_height), 4, boat_data)
        self.boat_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)

        # load enemy texture (used for other players)
        try:
            enemy_image = pygame.image.load("../Graphics/Sprites/Boats/enemy.png").convert_alpha()
            ew, eh = enemy_image.get_size()
            enemy_data = pygame.image.tobytes(enemy_image, "RGBA", True)
            self.enemy_width, self.enemy_height = ew, eh
            self.enemy_aspect = float(ew) / float(eh) if eh else 1.0
        except Exception:
            # fallback to boat texture if enemy not found
            enemy_data = boat_data
            self.enemy_width, self.enemy_height = self.boat_width, self.boat_height
            self.enemy_aspect = getattr(self, 'boat_aspect', 1.0)

        self.enemy_texture = self.ctx.texture((self.enemy_width, self.enemy_height), 4, enemy_data)
        self.enemy_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)

    def _compile_shaders(self):
        self.program = self.ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)
        # bind textures: player boat -> unit 0, enemy boat -> unit 1
        self.boat_texture.use(location=0)
        self.enemy_texture.use(location=1)
        self.program['boatTexture'].value = 0
        try:
            self.program['enemyTexture'].value = 1
        except Exception:
            pass
        # Pass boat aspect ratio to shader to avoid width distortion
        try:
            self.program['boatAspect'].value = float(getattr(self, 'boat_aspect', 1.0))
        except Exception:
            pass
        try:
            self.program['enemyAspect'].value = float(getattr(self, 'enemy_aspect', 1.0))
        except Exception:
            pass

    def _create_geometry(self):
        vertices = np.array([-1.0, -1.0, 1.0, -1.0, -1.0, 1.0, 1.0, 1.0], dtype='f4')
        vbo = self.ctx.buffer(vertices.tobytes())
        self.vao = self.ctx.simple_vertex_array(self.program, vbo, 'in_vert')

    def _create_overlay_resources(self):
        # simple textured quad program for overlays
        overlay_vertex = '''
#version 330 core
in vec2 in_vert;
out vec2 v_uv;
void main() {
    v_uv = in_vert * 0.5 + 0.5;
    gl_Position = vec4(in_vert, 0.0, 1.0);
}
'''

        overlay_fragment = '''
#version 330 core
precision highp float;
in vec2 v_uv;
out vec4 fragColor;
uniform sampler2D overlayTexture;
void main() {
    vec4 c = texture(overlayTexture, v_uv);
    fragColor = c;
}
'''

        try:
            self.overlay_program = self.ctx.program(vertex_shader=overlay_vertex, fragment_shader=overlay_fragment)
            # reuse same full-screen vbo as the main pass
            # create a simple vao for overlay
            vertices = np.array([-1.0, -1.0, 1.0, -1.0, -1.0, 1.0, 1.0, 1.0], dtype='f4')
            vbo = self.ctx.buffer(vertices.tobytes())
            self.overlay_vao = self.ctx.simple_vertex_array(self.overlay_program, vbo, 'in_vert')
        except Exception:
            self.overlay_program = None
            self.overlay_vao = None

        self.overlay_texture = None
        # initialize pygame freetype for rendering text to surface
        try:
            pygame.freetype.init()
            # Try a bundled TTF first (so DynaPuff looks identical across platforms if provided)
            font_paths = [
                # project-specific path you mentioned
                os.path.join(os.path.dirname(__file__), "..", "Assets", "DynaPuff Font", "DynaPuffFont.ttf"),
                os.path.join(os.path.dirname(__file__), "..", "DynaPuffFont.ttf"),
                os.path.join(os.getcwd(), "Assets", "DynaPuff Font", "DynaPuffFont.ttf"),
                os.path.join(os.getcwd(), "DynaPuffFont.ttf"),
            ]

            found_ttf = None
            for p in font_paths:
                try:
                    if os.path.exists(p):
                        found_ttf = p
                        break
                except Exception:
                    continue

            if found_ttf:
                try:
                    self.overlay_font_large = pygame.freetype.Font(found_ttf, 63)
                    self.overlay_font_small = pygame.freetype.Font(found_ttf, 27)
                    self.nametag_font = pygame.freetype.Font(found_ttf, 18)
                except Exception:
                    # fallback to SysFont lookup
                    self.overlay_font_large = pygame.freetype.SysFont("DynaPuff", 63)
                    self.overlay_font_small = pygame.freetype.SysFont("DynaPuff", 27)
                    self.nametag_font = pygame.freetype.SysFont("DynaPuff", 18)
            else:
                # Prefer DynaPuff via system font name, fallback to default
                try:
                    self.overlay_font_large = pygame.freetype.SysFont("DynaPuff", 63)
                    self.overlay_font_small = pygame.freetype.SysFont("DynaPuff", 27)
                    self.nametag_font = pygame.freetype.SysFont("DynaPuff", 18)
                except Exception:
                    self.overlay_font_large = pygame.freetype.SysFont(None, 63)
                    self.overlay_font_small = pygame.freetype.SysFont(None, 27)
                    self.nametag_font = pygame.freetype.SysFont(None, 18)
        except Exception:
            self.overlay_font_large = None
            self.overlay_font_small = None
            self.nametag_font = None

    def render(self, time, player, other_players_display):
        from config import WORLD_WIDTH, WORLD_HEIGHT
        
        self.program['time'].value = float(time)
        self.program['boatPosition'].value = (float(player.x), float(player.y))
        self.program['boatRotation'].value = float(player.rotation)
        self.program['boatVelocity'].value = (float(player.velocity_x), float(player.velocity_y))
        self.program['wakeFade'].value = float(player.wake_fade)
        self.program['cameraPos'].value = (float(player.camera_x), float(player.camera_y))
        self.program['viewportSize'].value = (float(self.viewport_width), float(self.viewport_height))
        self.program['worldSize'].value = (float(WORLD_WIDTH), float(WORLD_HEIGHT))


        display_list = list(other_players_display.values())[:10]
        num_other = len(display_list)
        self.program['numOtherPlayers'].value = num_other

        pos_array = np.zeros(20, dtype='f4')
        rot_array = np.zeros(10, dtype='f4')
        speed_array = np.zeros(10, dtype='f4')
        sway_phase_array = np.zeros(10, dtype='f4')
        sway_amp_array = np.zeros(10, dtype='f4')

        for idx, e in enumerate(display_list):
            pos_array[idx * 2 + 0] = float(e['x'])
            pos_array[idx * 2 + 1] = float(e['y'])
            rot_array[idx] = float(e['rot'])
            speed_array[idx] = float(max(0.0, min(2.5, e.get('speed', 0.0))))
            sway_phase_array[idx] = float(e.get('sway_phase', 0.0))
            sway_amp_array[idx] = float(e.get('sway_amp', 1.0))

        try:
            self.program.get("otherBoatPositions").write(pos_array.tobytes())
            self.program.get("otherBoatRotations").write(rot_array.tobytes())
            self.program.get("otherBoatSpeeds").write(speed_array.tobytes())
            self.program.get("otherBoatSwayPhases").write(sway_phase_array.tobytes())
            self.program.get("otherBoatSwayAmps").write(sway_amp_array.tobytes())
        except Exception:
            try:
                self.program['otherBoatPositions'].value = tuple(pos_array.tolist())
                self.program['otherBoatRotations'].value = tuple(rot_array.tolist())
                self.program['otherBoatSpeeds'].value = tuple(speed_array.tolist())
                self.program['otherBoatSwayPhases'].value = tuple(sway_phase_array.tolist())
                self.program['otherBoatSwayAmps'].value = tuple(sway_amp_array.tolist())
            except Exception:
                pass

        self.ctx.clear(0.0, 0.35, 0.75)
        self.vao.render(mode=moderngl.TRIANGLE_STRIP)

    def draw_overlay(self, main_text: str, sub_text: str = "", alpha: float = 1.0):
        """Render a fullscreen overlay by drawing text into a pygame surface,
        uploading it as a texture and drawing a textured quad on top of the scene.
        """
        # ensure overlay program exists
        if not getattr(self, 'overlay_program', None) or not getattr(self, 'overlay_vao', None):
            return

        # import sizes from config
        try:
            from config import WIDTH, HEIGHT
        except Exception:
            WIDTH, HEIGHT = 1280, 720

        # create an RGBA surface
        surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA, 32)
        surf = surf.convert_alpha()

        # draw semi-transparent dark background
        bg = (0, 0, 0, int(180 * alpha))
        surf.fill(bg)

        # render text
        if self.overlay_font_large:
            # center main text
            text_surf, _ = self.overlay_font_large.render(main_text, (255, 50, 50))
            tw, th = text_surf.get_size()
            surf.blit(text_surf, text_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

        if sub_text and self.overlay_font_small:
            sub_surf, _ = self.overlay_font_small.render(sub_text, (230, 230, 230))
            surf.blit(sub_surf, sub_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70)))

        # upload to GPU as texture
        data = pygame.image.tostring(surf, 'RGBA', True)
        w, h = surf.get_size()

        # create or write texture
        try:
            if self.overlay_texture is None:
                self.overlay_texture = self.ctx.texture((w, h), 4, data)
                self.overlay_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            else:
                # update existing texture
                try:
                    self.overlay_texture.write(data)
                except Exception:
                    # fallback to recreate
                    self.overlay_texture.release()
                    self.overlay_texture = self.ctx.texture((w, h), 4, data)
                    self.overlay_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)

            self.overlay_texture.use(location=2)
            try:
                self.overlay_program['overlayTexture'].value = 2
            except Exception:
                pass

            # enable blending and draw overlay quad
            self.ctx.enable(moderngl.BLEND)
            self.overlay_vao.render(mode=moderngl.TRIANGLE_STRIP)
            # leaving blending state as-is
        except Exception:
            return

    def draw_sprint_bar(self, player):
        """Draw a sprint energy bar in the corner of the screen"""
        try:
            from config import WIDTH, HEIGHT
        except Exception:
            WIDTH, HEIGHT = 1280, 720

        # create transparent surface
        surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA, 32)
        surf = surf.convert_alpha()

        # sprint bar dimensions and position
        bar_width = 200
        bar_height = 20
        x = WIDTH - bar_width - 20  # 20px from right edge
        y = HEIGHT - bar_height - 20  # 20px from bottom

        # Draw background (empty bar)
        pygame.draw.rect(surf, (255, 0, 0, 180), (x, y, bar_width, bar_height))
        
        # Draw foreground (sprint energy)
        current_width = (player.sprint / 100.0) * bar_width
        if current_width > 0:
            pygame.draw.rect(surf, (0, 255, 0, 180), (x, y, current_width, bar_height))

        # Add border for better visibility
        pygame.draw.rect(surf, (255, 255, 255, 100), (x, y, bar_width, bar_height), 2)

        # Optional: Add "SPRINT" label
        if self.nametag_font:
            try:
                label_surf, _ = self.nametag_font.render("SPRINT", (255, 255, 255))
                label_rect = label_surf.get_rect(bottomright=(x - 10, y + bar_height))
                surf.blit(label_surf, label_rect)
            except Exception:
                pass

        # Upload to GPU and render
        data = pygame.image.tostring(surf, 'RGBA', True)
        w, h = surf.get_size()

        try:
            if self.overlay_texture is None:
                self.overlay_texture = self.ctx.texture((w, h), 4, data)
                self.overlay_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            else:
                try:
                    self.overlay_texture.write(data)
                except Exception:
                    self.overlay_texture.release()
                    self.overlay_texture = self.ctx.texture((w, h), 4, data)
                    self.overlay_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)

            self.overlay_texture.use(location=2)
            try:
                self.overlay_program['overlayTexture'].value = 2
            except Exception:
                pass

            self.ctx.enable(moderngl.BLEND)
            self.overlay_vao.render(mode=moderngl.TRIANGLE_STRIP)
        except Exception:
            return

    def draw_player_nametags(self, player, other_players_display, names=None, y_offset=75):
        try:
            from config import WIDTH, HEIGHT
        except Exception:
            WIDTH, HEIGHT = 1280, 720

        # create transparent surface
        surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA, 32)
        surf = surf.convert_alpha()

        # helper to draw a nametag (text only) above screen position
        def draw_nametag(screen_x, screen_y, text=None):
            if not text:
                return
            font = getattr(self, 'nametag_font', None) or self.overlay_font_small
            if not font:
                return
            # position slightly higher
            pos = (int(screen_x), int(screen_y - y_offset))
            # draw shadow for readability
            try:
                shadow_surf, _ = font.render(text, (0, 0, 0))
                surf.blit(shadow_surf, shadow_surf.get_rect(center=(pos[0] + 1, pos[1] + 1)))
            except Exception:
                pass
            # draw main text in white
            try:
                txt_surf, _ = font.render(text, (255, 255, 255))
                surf.blit(txt_surf, txt_surf.get_rect(center=pos))
            except Exception:
                pass

        # draw for local player
        try:
            sx, sy = self.world_to_screen(player.x, player.y, player.camera_x, player.camera_y, WIDTH, HEIGHT)
            # local player label: if names dict provided and contains a special key 'local', use it
            local_label = None
            if isinstance(names, dict):
                local_label = names.get('local')
            draw_nametag(sx, sy, local_label or "You")
        except Exception:
            pass

        # draw for other players
        for pid, p in other_players_display.items():
            try:
                sx, sy = self.world_to_screen(p['x'], p['y'], player.camera_x, player.camera_y, WIDTH, HEIGHT)
                label = None
                if isinstance(names, dict):
                    label = names.get(pid)
                draw_nametag(sx, sy, label)
            except Exception:
                continue

        # upload to GPU as texture and render on top (reuse overlay texture logic)
        data = pygame.image.tostring(surf, 'RGBA', True)
        w, h = surf.get_size()

        try:
            if self.overlay_texture is None:
                self.overlay_texture = self.ctx.texture((w, h), 4, data)
                self.overlay_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            else:
                try:
                    self.overlay_texture.write(data)
                except Exception:
                    self.overlay_texture.release()
                    self.overlay_texture = self.ctx.texture((w, h), 4, data)
                    self.overlay_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)

            self.overlay_texture.use(location=2)
            try:
                self.overlay_program['overlayTexture'].value = 2
            except Exception:
                pass

            self.ctx.enable(moderngl.BLEND)
            self.overlay_vao.render(mode=moderngl.TRIANGLE_STRIP)
        except Exception:
            return
