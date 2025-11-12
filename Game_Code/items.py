import pygame
import random
import math
from config import WORLD_WIDTH, WORLD_HEIGHT


class Item:

    def __init__(self, x, y, item_type, image):
        self.x = x
        self.y = y
        self.item_type = item_type  # 1-5
        self.image = image
        self.width = 0.1  # collision size in world units
        self.height = 0.1

    def check_collision(self, player_x, player_y, player_radius=0.2):
        # Simple circle-rectangle collision
        # Find the closest point on the rectangle to the circle
        closest_x = max(self.x - self.width / 2, min(player_x, self.x + self.width / 2))
        closest_y = max(self.y - self.height / 2, min(player_y, self.y + self.height / 2))

        # Calculate distance from closest point to circle center
        distance_x = player_x - closest_x
        distance_y = player_y - closest_y
        distance = math.sqrt(distance_x ** 2 + distance_y ** 2)

        return distance < player_radius


class ItemManager:
    def __init__(self, num_items=15):
        self.items = []
        self.images = {}
        self.num_items = num_items
        self.textures = {}  # Will store ModernGL textures
        self._load_item_images()
        xvalues = [3, 14, 7, 11, 2, 9, 13, 5, 12, 6, 8, 1, 13, 4, 10, 7, 3, 15, 9, 12, 5, 11]
        yvalues = [8, 2, 14, 6, 11, 3, 10, 7, 10, 4, 13, 5, 9, 1, 12, 8, 14, 6, 11, 3, 14.2]
        self._spawn_items(xvalues,yvalues)


    def create_gl_textures(self, ctx):
        for item_type, image in self.images.items():
            width, height = image.get_size()
            image_data = pygame.image.tobytes(image, "RGBA", True)
            texture = ctx.texture((width, height), 4, image_data)
            texture.filter = (ctx.LINEAR, ctx.LINEAR)
            self.textures[item_type] = texture
            print(f"Created GL texture for item {item_type}")

    def _load_item_images(self):
        for i in range(1, 6):  # item1 through item5
            try:
                image = pygame.image.load(f"../Graphics/Map-Items/Rocks/rock{i}.png").convert_alpha()
                # Scale image if needed (optional)
                # image = pygame.transform.scale(image, (64, 64))
                self.images[i] = image
                print(f"Loaded rock{i}.png")
            except Exception as e:
                print(f"Warning: Could not load rock{i}.png - {e}")
                # Create placeholder if image not found
                placeholder = pygame.Surface((64, 64), pygame.SRCALPHA)
                # Draw a simple colored square for each item type
                colors = [(255, 100, 100), (100, 255, 100), (100, 100, 255),
                          (255, 255, 100), (255, 100, 255)]
                pygame.draw.rect(placeholder, colors[i - 1], (0, 0, 64, 64))
                pygame.draw.rect(placeholder, (0, 0, 0), (0, 0, 64, 64), 3)
                self.images[i] = placeholder


    def _spawn_items(self, xvalues, yvalues):
        # Create a margin from the edges
        margin = 1.0

        for _ in range(self.num_items):

            # Random position within world bounds
            x = xvalues.pop(0)
            y = yvalues.pop(0)

            # Random item type (1-5)
            item_type = random.randint(1, 5)

            # Get the image for this item type
            image = self.images.get(item_type)

            # Create and add the item
            item = Item(x, y, item_type, image)
            self.items.append(item)

        print(f"Spawned {len(self.items)} items on the map")

    def check_collision(self, player_x, player_y, player_radius=0.2):

        for item in self.items:
            if item.check_collision(player_x, player_y, player_radius):
                # Calculate collision normal (direction to push player away)
                dx = player_x - item.x
                dy = player_y - item.y
                distance = math.sqrt(dx ** 2 + dy ** 2)

                if distance > 0:
                    # Normalize
                    normal_x = dx / distance
                    normal_y = dy / distance
                    return (normal_x, normal_y, item)

        return None

    def resolve_collision(self, player, collision_info):
        if collision_info is None:
            return

        normal_x, normal_y, item = collision_info

        # Push player away from the item
        push_distance = 0.009 # How much to push the player
        player.x += normal_x * push_distance
        player.y += normal_y * push_distance

        # Stop player velocity in the direction of collision
        # This prevents the player from "sticking" to items
        velocity_dot_normal = (player.velocity_x * normal_x +
                               player.velocity_y * normal_y)

        if velocity_dot_normal < 0:  # Moving towards the item
            player.velocity_x -= velocity_dot_normal * normal_x
            player.velocity_y -= velocity_dot_normal * normal_y

    def get_visible_items(self, camera_x, camera_y, visible_radius=10.0):
        """Get items that are visible from the camera position"""
        visible = []
        for item in self.items:
            dx = item.x - camera_x
            dy = item.y - camera_y
            distance = math.sqrt(dx ** 2 + dy ** 2)

            if distance <= visible_radius:
                visible.append(item)

        return visible