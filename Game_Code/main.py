import pygame
import moderngl
import asyncio
import math
from pygame import RESIZABLE
from config import *
from renderer import Renderer
from player import Player
from network import NetworkManager
from prediction import PredictionManager
from items import ItemManager

pygame.init()
#controller initialization
pygame.joystick.init()

#getting the joysticks
joystick_count = pygame.joystick.get_count()
if joystick_count == 0:
    print("No joysticks found.")
    controller_joystick = None # Set to None if no controller is found
else:
    # Get the first joystick (index 0 is usually the first connected controller)
    controller_joystick = pygame.joystick.Joystick(0)
    controller_joystick.init()
    print(f"Detected joystick: {controller_joystick.get_name()}")
    # Diagnostic: print axes/buttons/hats mapping to help map triggers
    try:
        naxes = controller_joystick.get_numaxes()
        nbuttons = controller_joystick.get_numbuttons()
        nhats = controller_joystick.get_numhats()
        print(f"Controller axes: {naxes}, buttons: {nbuttons}, hats: {nhats}")
        axes_vals = [controller_joystick.get_axis(i) for i in range(naxes)]
        print("Axis values:", axes_vals)
        btn_vals = [controller_joystick.get_button(i) for i in range(nbuttons)]
        print("Button values:", btn_vals)
        hat_vals = [controller_joystick.get_hat(i) for i in range(nhats)]
        print("Hat values:", hat_vals)
    except Exception:
        pass

#music
pygame.mixer.music.load('../Assets/Sounds/music.mp3')
pygame.mixer.music.play(-1)

# Set OpenGL attributes before creating the display
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_FORWARD_COMPATIBLE_FLAG, True)
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF | RESIZABLE)

pygame.display.set_caption("Boat Man Shooters")
clock = pygame.time.Clock()

# large font for overlay messages

ctx = moderngl.create_context()
print("OpenGL context created")

renderer = Renderer(ctx)
player = Player(0, 0) #spawn (7.5, 7.5) is the middle
network = NetworkManager(player)
prediction = PredictionManager()
item_manager = ItemManager(num_items=15) #number of items


async def main():
    running = True
    start_ticks = pygame.time.get_ticks()
    print("Demo running — Player:", network.PLAYER_NAME)

    #joystick and dpad directions
    joystick_x = 0.0
    joystick_y = 0.0
    dpad_x = 0
    dpad_y = 0

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
        player.update(dt, keys, controller_joystick)

        collision = item_manager.check_collision(player.x, player.y, player_radius=0.15)
        if collision:
            item_manager.resolve_collision(player, collision)

        prediction.update_predictions(dt, network.other_players)

        current_time = (pygame.time.get_ticks() - start_ticks) / 1000.0
        renderer.render(current_time, player, prediction.other_players_display, item_manager)
        # draw small rectangles above players (local + others) with names
        try:
            # build names mapping: 'local' -> local player name, other pid -> stored name if available
            names = {'local': getattr(network, 'PLAYER_NAME', 'You')}
            try:
                for pid, pdata in network.other_players.items():
                    names[pid] = pdata.get('name')
            except Exception:
                pass

            renderer.draw_player_nametags(player, prediction.other_players_display, names=names, y_offset=90)
        except Exception:
            pass

        # Draw sprint bar
        try:
            renderer.draw_sprint_bar(player)
        except Exception:
            pass

        # Draw disconnect overlay if network reports disconnected
        disconnected = not getattr(network, 'connected', True)
        if disconnected:
            tsec = pygame.time.get_ticks() / 1000.0
            # Smooth easing function for opacity using sine wave
            # Base opacity of 0.6 with a gentle oscillation of ±0.25
            # Slower animation for a more subtle effect (1.5 seconds per cycle)
            base_opacity = 0.6
            oscillation = 0.25
            frequency = 1.3  # cycles per second
            alpha = base_opacity + math.sin(tsec * frequency * math.pi) * oscillation
            # Ensure alpha stays within reasonable bounds
            alpha = max(0.35, min(0.85, alpha))
            
            text = "DISCONNECTED FROM SERVER"
            subtext = "Attempting to reconnect..."
            # draw overlay using the moderngl-backed renderer so it appears on OpenGL surface
            try:
                renderer.draw_overlay(text, subtext, alpha)
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