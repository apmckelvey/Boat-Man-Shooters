import pygame
import math

class CannonBall:
    def __init__(self, x, y, rotation, side):
        self.x = x
        self.y = y
        self.rotation = rotation
        self.side = side
        self.speed = 1
        self.lifetime = 5.0
        self.age = 0.0

        try:
            self.image = pygame.image.load("../Graphics/Sprites/cannonball.png").convert_alpha()
            self.image = pygame.transform.scale(self.image, (24, 24))
            print("Loaded cannonball.png successfully")
        except Exception as e:
            print(f"Could not load cannonball.png: {e}")
            self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (200, 200, 200), (16, 16), 12)
            pygame.draw.circle(self.image, (150, 150, 150), (16, 16), 10)

        offset_distance = 0.15
        angle_offset = 1 if side == "left" else -1

        spawn_angle = rotation + angle_offset
        self.x += math.cos(spawn_angle) * offset_distance
        self.y += math.sin(spawn_angle) * offset_distance

        self.velocity_x = math.cos(spawn_angle) * self.speed
        self.velocity_y = math.sin(spawn_angle) * self.speed

    def update(self, dt):
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        self.age += dt
        return self.age < self.lifetime


