import pygame
import moderngl
import asyncio
from config import *
from renderer import Renderer
from player import Player
from network import NetworkManager
from prediction import PredictionManager

pygame.init()

# Set OpenGL attributes before creating the display
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
pygame.display.set_caption("Boat Man Shooters")
clock = pygame.time.Clock()

ctx = moderngl.create_context()
print("OpenGL context created")

renderer = Renderer(ctx)
player = Player(0, 0) #spawn (7.5, 7.5) is the middle
network = NetworkManager(player)
prediction = PredictionManager()

def draw_name_tags(screen, player, other_players_display, renderer):
    from config import WIDTH, HEIGHT
    font = pygame.font.SysFont(None, 24)
    screen_x, screen_y = renderer.world_to_screen(player.x, player.y, player.camera_x, player.camera_y, WIDTH, HEIGHT)

    #draw name above your boat
    name_surface = font.render(network.PLAYER_NAME, True, (255, 255, 255))
    name_rect = name_surface.get_rect(center=(screen_x, screen_y - 40))

    #draw outline
    outline_surface = font.render(network.PLAYER_NAME, True, (0, 0, 0))
    for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
        screen.blit(outline_surface, (name_rect.x + dx, name_rect.y + dy))

    screen.blit(name_surface, name_rect)

    #draw other ppls name tags
    for pid, data in other_players_display.items():
        screen_x, screen_y = renderer.world_to_screen(data['x'], data['y'], player.camera_x, player.camera_y, WIDTH, HEIGHT)

        player_name = data.get('name', 'Unknown')
        name_surface = font.render(player_name, True, (255, 255, 255))
        name_rect = name_surface.get_rect(center=(screen_x, screen_y - 40))

        #draw outline
        outline_surface = font.render(player_name, True, (0, 0, 0))
        for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            screen.blit(outline_surface, (name_rect.x + dx, name_rect.y + dy))

        screen.blit(name_surface, name_rect)
async def main():
    running = True
    start_ticks = pygame.time.get_ticks()
    print("Demo running — Player:", network.PLAYER_NAME)

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
        player.update(dt, keys)

        prediction.update_predictions(dt, network.other_players)

        current_time = (pygame.time.get_ticks() - start_ticks) / 1000.0
        renderer.render(current_time, player, prediction.other_players_display)

        draw_name_tags(screen, player, prediction.other_players_display, renderer)

        pygame.display.flip()
        clock.tick(TARGET_FPS)
        await asyncio.sleep(0)

    network.stop()
    pygame.quit()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        network.stop()
        pygame.quit()
        print("Exited by user")