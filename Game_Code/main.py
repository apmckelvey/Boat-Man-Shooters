"""
we need to make the loading screen before the main menu render with the logo and the .gif before it
 and the one after the main menu into the game as “Loading… (##%)"
"""

# module imports
import pygame
import moderngl
import asyncio
import math
import random
import numpy as np
import os
import sys

#file path initialization
if sys.platform == 'darwin' and 'Contents/MacOS' in sys.argv[0]:
    BASE_DIR = os.path.join(os.dirname(sys.argv[0]), '..', 'Resources')
else:
    BASE_DIR = os.path.dirname(sys.argv[0])

# imports from other files
from config import *
from renderer import Renderer
from player import Player
from network import NetworkManager
from prediction import PredictionManager
from items import ItemManager
from cannonball import CannonBall
from buttons import ButtonSubmit

pygame.init()


# controller initialization
pygame.joystick.init()
controller_joystick = None
if pygame.joystick.get_count() > 0:
    try:
        controller_joystick = pygame.joystick.Joystick(0)
        controller_joystick.init()
        print(f"Controller detected: {controller_joystick.get_name()}")
    except Exception as e:
        print(f"Controller error: {e}")
        controller_joystick = None

# music & sounds
pygame.mixer.music.load(os.path.join(BASE_DIR, '../Assets/Sounds/music.mp3'))
pygame.mixer.music.play(-1)
cannon_sound = pygame.mixer.Sound(os.path.join(BASE_DIR, '../Assets/Sounds/Game Sounds/cannon.mp3'))

# icon/window
icon = pygame.image.load(os.path.join(BASE_DIR, '../Logos/icon.png'))
pygame.display.set_icon(icon)
pygame.display.set_caption("Boat Man Shooters")

# OpenGL setup
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF)
clock = pygame.time.Clock()
ctx = moderngl.create_context()
renderer = Renderer(ctx)



# game state
game_state = "SPLASH" #(loading)

player = None
network = None
prediction = None
item_manager = None
menu_buttons = []

# cannon vars
cannon_balls = []
L_Can_fire = True
R_Can_fire = True
cooldown = 1.0
L_cooldown_end = 0.0
R_cooldown_end = 0.0

# controller trigger rest values
lt_rest = None
rt_rest = None
inescape_menu = False
escape_was_pressed = False

# timing
splash_start_time = pygame.time.get_ticks() / 1000.0
load_start_time = None
SCREEN_DURATION = 5  # seconds


def open_settings_action():
    print("Settings button clicked")


async def main():
    global game_state, player, network, prediction, item_manager
    global L_Can_fire, R_Can_fire, lt_rest, rt_rest, cannon_balls, L_cooldown_end, R_cooldown_end
    global inescape_menu, escape_was_pressed, menu_buttons
    global splash_start_time, load_start_time

    running = True
    start_ticks = pygame.time.get_ticks()
    loading_game = False

    def set_loading_game(value):
        global load_start_time
        nonlocal loading_game
        loading_game = value
        if value:
            load_start_time = pygame.time.get_ticks() / 1000.0

    while running:
        cancel_button = renderer.cancel_button
        menu_boolean = renderer.menu_boolean
        if menu_boolean is True:
            print(menu_boolean)
            game_state = "MENU"
            renderer.menu_boolean = False
            inescape_menu = False
        if cancel_button is True:
            inescape_menu = False
            renderer.cancel_button = False
        current_time = (pygame.time.get_ticks() - start_ticks) / 1000.0
        dt = clock.get_time() / 1000.0
        if dt <= 0: dt = 1.0 / TARGET_FPS
        if dt > 0.25: dt = 0.25

        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False

            # controller trigger calibration
            if event.type == pygame.JOYAXISMOTION and controller_joystick:
                if lt_rest is None or rt_rest is None:
                    try:
                        lt_rest = controller_joystick.get_axis(4)
                        rt_rest = controller_joystick.get_axis(5)
                    except:
                        pass

            # cannon firing (only in GAME state)
            if game_state == "GAME":
                if event.type == pygame.JOYAXISMOTION and event.axis in (4, 5):
                    value = event.value
                    if event.axis == 4 and L_Can_fire and (lt_rest is None or abs(value - lt_rest) > 0.6):
                        new_ball = CannonBall(player.x, player.y, player.rotation, "left")
                        cannon_balls.append(new_ball)
                        cannon_sound.play()
                        if network:
                            server_id = network.create_cannonball(new_ball.to_dict())
                            if server_id:
                                new_ball.server_id = server_id
                        L_Can_fire = False
                        L_cooldown_end = current_time + cooldown
                        pygame.time.set_timer(pygame.USEREVENT + 1, int(cooldown * 1000), loops=1)

                    if event.axis == 5 and R_Can_fire and (rt_rest is None or abs(value - rt_rest) > 0.6):
                        new_ball = CannonBall(player.x, player.y, player.rotation, "right")
                        cannon_balls.append(new_ball)
                        cannon_sound.play()
                        if network:
                            server_id = network.create_cannonball(new_ball.to_dict())
                            if server_id:
                                new_ball.server_id = server_id
                        R_Can_fire = False
                        R_cooldown_end = current_time + cooldown
                        pygame.time.set_timer(pygame.USEREVENT + 2, int(cooldown * 1000), loops=1)

                if event.type == pygame.USEREVENT + 1:
                    L_Can_fire = True
                if event.type == pygame.USEREVENT + 2:
                    R_Can_fire = True

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q and L_Can_fire:
                        new_ball = CannonBall(player.x, player.y, player.rotation, "left")
                        cannon_balls.append(new_ball)
                        cannon_sound.play()
                        if network:
                            server_id = network.create_cannonball(new_ball.to_dict())
                            if server_id:
                                new_ball.server_id = server_id
                        L_Can_fire = False
                        L_cooldown_end = current_time + cooldown
                        pygame.time.set_timer(pygame.USEREVENT + 1, int(cooldown * 1000), loops=1)

                    if event.key == pygame.K_e and R_Can_fire:
                        new_ball = CannonBall(player.x, player.y, player.rotation, "right")
                        cannon_balls.append(new_ball)
                        cannon_sound.play()
                        if network:
                            server_id = network.create_cannonball(new_ball.to_dict())
                            if server_id:
                                new_ball.server_id = server_id
                        R_Can_fire = False
                        R_cooldown_end = current_time + cooldown
                        pygame.time.set_timer(pygame.USEREVENT + 2, int(cooldown * 1000), loops=1)

                    if event.key == pygame.K_ESCAPE and not escape_was_pressed:
                        inescape_menu = not inescape_menu
                        escape_was_pressed = True

                if event.type == pygame.KEYUP and event.key == pygame.K_ESCAPE:
                    escape_was_pressed = False

        if game_state == "SPLASH":
            elapsed = current_time - splash_start_time
            if elapsed >= SCREEN_DURATION:
                game_state = "MENU"
                menu_buttons = [
                    ButtonSubmit(WIDTH // 2, int(HEIGHT * 0.45),
                                 os.path.join(BASE_DIR, '../Graphics/UI Interface/Buttons/Join Game Button/join-game-button-unpressed.png'),
                                 os.path.join(BASE_DIR, '../Graphics/UI Interface/Buttons/Join Game Button/join-game-button-pressed.png'),
                                 scale=0.32, action=lambda: set_loading_game(True)),
                    ButtonSubmit(WIDTH // 2, int(HEIGHT * 0.58),
                                 os.path.join(BASE_DIR, '../Graphics/UI Interface/Buttons/Settings Button/settings-button-unpressed.png'),
                                 os.path.join(BASE_DIR, '../Graphics/UI Interface/Buttons/Settings Button/settings-button-pressed.png'),
                                 scale=0.32, action=open_settings_action)
                ]
            renderer.render_splash_screen(current_time)

        elif game_state == "MENU":
            if loading_game:
                now = pygame.time.get_ticks() / 1000.0
                elapsed = (now - load_start_time) if load_start_time else 0
                progress = min(elapsed / SCREEN_DURATION, 1.0)

                if elapsed >= SCREEN_DURATION:
                    item_manager = ItemManager(num_items=15)
                    renderer.setup_item_textures(item_manager)
                    fallback_x, fallback_y = 2.0, 2.0
                    player = Player(fallback_x, fallback_y)
                    for _ in range(50):
                        rx = random.randint(1, WORLD_WIDTH - 1)
                        ry = random.randint(1, WORLD_HEIGHT - 1)
                        if not item_manager.check_collision(rx, ry, player_radius=0.5):
                            player = Player(rx, ry)
                            break

                    network = NetworkManager(player)
                    prediction = PredictionManager()
                    cannon_balls = []
                    print(f"{network.PLAYER_NAME} joined game")
                    game_state = "GAME"
                    loading_game = False
                    load_start_time = None

                else:
                    renderer.render_loading_screen(current_time, progress)

            else:

                for button in menu_buttons:
                    button.update(events)

                renderer.render_menu(current_time, menu_buttons)
        elif game_state == "GAME":
            keys = pygame.key.get_pressed()
            player.update(dt, keys, controller_joystick)

            cannon_balls = [b for b in cannon_balls if b.update(dt)]

            if network:
                remote_balls = network.get_remote_cannonballs()
                for ball in remote_balls:
                    ball.update(dt)
                for remote_ball in remote_balls:
                    if remote_ball.server_id not in [cb.server_id for cb in cannon_balls if hasattr(cb, 'server_id')]:
                        cannon_balls.append(remote_ball)

            collision = item_manager.check_collision(player.x, player.y, player_radius=0.15)
            if collision:
                item_manager.resolve_collision(player, collision)

            prediction.update_predictions(dt, network.other_players)

            renderer.render(current_time, player, prediction.other_players_display, item_manager)
            renderer.draw_cannon_balls(cannon_balls, player)

            try:
                names = {'local': getattr(network, 'PLAYER_NAME', 'You')}
                for pid, data in network.other_players.items():
                    names[pid] = data.get('name', '???')
                renderer.draw_player_nametags(player, prediction.other_players_display, names=names, y_offset=90)
                renderer.draw_minimap(player, prediction.other_players_display)
                renderer.draw_sprint_bar(player)

                if inescape_menu:
                    renderer.escape_menu(player)

                left_frac = max(0.0, min((L_cooldown_end - current_time) / cooldown, 1.0)) if L_cooldown_end > current_time else 0.0
                right_frac = max(0.0, min((R_cooldown_end - current_time) / cooldown, 1.0)) if R_cooldown_end > current_time else 0.0
                renderer.draw_health_and_cannon_cd(player, left_cd_frac=left_frac, right_cd_frac=right_frac)
            except Exception as e:
                print(f"Overlay error: {e}")

            if not getattr(network, 'connected', True):
                t = pygame.time.get_ticks() / 1000.0
                alpha = 0.6 + math.sin(t * 4) * 0.2
                renderer.draw_overlay("DISCONNECTED", "Reconnecting...", alpha)

        pygame.display.flip()
        clock.tick(TARGET_FPS)
        await asyncio.sleep(0)

    if network:
        network.stop()
    pygame.quit()


if __name__ == "__main__":
    asyncio.run(main())