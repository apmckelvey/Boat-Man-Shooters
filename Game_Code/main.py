"""
MAIN MENU:

1. Have main-menu.png loaded in the middle of the screen
2. Have the Join Game and Settings buttons loaded on the menu in their respective order
3. BUTTON BEHAVIORS:
    a. When the cursor is hovered over the button, enlarge button by 10%, wiggle it for a sec, and add "aura" effect
    b. When the button is pressed, play press sound (../Assets/Sounds/Button Sounds/button-submit/button-submit-press.mp3) for normal button and change to pressed state graphic
        i. Keep the button in pressed graphic while being clicked
        ii. As button is being pressed, decrease the size by 5%
    c. When the button is unpressed, revert to the unpressed state, and play unpress sound (../Assets/Sounds/Button Sounds/button-submit/button-submit-unpress.mp3)

REFER TO THE BUTTON-TEST.HTML FOR THE PREFERRED BUTTON ANIMATIONS
"""
import pygame
import moderngl
import asyncio
from pygame import RESIZABLE
from config import *
from renderer import Renderer
from player import Player
from network import NetworkManager
from prediction import PredictionManager
from items import ItemManager
import math
import datetime
from prediction import *

pygame.init()
# controller initialization
pygame.joystick.init()

# getting the joysticks
joystick_count = pygame.joystick.get_count()
if joystick_count == 0:
    print("No joysticks found.")
    controller_joystick = None
else:
    try:
        controller_joystick = pygame.joystick.Joystick(0)
        controller_joystick.init()
        print(f"Detected joystick: {controller_joystick.get_name()}")
    except pygame.error as e:
        print(f"Warning: Controller detected but couldn't enable all features: {e}")
        print("Continuing without controller support...")
        controller_joystick = None

# music
pygame.mixer.music.load('../Assets/Sounds/music.mp3')
pygame.mixer.music.play(-1)

#cannonball sound
cannon_sound = pygame.mixer.Sound('../Assets/Sounds/Game Sounds/cannon.mp3')

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

L_Can_fire = True
R_Can_fire = True
L_fire_time = 0
R_fire_time = 0
cooldown = 1
current_time = pygame.time.get_ticks()

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
                        self.image = pygame.transform.scale(self.image, (32, 32))
                        print("Loaded cannonball.png successfully")
                    except Exception as e:
                        print(f"Could not load cannonball.png: {e}")
                        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
                        pygame.draw.circle(self.image, (200, 200, 200), (16, 16), 12)
                        pygame.draw.circle(self.image, (150, 150, 150), (16, 16), 10)

                    offset_distance = 0.15
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



            if event.type == pygame.KEYDOWN and game_state == "GAME":
                global L_Can_fire, R_Can_fire, current_time, L_fire_time, R_fire_time
                if pygame.key.get_pressed()[pygame.K_z]:
                    current_time = datetime.datetime.now()
                    NetworkManager.new_chat(network,  {
                        "msg": f"{input('Name: ')} - \"{input('Message: ')}\" @ {current_time.strftime('%c')}\""}) #FUTURE USE THREADING TO STOP PROJECT FROM STOPPING FOR INPUTS
                if pygame.key.get_pressed()[pygame.K_x]:
                    NetworkManager.get_chats(network)
                if pygame.key.get_pressed()[pygame.K_c]:
                    NetworkManager.delete_chat_history(network)

                if event.key == pygame.K_q and L_Can_fire is True:  # Left cannon
                    L_Can_fire = False
                    L_fire_time = current_time
                    new_ball = CannonBall(player.x, player.y, player.rotation, "left")
                    cannon_sound.play()
                    cannon_balls.append(new_ball)
                    print(f"Left cannon fired! Total balls: {len(cannon_balls)}")

                if event.key == pygame.K_e and R_Can_fire is True:  # Right cannon
                    R_Can_fire = False
                    R_fire_time = current_time
                    new_ball = CannonBall(player.x, player.y, player.rotation, "right")
                    cannon_sound.play()
                    cannon_balls.append(new_ball)
                    print(f"Right cannon fired! Total balls: {len(cannon_balls)}")

                if not L_Can_fire and current_time - L_fire_time >= cooldown:
                    L_Can_fire = True
                if not R_Can_fire and current_time - R_fire_time >= cooldown:
                    R_Can_fire = True


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
                    pygame.display.set_mode((WIDTH, HEIGHT),
                                                     pygame.OPENGL | pygame.DOUBLEBUF | pygame.FULLSCREEN)
                else:
                    pygame.display.set_mode((WIDTH, HEIGHT),
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
                    cannon_balls = []
                    print(f"{network.PLAYER_NAME} joined game")

        current_time = (pygame.time.get_ticks() - start_ticks) / 1000.0

        if game_state == "MENU":
            renderer.render_menu(current_time)
            pygame.display.flip()

        elif game_state == "GAME":
            keys = pygame.key.get_pressed()
            player.update(dt, keys, controller_joystick)

            cannon_balls = [ball for ball in cannon_balls if ball.update(dt)]

            collision = item_manager.check_collision(player.x, player.y, player_radius=0.15)
            if collision:
                item_manager.resolve_collision(player, collision)

            prediction.update_predictions(dt, network.other_players)

            renderer.render(current_time, player, prediction.other_players_display, item_manager)
            if cannon_balls:
                renderer.draw_cannon_balls(cannon_balls, player)

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
                renderer.draw_minimap(player, prediction.other_players_display)
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