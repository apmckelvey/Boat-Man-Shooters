import pygame
import math


class CannonBall:
    def __init__(self, x, y, rotation, side, velocity_x=None, velocity_y=None, server_id=None):
        self.x = x
        self.y = y
        self.rotation = rotation
        self.side = side
        self.speed = 1.2
        self.lifetime = 5.0
        self.age = 0.0
        self.server_id = server_id  # ID from Supabase
        self.is_remote = server_id is not None  # If created by another player

        try:
            img = pygame.image.load("../Graphics/Sprites/Cannonballs/cannonball.png").convert_alpha()
            self.image = pygame.transform.scale(img, (32, 32))
        except:
            self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.circle(self.image, (200, 200, 200), (16, 16), 16)

        offset_distance = 0.18
        angle_offset = 1.5 if side == "left" else -1.5
        spawn_angle = rotation + angle_offset

        # Initial position offset
        init_x = x + math.cos(spawn_angle) * offset_distance
        init_y = y + math.sin(spawn_angle) * offset_distance

        # Use provided velocities for remote cannonballs, calculate for local
        if velocity_x is not None and velocity_y is not None:
            self.velocity_x = velocity_x
            self.velocity_y = velocity_y
            # Use provided x, y directly for remote balls
            self.x = x
            self.y = y
        else:
            self.velocity_x = math.cos(spawn_angle) * self.speed
            self.velocity_y = math.sin(spawn_angle) * self.speed
            self.x = init_x
            self.y = init_y

    def update(self, dt):
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt
        self.age += dt
        return self.age < self.lifetime

    def to_dict(self):
        """Convert to dictionary for Supabase"""
        return {
            "player_id": None,  # Will be set by NetworkManager
            "x": self.x,
            "y": self.y,
            "rotation": self.rotation,
            "velocity_x": self.velocity_x,
            "velocity_y": self.velocity_y,
            "side": self.side
        }

    @classmethod
    def from_dict(cls, data):
        """Create cannonball from Supabase data"""
        return cls(
            x=float(data["x"]),
            y=float(data["y"]),
            rotation=float(data["rotation"]),
            side=data["side"],
            velocity_x=float(data["velocity_x"]),
            velocity_y=float(data["velocity_y"]),
            server_id=data["id"]
        )

