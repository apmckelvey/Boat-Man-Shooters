import pygame
import moderngl
import asyncio
import math
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

# large font for overlay messages

ctx = moderngl.create_context()
print("OpenGL context created")

renderer = Renderer(ctx)
player = Player(0, 0) #spawn (7.5, 7.5) is the middle
network = NetworkManager(player)
prediction = PredictionManager()


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

        # Draw disconnect overlay if network reports disconnected
        disconnected = not getattr(network, 'connected', True)
        if disconnected:
            tsec = pygame.time.get_ticks() / 1000.0
            # flash once per second
            visible = (math.sin(tsec * 1.0) > 0)
            if visible:
                text = "DISCONNECTED FROM SERVER"
                subtext = "Attempting to reconnect..."
                # draw overlay using the moderngl-backed renderer so it appears on OpenGL surface
                try:
                    renderer.draw_overlay(text, subtext)
                except Exception:
                    # fallback: nothing
                    pass

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