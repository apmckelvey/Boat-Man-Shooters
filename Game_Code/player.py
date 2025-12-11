import math
import pygame
from utils import lerp_angle, smoothstep
from config import SPRINT, WORLD_WIDTH, WORLD_HEIGHT
import os
import sys

#file path initialization
if sys.platform == 'darwin' and 'Contents/MacOS' in sys.argv[0]:
    BASE_DIR = os.path.join(os.dirname(sys.argv[0]), '..', 'Resources')
else:
    BASE_DIR = os.path.dirname(sys.argv[0])


class Player:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.rotation = 0.0
        self.target_rotation = 0.0

        self.speed = 1.0
        self.backward_speed = 0.25
        self.rotation_speed = 3.8
        self.rotation_smoothing = 0.15

        self.current_velocity = 0.0
        self.target_velocity = 0.0
        self.acceleration = 4.0
        self.deceleration = 5.0
        self.velocity_x = 0.0
        self.velocity_y = 0.0
        self.wake_fade = 0.0

        self.camera_x = x
        self.camera_y = y
        self.camera_smoothing = 0.12

        self.previous_x = x
        self.previous_y = y

        self.sprint = SPRINT
        self.display_sprint = SPRINT  # animated display value
        self.sprinting = False

        self.l3_pressed = False
        self.r3_pressed = False

        #motor sound
        self.motor_sound = pygame.mixer.Sound(os.path.join(BASE_DIR, '../Assets/Sounds/Game Sounds/motor.mp3'))
        self.motor_sound.set_volume(0.25)
        self.motor_sound.play(loops=-1)

        #engine sound
        self.engine_sound = pygame.mixer.Sound(os.path.join(BASE_DIR, '../Assets/Sounds/Game Sounds/boat.mp3'))
        self.engine_sound.set_volume(1.0)
        self.engine_channel = None
        self.engine_fade_ms = 120

    def update(self, dt, keys, controller=None):
        #input collection vars
        move_input = 0.0
        turn_input = 0.0
        sprint_this_frame = False

        #keyboard input
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            move_input = 1.0
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            move_input = -3.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            turn_input += 1.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            turn_input -= 1.0
        if keys[pygame.K_LSHIFT]:
            sprint_this_frame = True

        #controller
        if controller:
            #left stick
            lx = controller.get_axis(0)
            ly = controller.get_axis(1)
            #right stick
            rx = controller.get_axis(2)
            ry = controller.get_axis(3)

            #use stick with larger input
            move_stick = ly if abs(ly) > abs(ry) else ry
            turn_stick = lx if abs(lx) > abs(rx) else rx

            deadzone = 0.15
            if abs(move_stick) > deadzone:
                move_input = -move_stick  # inverted Y
            if abs(turn_stick) > deadzone:
                turn_input -= turn_stick * 1.2  # right stick feel

            #sprint logic
            if controller:
                l3 = controller.get_button(pygame.CONTROLLER_BUTTON_LEFTSTICK)
                r3 = controller.get_button(pygame.CONTROLLER_BUTTON_RIGHTSTICK)
                if l3 or r3:
                    sprint_this_frame = True
        #apply the sprint
        if sprint_this_frame and move_input > 0 and self.sprint > 0:
            self.sprinting = True
            self.sprint = max(0, self.sprint - dt * 35)
            move_input = 2.0
        else:
            self.sprinting = False
            if self.sprint < SPRINT:
                self.sprint += dt * 12  # regen
        
        # Smoothly animate display_sprint towards actual sprint value
        sprint_smoothing = 0.15
        self.display_sprint += (self.sprint - self.display_sprint) * sprint_smoothing

        # rotation
        self.target_rotation += turn_input * self.rotation_speed * dt
        self.rotation = lerp_angle(self.rotation, self.target_rotation, self.rotation_smoothing)
        self.rotation %= (2 * math.pi)
        self.target_rotation %= (2 * math.pi)

        #movement smoothing
        self.target_velocity = move_input
        if self.target_velocity > self.current_velocity:
            self.current_velocity = min(self.current_velocity + self.acceleration * dt, self.target_velocity)
        else:
            self.current_velocity = max(self.current_velocity - self.deceleration * dt, self.target_velocity)

        #engine sounds fade in/out
        moving = abs(self.current_velocity) > 0.01
        was_moving = abs((self.x - self.previous_x) / dt) > 0.01 if dt > 0 else False
        if moving and not was_moving:
            if not self.engine_channel:
                self.engine_channel = self.engine_sound.play(loops=-1, fade_ms=self.engine_fade_ms)
        elif not moving and was_moving and self.engine_channel:
            self.engine_channel.fadeout(self.engine_fade_ms)
            self.engine_channel = None

        self.previous_x, self.previous_y = self.x, self.y

        speed_multiplier = self.speed if self.current_velocity >= 0 else self.backward_speed
        self.x += math.cos(self.rotation) * speed_multiplier * self.current_velocity * dt
        self.y += math.sin(self.rotation) * speed_multiplier * self.current_velocity * dt

        #clamp to world
        self.x = max(0.5, min(WORLD_WIDTH - 0.5, self.x))
        self.y = max(0.5, min(WORLD_HEIGHT - 0.5, self.y))

        #cam follow
        self.camera_x += (self.x - self.camera_x) * self.camera_smoothing
        self.camera_y += (self.y - self.camera_y) * self.camera_smoothing

        target_wake = smoothstep(0.0, 0.25, abs(self.current_velocity))
        self.wake_fade += (target_wake - self.wake_fade) * 6.0 * dt

    def stop(self):
        if self.motor_sound: self.motor_sound.stop()
        if self.engine_channel: self.engine_channel.stop()