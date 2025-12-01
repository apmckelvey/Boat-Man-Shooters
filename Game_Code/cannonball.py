import pygame
import math

class CannonBall:
    def __init__(self, x, y, rotation, side):
        self.x = x
        self.y = y
        self.rotation = rotation
        self.side = side
        self.speed = 1.2
        self.lifetime = 5.0
        self.age = 0.0

        try:
            img = pygame.image.load("../Graphics/Sprites/Cannonballs/cannonball.png").convert_alpha()
            self.image = pygame.transform.scale(img, (32, 32))
        except:
            self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (200, 200, 200), (16, 16), 16)

        offset_distance = 0.18
        angle_offset = 1.5 if side == "left" else -1.5
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