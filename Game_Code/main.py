"""
MAIN MENU:

1. Have main-menu.png loaded in the middle of the screen
2. Have the Join Game and Settings buttons loaded on the menu in their respective order
3. BUTTON BEHAVIORS:
    a. When the cursor is hovered over the button, enlarge button by 10%
    b. When the button is pressed, play press sound (../Assets/Sounds/Button\ Sounds/button-submit/button-submit-press.mp3) for normal button and change to pressed state graphic
        i. Keep the button in pressed graphic while being clicked
    c. When the button is unpressed, revert to the unpressed state, and play unpress sound (../Assets/Sounds/Button\ Sounds/button-submit/button-submit-unpress.mp3)
"""

import pygame
import moderngl
import asyncio
import math
import sys
from pygame import RESIZABLE
from config import *
from renderer import Renderer
from player import Player
from network import NetworkManager
from prediction import PredictionManager
from items import ItemManager

pygame.init()
# controller initialization
pygame.joystick.init()

# getting the joysticks
joystick_count = pygame.joystick.get_count()
if joystick_count == 0:
    print("No joysticks found.")
    controller_joystick = None
else:
    controller_joystick = pygame.joystick.Joystick(0)
    controller_joystick.init()
    print(f"Detected joystick: {controller_joystick.get_name()}")

# music
pygame.mixer.music.load('../Assets/Sounds/music.mp3')
pygame.mixer.music.play(-1)

icon = pygame.image.load('../Logos/icon.png')

pygame.display.set_icon(icon)
pygame.display.set_caption("Boat Man Shooters")

# Set OpenGL attributes before creating the display
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF | RESIZABLE)

clock = pygame.time.Clock()

ctx = moderngl.create_context()
print("OpenGL context created")

renderer = Renderer(ctx)


game_state = "MENU" #game state

player = None
network = None
prediction = None
item_manager = None


async def main():
    global game_state, player, network, prediction, item_manager

    fullscreen = False
    running = True
    start_ticks = pygame.time.get_ticks()

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
                if game_state == "GAME":
                    game_state = "MENU"
                    if network:
                        network.stop()
                    player = None
                    network = None
                    prediction = None
                    item_manager = None
                    print("Returned to main menu")
                else:
                    running = False
            if event.type == pygame.KEYDOWN and event.key == pygame.K_f:
                fullscreen = not fullscreen
                if fullscreen:
                    screen = pygame.display.set_mode((WIDTH, HEIGHT),
                                                     pygame.OPENGL | pygame.DOUBLEBUF | pygame.FULLSCREEN)
                else:
                    screen = pygame.display.set_mode((WIDTH, HEIGHT),
                                                     pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)

            if game_state == "MENU" and event.type == pygame.MOUSEBUTTONDOWN:
                mouse_pos = event.pos
                button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 30, 200, 60)
                if button_rect.collidepoint(mouse_pos):
                    game_state = "GAME"
                    player = Player(0, 0)
                    network = NetworkManager(player)
                    prediction = PredictionManager()
                    item_manager = ItemManager(num_items=15)
                    print(f"{network.PLAYER_NAME} joined game")

        current_time = (pygame.time.get_ticks() - start_ticks) / 1000.0

        if game_state == "MENU":
            renderer.render_menu(current_time)
            pygame.display.flip()

        elif game_state == "GAME":
            keys = pygame.key.get_pressed()
            player.update(dt, keys, controller_joystick)

            collision = item_manager.check_collision(player.x, player.y, player_radius=0.15)
            if collision:
                item_manager.resolve_collision(player, collision)

            prediction.update_predictions(dt, network.other_players)

            renderer.render(current_time, player, prediction.other_players_display, item_manager)

            try:
                names = {'local': getattr(network, 'PLAYER_NAME', 'You')}
                try:
                    for pid, pdata in network.other_players.items():
                        names[pid] = pdata.get('name')
                except Exception:
                    pass
                renderer.draw_player_nametags(player, prediction.other_players_display, names=names, y_offset=90)
            except Exception:
                pass

            try:
                renderer.draw_sprint_bar(player)
            except Exception:
                pass

            disconnected = not getattr(network, 'connected', True)
            if disconnected:
                tsec = pygame.time.get_ticks() / 1000.0
                base_opacity = 0.6
                oscillation = 0.25
                frequency = 1.3
                alpha = base_opacity + math.sin(tsec * frequency * math.pi) * oscillation
                alpha = max(0.35, min(0.85, alpha))

                text = "DISCONNECTED FROM SERVER"
                subtext = "Attempting to reconnect..."
                try:
                    renderer.draw_overlay(text, subtext, alpha)
                except Exception:
                    pass

            pygame.display.flip()

        clock.tick(TARGET_FPS)
        await asyncio.sleep(0)

    if network:
        network.stop()
    pygame.quit()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        network.stop()
        pygame.quit()
        print("Exited by user")