import pygame
import moderngl
import numpy as np
import asyncio
import math
import time
import uuid
from threading import Thread
from supabase import create_client, Client

# ------------------------
# CONFIG
# -------------------------
WIDTH, HEIGHT = 1280, 720
INTERP_DELAY = 0.15
MAX_HISTORY = 15
FETCH_INTERVAL = 0.08
SEND_INTERVAL = 0.10
VISIBLE_RADIUS = 10.0
TARGET_FPS = 60

# Prediction parameters
VELOCITY_CORRECTION_SPEED = 0.15  # How fast to correct velocity errors
POSITION_CORRECTION_SPEED = 0.08  # Gentle position correction to prevent drift
ROTATION_CORRECTION_SPEED = 0.12  # Rotation correction speed
MAX_POSITION_ERROR = 0.5  # Max position error before stronger correction

SUPABASE_URL = "https://ciuqcdaowlwztlzkanpq.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNpdXFjZGFvd2x3enRsemthbnBxIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE5MTYxMjUsImV4cCI6MjA3NzQ5MjEyNX0.WdoFmiZTRZbkTlnNISPTbkcDTFWDv75QEFsKNs7zkeY"

# -------------------------
# INIT
# -------------------------
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
pygame.display.set_caption("Predictive Water Demo")
clock = pygame.time.Clock()

ctx = moderngl.create_context()
print("OpenGL context created")

# -------------------------
# Supabase
# -------------------------
supabase = None
try:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    print("✓ Connected to Supabase")
except Exception as e:
    print("✗ Supabase disabled:", e)
    supabase = None

# -------------------------
# Player state
# -------------------------
PLAYER_ID = str(uuid.uuid4())
PLAYER_NAME = f"Player_{PLAYER_ID[:8]}"

WORLD_WIDTH = 30.0
WORLD_HEIGHT = 30.0

boat_x = 15.0
boat_y = 15.0
boat_rotation = 0.0
boat_target_rotation = 0.0

boat_speed = 0.3
boat_backward_speed = 0.08
rotation_speed = 2.5
rotation_smoothing = 0.15

boat_current_velocity = 0.0
boat_target_velocity = 0.0
acceleration = 3.0
deceleration = 4.0

boat_velocity_x = 0.0
boat_velocity_y = 0.0
wake_fade = 0.0

camera_x = 15.0
camera_y = 15.0
camera_smoothing = 0.12
viewport_width = 1.0
viewport_height = 1.0

network_running = True

# Predictive player tracking
# other_players: { pid: {
#   "state": {x, y, rot, vx, vy, vrot},  # Current predicted state
#   "target": {x, y, rot, vx, vy, vrot}, # Target from network
#   "history": [...]
# }}
other_players = {}
other_players_display = {}

# -------------------------
# Boat texture
# -------------------------
try:
    boat_image = pygame.image.load("boat.png").convert_alpha()
    boat_width, boat_height = boat_image.get_size()
    boat_data = pygame.image.tobytes(boat_image, "RGBA", True)
    print(f"Loaded boat.png ({boat_width}x{boat_height})")
except Exception as e:
    print("boat.png not found — creating placeholder")
    boat_width, boat_height = 64, 64
    surf = pygame.Surface((boat_width, boat_height), pygame.SRCALPHA)
    pygame.draw.polygon(surf, (139, 69, 19), [(50, 32), (10, 20), (10, 44)])
    pygame.draw.circle(surf, (255, 255, 255), (35, 32), 8)
    boat_data = pygame.image.tobytes(surf, "RGBA", True)

# -------------------------
# GLSL
# -------------------------
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

# -------------------------
# Build program
# -------------------------
program = ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)
boat_texture = ctx.texture((boat_width, boat_height), 4, boat_data)
boat_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
boat_texture.use(location=0)
program['boatTexture'].value = 0

vertices = np.array([-1.0, -1.0, 1.0, -1.0, -1.0, 1.0, 1.0, 1.0], dtype='f4')
vbo = ctx.buffer(vertices.tobytes())
vao = ctx.simple_vertex_array(program, vbo, 'in_vert')


# -------------------------
# Helpers
# -------------------------
def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def lerp_angle(a: float, b: float, t: float) -> float:
    diff = (b - a) % (2 * math.pi)
    if diff > math.pi:
        diff -= 2 * math.pi
    return a + diff * t


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    if edge0 == edge1:
        return 0.0
    t = max(0.0, min(1.0, (x - edge0) / (edge1 - edge0)))
    return t * t * (3.0 - 2.0 * t)


def small_hash_to_phase_amp(s: str):
    h = 0
    for ch in s:
        h = (h * 31 + ord(ch)) & 0xffffffff
    phase = float((h % 1000)) / 1000.0 * math.pi * 2.0
    amp = 0.7 + ((h >> 10) % 50) / 100.0
    return phase, amp


# -------------------------
# Network Thread
# -------------------------
def network_loop():
    global other_players, network_running
    if not supabase:
        return
    last_send = 0.0
    last_fetch = 0.0
    while network_running:
        try:
            now = time.time()
            if now - last_send >= SEND_INTERVAL:
                data = {
                    "player_id": PLAYER_ID,
                    "player_name": PLAYER_NAME,
                    "x": float(boat_x),
                    "y": float(boat_y),
                    "rotation": float(boat_rotation),
                    "updated_at": float(now)
                }
                supabase.table("players").upsert(data, on_conflict="player_id").execute()
                last_send = now

            if now - last_fetch >= FETCH_INTERVAL:
                cutoff = now - 10.0
                resp = supabase.table("players").select("*").gt("updated_at", cutoff).execute()
                rows = getattr(resp, "data", None) or resp

                for player in rows:
                    try:
                        pid = player.get("player_id")
                        if not pid or pid == PLAYER_ID:
                            continue
                        px = float(player.get("x", 0.0))
                        py = float(player.get("y", 0.0))
                        prot = float(player.get("rotation", 0.0))
                        ts = float(player.get("updated_at", time.time()))

                        dx = px - boat_x
                        dy = py - boat_y
                        dist = math.hypot(dx, dy)
                        if dist <= VISIBLE_RADIUS:
                            if pid not in other_players:
                                # Initialize with network position and zero velocity
                                other_players[pid] = {
                                    "state": {"x": px, "y": py, "rot": prot, "vx": 0.0, "vy": 0.0, "vrot": 0.0},
                                    "target": {"x": px, "y": py, "rot": prot, "vx": 0.0, "vy": 0.0, "vrot": 0.0},
                                    "history": []
                                }

                            hist = other_players[pid]["history"]
                            hist.append({"x": px, "y": py, "rot": prot, "ts": ts})
                            hist.sort(key=lambda s: s["ts"])
                            if len(hist) > MAX_HISTORY:
                                hist[:] = hist[-MAX_HISTORY:]
                    except Exception:
                        continue
                last_fetch = now
            time.sleep(0.01)
        except Exception as e:
            print("Network error:", e)
            time.sleep(0.5)


if supabase:
    Thread(target=network_loop, daemon=True).start()
    print("Network thread started")
else:
    print("Running local-only")


# -------------------------
# Predictive update with velocity-based movement
# -------------------------
def update_predictions(dt):
    """Update all remote players using dead reckoning with velocity correction."""
    global other_players, other_players_display
    now = time.time()
    render_time = now - INTERP_DELAY
    display = {}

    for pid, data in list(other_players.items()):
        hist = data.get("history", [])
        if not hist:
            continue

        state = data["state"]
        target = data["target"]

        # Calculate target state from network data
        s0, s1 = None, None
        for i in range(len(hist) - 1):
            a = hist[i]
            b = hist[i + 1]
            if a["ts"] <= render_time <= b["ts"]:
                s0, s1 = a, b
                break

        if s0 and s1:
            # Interpolate between samples
            dt_net = max(1e-6, s1["ts"] - s0["ts"])
            alpha = (render_time - s0["ts"]) / dt_net
            alpha = max(0.0, min(1.0, alpha))

            # Target position
            target["x"] = lerp(s0["x"], s1["x"], alpha)
            target["y"] = lerp(s0["y"], s1["y"], alpha)
            target["rot"] = lerp_angle(s0["rot"], s1["rot"], alpha)

            # Target velocity (from network samples)
            target["vx"] = (s1["x"] - s0["x"]) / dt_net
            target["vy"] = (s1["y"] - s0["y"]) / dt_net
            rot_diff = (s1["rot"] - s0["rot"]) % (2 * math.pi)
            if rot_diff > math.pi:
                rot_diff -= 2 * math.pi
            target["vrot"] = rot_diff / dt_net

        elif render_time <= hist[0]["ts"]:
            # Before first sample - use it directly
            s = hist[0]
            target["x"] = s["x"]
            target["y"] = s["y"]
            target["rot"] = s["rot"]
            target["vx"] = 0.0
            target["vy"] = 0.0
            target["vrot"] = 0.0

        else:
            # After last sample - extrapolate with last known velocity
            last = hist[-1]
            prev = hist[-2] if len(hist) >= 2 else None

            if prev:
                dt_net = max(1e-6, last["ts"] - prev["ts"])
                target["vx"] = (last["x"] - prev["x"]) / dt_net
                target["vy"] = (last["y"] - prev["y"]) / dt_net
                rot_diff = (last["rot"] - prev["rot"]) % (2 * math.pi)
                if rot_diff > math.pi:
                    rot_diff -= 2 * math.pi
                target["vrot"] = rot_diff / dt_net
            else:
                target["vx"] = 0.0
                target["vy"] = 0.0
                target["vrot"] = 0.0

            # Extrapolate target position
            extra = render_time - last["ts"]
            extra_clamped = max(0.0, min(0.4, extra))
            damping = max(0.3, 1.0 - (extra_clamped / 0.4) * 0.6)

            target["x"] = last["x"] + target["vx"] * extra_clamped * damping
            target["y"] = last["y"] + target["vy"] * extra_clamped * damping
            target["rot"] = (last["rot"] + target["vrot"] * extra_clamped * damping) % (2 * math.pi)

        # DEAD RECKONING: Move boat using current velocity
        state["x"] += state["vx"] * dt
        state["y"] += state["vy"] * dt
        state["rot"] = (state["rot"] + state["vrot"] * dt) % (2 * math.pi)

        # VELOCITY CORRECTION: Smoothly adjust velocity toward target velocity
        state["vx"] = lerp(state["vx"], target["vx"], VELOCITY_CORRECTION_SPEED)
        state["vy"] = lerp(state["vy"], target["vy"], VELOCITY_CORRECTION_SPEED)
        state["vrot"] = lerp(state["vrot"], target["vrot"], VELOCITY_CORRECTION_SPEED)

        # POSITION CORRECTION: Gently correct position drift
        pos_error_x = target["x"] - state["x"]
        pos_error_y = target["y"] - state["y"]
        pos_error_dist = math.hypot(pos_error_x, pos_error_y)

        if pos_error_dist > 0.001:
            # Adaptive correction: stronger for large errors
            correction_strength = POSITION_CORRECTION_SPEED
            if pos_error_dist > MAX_POSITION_ERROR:
                correction_strength = lerp(POSITION_CORRECTION_SPEED, 0.3,
                                           min(1.0, (pos_error_dist - MAX_POSITION_ERROR) / MAX_POSITION_ERROR))

            state["x"] = lerp(state["x"], target["x"], correction_strength)
            state["y"] = lerp(state["y"], target["y"], correction_strength)

        # ROTATION CORRECTION
        state["rot"] = lerp_angle(state["rot"], target["rot"], ROTATION_CORRECTION_SPEED)

        # Calculate display speed
        speed = math.hypot(state["vx"], state["vy"])
        phase, amp = small_hash_to_phase_amp(pid)

        display[pid] = {
            "x": state["x"],
            "y": state["y"],
            "rot": state["rot"],
            "speed": speed,
            "sway_phase": phase,
            "sway_amp": amp
        }

    # Cleanup stale players
    stale_cutoff = now - 12.0
    to_delete = []
    for pid, data in list(other_players.items()):
        if data.get("history") and data["history"][-1]["ts"] < stale_cutoff:
            to_delete.append(pid)
    for pid in to_delete:
        other_players.pop(pid, None)

    other_players_display = display


# -------------------------
# Main loop
# -------------------------
async def main():
    global boat_x, boat_y, boat_rotation, boat_target_rotation
    global boat_velocity_x, boat_velocity_y
    global boat_current_velocity, boat_target_velocity, wake_fade
    global camera_x, camera_y, network_running

    running = True
    start_ticks = pygame.time.get_ticks()
    print("Predictive demo running — Player:", PLAYER_NAME)

    previous_boat_x = boat_x
    previous_boat_y = boat_y

    while running:
        dt = clock.get_time() / 1000.0
        if dt <= 0:
            dt = 1.0 / TARGET_FPS
        if dt > 0.25:
            dt = 0.25

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

        keys = pygame.key.get_pressed()

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            boat_target_rotation += rotation_speed * dt
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            boat_target_rotation -= rotation_speed * dt

        boat_rotation = lerp_angle(boat_rotation, boat_target_rotation, rotation_smoothing)
        boat_rotation %= (2 * math.pi)
        boat_target_rotation %= (2 * math.pi)

        previous_boat_x, previous_boat_y = boat_x, boat_y

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            boat_target_velocity = 1.0
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            boat_target_velocity = -0.27
        else:
            boat_target_velocity = 0.0

        if boat_target_velocity > boat_current_velocity:
            boat_current_velocity = min(boat_current_velocity + acceleration * dt, boat_target_velocity)
        else:
            boat_current_velocity = max(boat_current_velocity - deceleration * dt, boat_target_velocity)

        target_wake_fade = smoothstep(0.0, 0.2, abs(boat_current_velocity))
        if target_wake_fade > wake_fade:
            wake_fade = min(wake_fade + 3.5 * dt, target_wake_fade)
        else:
            wake_fade = max(wake_fade - 3.5 * dt, target_wake_fade)

        if boat_current_velocity > 0:
            boat_x += math.cos(boat_rotation) * boat_speed * boat_current_velocity * dt
            boat_y += math.sin(boat_rotation) * boat_speed * boat_current_velocity * dt
        elif boat_current_velocity < 0:
            boat_x += math.cos(boat_rotation) * boat_backward_speed * boat_current_velocity * dt
            boat_y += math.sin(boat_rotation) * boat_backward_speed * boat_current_velocity * dt

        boat_velocity_x = (boat_x - previous_boat_x) / (dt + 1e-6)
        boat_velocity_y = (boat_y - previous_boat_y) / (dt + 1e-6)

        boat_x = max(0.5, min(WORLD_WIDTH - 0.5, boat_x))
        boat_y = max(0.5, min(WORLD_HEIGHT - 0.5, boat_y))

        camera_x = lerp(camera_x, boat_x, camera_smoothing)
        camera_y = lerp(camera_y, boat_y, camera_smoothing)

        # Update predictions using velocity-based dead reckoning
        update_predictions(dt)

        # Update GL uniforms
        current_time = (pygame.time.get_ticks() - start_ticks) / 1000.0
        program['time'].value = float(current_time)
        program['boatPosition'].value = (float(boat_x), float(boat_y))
        program['boatRotation'].value = float(boat_rotation)
        program['boatVelocity'].value = (float(boat_velocity_x), float(boat_velocity_y))
        program['wakeFade'].value = float(wake_fade)
        program['cameraPos'].value = (float(camera_x), float(camera_y))
        program['viewportSize'].value = (float(viewport_width), float(viewport_height))

        # Prepare arrays for up to 10 other players
        display_list = list(other_players_display.values())[:10]
        num_other = len(display_list)
        program['numOtherPlayers'].value = num_other

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

        # Write uniforms
        try:
            program.get("otherBoatPositions").write(pos_array.tobytes())
            program.get("otherBoatRotations").write(rot_array.tobytes())
            program.get("otherBoatSpeeds").write(speed_array.tobytes())
            program.get("otherBoatSwayPhases").write(sway_phase_array.tobytes())
            program.get("otherBoatSwayAmps").write(sway_amp_array.tobytes())
        except Exception:
            try:
                program['otherBoatPositions'].value = tuple(pos_array.tolist())
                program['otherBoatRotations'].value = tuple(rot_array.tolist())
                program['otherBoatSpeeds'].value = tuple(speed_array.tolist())
                program['otherBoatSwayPhases'].value = tuple(sway_phase_array.tolist())
                program['otherBoatSwayAmps'].value = tuple(sway_amp_array.tolist())
            except Exception:
                pass

        # Render
        ctx.clear(0.0, 0.35, 0.75)
        vao.render(mode=moderngl.TRIANGLE_STRIP)
        pygame.display.flip()

        clock.tick(TARGET_FPS)
        await asyncio.sleep(0)

    # Cleanup
    network_running = False
    if supabase:
        try:
            supabase.table("players").delete().eq("player_id", PLAYER_ID).execute()
        except Exception:
            pass
    pygame.quit()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        network_running = False
        pygame.quit()
        print("Exited by user")