import time
import math
from config import *
from utils import lerp, lerp_angle, small_hash_to_phase_amp


class PredictionManager:
    def __init__(self):
        self.other_players_display = {}

    def update_predictions(self, dt, other_players):
        now = time.time()
        render_time = now - INTERP_DELAY
        display = {}

        for pid, data in list(other_players.items()):
            hist = data.get("history", [])
            if not hist:
                continue

            state = data["state"]
            target = data["target"]

            s0, s1 = None, None
            for i in range(len(hist) - 1):
                a = hist[i]
                b = hist[i + 1]
                if a["ts"] <= render_time <= b["ts"]:
                    s0, s1 = a, b
                    break

            if s0 and s1:
                dt_net = max(1e-6, s1["ts"] - s0["ts"])
                alpha = (render_time - s0["ts"]) / dt_net
                alpha = max(0.0, min(1.0, alpha))

                target["x"] = lerp(s0["x"], s1["x"], alpha)
                target["y"] = lerp(s0["y"], s1["y"], alpha)
                target["rot"] = lerp_angle(s0["rot"], s1["rot"], alpha)

                target["vx"] = (s1["x"] - s0["x"]) / dt_net
                target["vy"] = (s1["y"] - s0["y"]) / dt_net
                rot_diff = (s1["rot"] - s0["rot"]) % (2 * math.pi)
                if rot_diff > math.pi:
                    rot_diff -= 2 * math.pi
                target["vrot"] = rot_diff / dt_net

            elif render_time <= hist[0]["ts"]:
                s = hist[0]
                target["x"] = s["x"]
                target["y"] = s["y"]
                target["rot"] = s["rot"]
                target["vx"] = 0.0
                target["vy"] = 0.0
                target["vrot"] = 0.0

            else:
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

                extra = render_time - last["ts"]
                extra_clamped = max(0.0, min(0.4, extra))
                damping = max(0.3, 1.0 - (extra_clamped / 0.4) * 0.6)

                target["x"] = last["x"] + target["vx"] * extra_clamped * damping
                target["y"] = last["y"] + target["vy"] * extra_clamped * damping
                target["rot"] = (last["rot"] + target["vrot"] * extra_clamped * damping) % (2 * math.pi)

            state["x"] += state["vx"] * dt
            state["y"] += state["vy"] * dt
            state["rot"] = (state["rot"] + state["vrot"] * dt) % (2 * math.pi)

            state["vx"] = lerp(state["vx"], target["vx"], VELOCITY_CORRECTION_SPEED)
            state["vy"] = lerp(state["vy"], target["vy"], VELOCITY_CORRECTION_SPEED)
            state["vrot"] = lerp(state["vrot"], target["vrot"], VELOCITY_CORRECTION_SPEED)

            pos_error_x = target["x"] - state["x"]
            pos_error_y = target["y"] - state["y"]
            pos_error_dist = math.hypot(pos_error_x, pos_error_y)

            if pos_error_dist > 0.001:
                correction_strength = POSITION_CORRECTION_SPEED
                if pos_error_dist > MAX_POSITION_ERROR:
                    correction_strength = lerp(POSITION_CORRECTION_SPEED, 0.3,
                                               min(1.0, (pos_error_dist - MAX_POSITION_ERROR) / MAX_POSITION_ERROR))

                state["x"] = lerp(state["x"], target["x"], correction_strength)
                state["y"] = lerp(state["y"], target["y"], correction_strength)

            state["rot"] = lerp_angle(state["rot"], target["rot"], ROTATION_CORRECTION_SPEED)

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

        stale_cutoff = now - 12.0
        to_delete = []
        for pid, data in list(other_players.items()):
            if data.get("history") and data["history"][-1]["ts"] < stale_cutoff:
                to_delete.append(pid)
        for pid in to_delete:
            other_players.pop(pid, None)

        self.other_players_display = display