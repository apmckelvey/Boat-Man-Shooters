import math
from utils import lerp_angle, smoothstep


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.rotation = 0.0
        self.target_rotation = 0.0

        self.speed = 0.5
        self.backward_speed = 0.08
        self.rotation_speed = 2.5
        self.rotation_smoothing = 0.15

        self.current_velocity = 0.0
        self.target_velocity = 0.0
        self.acceleration = 3.0
        self.deceleration = 4.0

        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.wake_fade = 0.0

        self.camera_x = x
        self.camera_y = y
        self.camera_smoothing = 0.12

        self.previous_x = x
        self.previous_y = y

        self.sprint = 100
        self.sprinting = False
        # Option to invert right-stick rotation direction if a controller's axis is reversed
        self.invert_right_stick = False
        # Left trigger rest value (detected on first controller sample) for robust LT detection
        self._lt_rest = None

    def update(self, dt, keys, controller=None):
        import pygame
        from config import WORLD_WIDTH, WORLD_HEIGHT

        # Regenerate sprint when not currently sprinting (time-based)
        if self.sprint < 100 and not self.sprinting:
            # regen rate: 10 units per second
            self.sprint = min(100, self.sprint + dt * 10.0)

        # Keyboard input for rotation
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.target_rotation += self.rotation_speed * dt
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.target_rotation -= self.rotation_speed * dt

        # Controller input for rotation (right stick or d-pad)
        # Read controller axes/hats defensively since some controllers may not have the same layout
        if controller is not None:
            try:
                    raw_rotation = controller.get_axis(2)
            except Exception:
                raw_rotation = 0.0
            # Allow inversion in case a controller's axis is reversed for rotation
            if self.invert_right_stick:
                rotation_value = -raw_rotation if raw_rotation is not None else 0.0
            else:
                rotation_value = raw_rotation if raw_rotation is not None else 0.0

            try:
                dpad_x = controller.get_hat(0)[0]
            except Exception:
                dpad_x = 0

            # Apply rotation with dead zone
            if abs(rotation_value) > 0.1:
                # Apply rotation in the same directional sense as keyboard/D-pad
                # If rotation_value is positive (stick right), rotate right (decrease target_rotation)
                # If rotation_value is negative (stick left), rotate left (increase target_rotation)
                self.target_rotation -= rotation_value * self.rotation_speed * dt
            if dpad_x != 0:
                self.target_rotation -= dpad_x * self.rotation_speed * dt

        self.rotation = lerp_angle(self.rotation, self.target_rotation, self.rotation_smoothing)
        self.rotation %= (2 * math.pi)
        self.target_rotation %= (2 * math.pi)

        self.previous_x, self.previous_y = self.x, self.y

        # Initialize movement input
        movement_input = 0.0

        # Keyboard controls
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            movement_input = 1.0
            if (keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]) and self.sprint > 0:
                self.sprint -= 0.5
                self.sprinting = True
                movement_input = 2
            if not keys[pygame.K_LSHIFT] or not keys[pygame.K_RSHIFT]:
                self.sprinting = False


        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            movement_input = -3.0

        # Controller input for movement (if controller is connected)
        if controller is not None:
            try:
                raw_stick = controller.get_axis(1)
            except Exception:
                raw_stick = 0.0
            stick_value = -raw_stick if raw_stick is not None else 0.0

            # Read left trigger (LT) defensively — common axes are 4 or 5 depending on driver
            lt_pressed = False
            try:
                lt_val = None
                for ax_idx in (4, 5):
                    try:
                        v = controller.get_axis(ax_idx)
                    except Exception:
                        v = None
                    if v is not None:
                        lt_val = v
                        break

                if lt_val is not None:
                    # Initialize resting value on first sample
                    if self._lt_rest is None:
                        self._lt_rest = lt_val

                    # Determine pressed relative to resting value to handle different driver mappings
                    # If rest is high (>0.5), pressing typically moves value lower -> detect drop
                    if self._lt_rest > 0.5:
                        lt_pressed = lt_val < (self._lt_rest - 0.4)
                    # If rest is low (<-0.5), pressing typically moves value higher -> detect increase
                    elif self._lt_rest < -0.5:
                        lt_pressed = lt_val > (self._lt_rest + 0.4)
                    else:
                        # Fallback: treat as pressed when lt_val is clearly positive
                        lt_pressed = lt_val > 0.5
            except Exception:
                lt_pressed = False

            # Stick: map to same keyboard rates with dead zone
            if abs(stick_value) > 0.1:
                if stick_value > 0:
                    movement_input = stick_value * 1.0
                    # Sprint when LT pressed: use time-based drain
                    if lt_pressed and self.sprint > 0:
                        # time-based drain so controller is frame-rate independent
                        # 0.5 per update @60 FPS -> 30 units/sec
                        self.sprint = max(0.0, self.sprint - dt * 30.0)
                        self.sprinting = True
                        movement_input = 2.0
                    else:
                        self.sprinting = False
                else:
                    movement_input = stick_value * 3.0

            # D-pad: only used if stick not engaged
            if abs(stick_value) <= 0.1:
                try:
                    dpad_y = controller.get_hat(0)[1]
                except Exception:
                    dpad_y = 0
                if dpad_y > 0:
                    movement_input = 1.0
                    if lt_pressed and self.sprint > 0:
                        # time-based drain so controller is frame-rate independent
                        # 0.5 per update @60 FPS -> 30 units/sec
                        self.sprint = max(0.0, self.sprint - dt * 30.0)
                        self.sprinting = True
                        movement_input = 2.0
                    else:
                        self.sprinting = False
                elif dpad_y < 0:
                    movement_input = -3.0

        # Apply the movement input
        self.target_velocity = movement_input

        if self.target_velocity > self.current_velocity:
            self.current_velocity = min(self.current_velocity + self.acceleration * dt, self.target_velocity)
        else:
            self.current_velocity = max(self.current_velocity - self.deceleration * dt, self.target_velocity)

        target_wake_fade = smoothstep(0.0, 0.2, abs(self.current_velocity))
        if target_wake_fade > self.wake_fade:
            self.wake_fade = min(self.wake_fade + 3.5 * dt, target_wake_fade)
        else:
            self.wake_fade = max(self.wake_fade - 3.5 * dt, target_wake_fade)

        if self.current_velocity > 0:
            self.x += math.cos(self.rotation) * self.speed * self.current_velocity * dt
            self.y += math.sin(self.rotation) * self.speed * self.current_velocity * dt
        elif self.current_velocity < 0:
            self.x += math.cos(self.rotation) * self.backward_speed * self.current_velocity * dt
            self.y += math.sin(self.rotation) * self.backward_speed * self.current_velocity * dt

        self.velocity_x = (self.x - self.previous_x) / (dt + 1e-6)
        self.velocity_y = (self.y - self.previous_y) / (dt + 1e-6)

        self.x = max(0.5, min(WORLD_WIDTH - 0.5, self.x))
        self.y = max(0.5, min(WORLD_HEIGHT - 0.5, self.y))

        self.camera_x += (self.x - self.camera_x) * self.camera_smoothing
        self.camera_y += (self.y - self.camera_y) * self.camera_smoothing
