import math
from utils import lerp_angle, smoothstep


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.rotation = 0.0
        self.target_rotation = 0.0

        self.speed = 0.3
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

    def update(self, dt, keys):
        import pygame
        from config import WORLD_WIDTH, WORLD_HEIGHT

        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.target_rotation += self.rotation_speed * dt
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.target_rotation -= self.rotation_speed * dt

        self.rotation = lerp_angle(self.rotation, self.target_rotation, self.rotation_smoothing)
        self.rotation %= (2 * math.pi)
        self.target_rotation %= (2 * math.pi)

        self.previous_x, self.previous_y = self.x, self.y

        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.target_velocity = 1.0
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.target_velocity = -0.27
        else:
            self.target_velocity = 0.0

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