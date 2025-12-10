# module imports
import pygame
import moderngl
import asyncio
import math
import random
import renderer

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

# muzic
pygame.mixer.music.load('../Assets/Sounds/music.mp3')
pygame.mixer.music.play(-1)
cannon_sound = pygame.mixer.Sound('../Assets/Sounds/Game Sounds/cannon.mp3')

# icon/window name
icon = pygame.image.load('../Logos/icon.png')
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

# game state vars
game_state = renderer.game_state

player = None
network = None
prediction = None
item_manager = None
menu_buttons = []

# cannon logic vars
cannon_balls = []
L_Can_fire = True
R_Can_fire = True
cooldown = 1.0
L_cooldown_end = 0.0
R_cooldown_end = 0.0

# trigger rest values (calibrated on first frame)
lt_rest = None
rt_rest = None
inescape_menu = False
escape_was_pressed = False


def open_settings_action():
    """CALLBACK FUNCTION for settings button!!!!!!!!!!!!!!!"""
    print("Settings button clicked")


async def main():
    global game_state, player, network, prediction, item_manager
    global L_Can_fire, R_Can_fire, lt_rest, rt_rest, cannon_balls, L_cooldown_end, R_cooldown_end, inescape_menu, escape_was_pressed, menu_buttons

    fullscreen = False
    running = True
    start_ticks = pygame.time.get_ticks()
    loading_game = False

    def set_loading_game(value):
        nonlocal loading_game
        loading_game = value

    # initialize menu buttons
    menu_buttons = [
        ButtonSubmit(
            x=WIDTH // 2,
            y=int(HEIGHT * 0.45),
            unpressed_path='../Graphics/UI Interface/Buttons/Join Game Button/join-game-button-unpressed.png',
            pressed_path='../Graphics/UI Interface/Buttons/Join Game Button/join-game-button-pressed.png',
            scale=0.40,
            action=lambda: set_loading_game(True)
        ),
        ButtonSubmit(
            x=WIDTH // 2,
            y=int(HEIGHT * 0.58),
            unpressed_path='../Graphics/UI Interface/Buttons/Settings Button/settings-button-unpressed.png',
            pressed_path='../Graphics/UI Interface/Buttons/Settings Button/settings-button-pressed.png',
            scale=0.40,
            action=open_settings_action
        )
    ]

    while running:
        menu_boolean = renderer.menu_boolean
        if menu_boolean is True:
            print(menu_boolean)
            game_state = "MENU"
            renderer.menu_boolean = False
            inescape_menu = False

        dt = clock.get_time() / 1000.0
        if dt <= 0:
            dt = 1.0 / TARGET_FPS
        if dt > 0.25:
            dt = 0.25

        current_time = (pygame.time.get_ticks() - start_ticks) / 1000.0

        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                running = False

            # triggers
            if event.type == pygame.JOYAXISMOTION and controller_joystick:
                global lt_rest, rt_rest
                if lt_rest is None or rt_rest is None:
                    try:
                        lt_rest = controller_joystick.get_axis(4)
                        rt_rest = controller_joystick.get_axis(5)
                    except:
                        pass

            if game_state == "GAME":
                # left cannon (LT)
                if event.type == pygame.JOYAXISMOTION and event.axis in (4, 5) and L_Can_fire:
                    value = event.value
                    axis = event.axis
                    if axis == 4:
                        if (lt_rest is None or abs(value - lt_rest) > 0.6):
                            # Create local cannonball
                            new_ball = CannonBall(player.x, player.y, player.rotation, "left")
                            cannon_balls.append(new_ball)
                            cannon_sound.play()

                            # Send to network
                            if network:
                                server_id = network.create_cannonball(new_ball.to_dict())
                                if server_id:
                                    new_ball.server_id = server_id

                            L_Can_fire = False
                            L_cooldown_end = current_time + cooldown
                            pygame.time.set_timer(pygame.USEREVENT + 1, int(cooldown * 1000), loops=1)

                # right cannon (RT)
                if event.type == pygame.JOYAXISMOTION and event.axis in (4, 5) and R_Can_fire:
                    value = event.value
                    if axis == 5:
                        if (rt_rest is None or abs(value - rt_rest) > 0.6):
                            # Create local cannonball
                            new_ball = CannonBall(player.x, player.y, player.rotation, "right")
                            cannon_balls.append(new_ball)
                            cannon_sound.play()

                            # Send to network
                            if network:
                                server_id = network.create_cannonball(new_ball.to_dict())
                                if server_id:
                                    new_ball.server_id = server_id

                            R_Can_fire = False
                            R_cooldown_end = current_time + cooldown
                            pygame.time.set_timer(pygame.USEREVENT + 2, int(cooldown * 1000), loops=1)

            # cooldown reset
            if event.type == pygame.USEREVENT + 1:
                L_Can_fire = True
                L_cooldown_end = 0.0
            if event.type == pygame.USEREVENT + 2:
                R_Can_fire = True
                R_cooldown_end = 0.0

            # keyboard fallback cannons
            if event.type == pygame.KEYDOWN and game_state == "GAME":
                if event.key == pygame.K_q and L_Can_fire:
                    new_ball = CannonBall(player.x, player.y, player.rotation, "left")
                    cannon_balls.append(new_ball)
                    cannon_sound.play()

                    # Send to network
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

                    # Send to network
                    if network:
                        server_id = network.create_cannonball(new_ball.to_dict())
                        if server_id:
                            new_ball.server_id = server_id

                    R_Can_fire = False
                    R_cooldown_end = current_time + cooldown
                    pygame.time.set_timer(pygame.USEREVENT + 2, int(cooldown * 1000), loops=1)
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE and not escape_was_pressed:
                        inescape_menu = not inescape_menu
                        escape_was_pressed = True
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_ESCAPE:
                    escape_was_pressed = False

        # game loop
        if game_state == "MENU":
            if loading_game:
                # Initialize game
                item_manager = ItemManager(num_items=15)
                fallback_x, fallback_y = 2.0, 2.0
                player = Player(fallback_x, fallback_y)

                for _ in range(50):
                    random_x = random.randint(1, WORLD_WIDTH - 1)
                    random_y = random.randint(1, WORLD_HEIGHT - 1)
                    if not item_manager.check_collision(random_x, random_y, player_radius=0.5):
                        player = Player(random_x, random_y)
                        break

                network = NetworkManager(player)
                prediction = PredictionManager()
                cannon_balls = []
                print(f"{network.PLAYER_NAME} joined game")

                game_state = "GAME"
                loading_game = False

            # Update menu buttons with events
            for button in menu_buttons:
                button.update(events)
            renderer.render_menu(current_time, menu_buttons)

        elif game_state == "GAME":
            keys = pygame.key.get_pressed()
            player.update(dt, keys, controller_joystick)

            # update local cannonballs
            cannon_balls = [b for b in cannon_balls if b.update(dt)]

            # update remote cannonballs
            if network:
                remote_balls = network.get_remote_cannonballs()
                for ball in remote_balls:
                    ball.update(dt)
                    # Add to display list if not already there
                    if ball.server_id and ball.server_id not in [cb.server_id for cb in cannon_balls if cb.server_id]:
                        cannon_balls.append(ball)

            # items
            collision = item_manager.check_collision(player.x, player.y, player_radius=0.15)
            if collision:
                item_manager.resolve_collision(player, collision)

            prediction.update_predictions(dt, network.other_players)

            # rendering
            renderer.render(current_time, player, prediction.other_players_display, item_manager)
            if cannon_balls:
                renderer.draw_cannon_balls(cannon_balls, player)

            # overlay elements
            try:
                names = {'local': getattr(network, 'PLAYER_NAME', 'You')}
                for pid, data in network.other_players.items():
                    names[pid] = data.get('name', '??? ')
                renderer.draw_player_nametags(player, prediction.other_players_display, names=names, y_offset=90)
                renderer.draw_minimap(player, prediction.other_players_display)
                renderer.draw_sprint_bar(player)

                if inescape_menu:
                    renderer.escape_menu(player)

                # cooldown fractions
                left_frac = 0.0
                right_frac = 0.0
                if L_cooldown_end and L_cooldown_end > current_time:
                    left_frac = min(max((L_cooldown_end - current_time) / cooldown, 0.0), 1.0)
                if R_cooldown_end and R_cooldown_end > current_time:
                    right_frac = min(max((R_cooldown_end - current_time) / cooldown, 0.0), 1.0)

                renderer.draw_health_and_cannon_cd(player, left_cd_frac=left_frac, right_cd_frac=right_frac)
            except Exception as e:
                print(f"Overlay error: {e}")

            # disconnected alert
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