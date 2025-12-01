"""
BUTTON BEHAVIORS:
    a. When the cursor is hovered over the button, enlarge the button by 10%, wiggle it for a sec, and add "aura" effect
    b. When the button is pressed, play press sound (../Assets/Sounds/Button Sounds/button-submit/button-submit-press.mp3) for normal button and change to pressed state graphic
        i. Keep the button in pressed graphic while being clicked
        ii. As button is being pressed, decrease the size by 5%
    c. When the button is unpressed, revert to the unpressed state, and play unpress sound (../Assets/Sounds/Button Sounds/button-submit/button-submit-unpress.mp3)

REFER TO THE BUTTON-TEST.HTML FOR THE PREFERRED BUTTON ANIMATIONS
"""

#module imports
import pygame
import math

class ButtonSubmit:
    def __init__(self, x, y, unpressed_path, pressed_path, scale, action=None):
        self.x = x
        self.y = y
        self.scale = scale
        unpressed_img = pygame.image.load(unpressed_path).convert_alpha()
        pressed_img = pygame.image.load(pressed_path).convert_alpha()
        self.unpressed_image = pygame.transform.scale_by(unpressed_img, self.scale)
        self.pressed_image = pygame.transform.scale_by(pressed_img, self.scale)
        self.image = self.unpressed_image
        self.rect = self.image.get_rect(center=(x, y))
        self.action = action
        self.is_pressed = False
        self.is_hover = False
        self.hover_start = None
        self.wiggle_duration = 0.3 #seconds
        self.press_sound = pygame.mixer.Sound('../Assets/Sounds/Button Sounds/button-submit/button-submit-press.mp3')
        self.unpress_sound = pygame.mixer.Sound(
            '../Assets/Sounds/Button Sounds/button-submit/button-submit-unpress.mp3')

    def update(self, events):
        mouse_pos = pygame.mouse.get_pos()
        hover = self.rect.collidepoint(mouse_pos)

        if hover and not self.is_hover:
            self.is_hover = True
            self.hover_start = pygame.time.get_ticks() / 1000.0
        elif not hover:
            self.is_hover = False
            self.hover_start = None

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and hover:
                self.is_pressed = True
                self.image = self.pressed_image
                self.press_sound.play()
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.is_pressed and hover:
                    self.unpress_sound.play()
                    if self.action:
                        self.action()
                self.is_pressed = False
                self.image = self.unpressed_image

    def draw(self, surface):
        scale = 1.0
        rotation = 0.0
        current_image = self.image

        if self.is_pressed:
            scale = 0.95  #decrease by 5%
        elif self.is_hover:
            scale = 1.1  #enlarge by 10%
            if self.hover_start:
                t = (pygame.time.get_ticks() / 1000.0 - self.hover_start) / self.wiggle_duration
                if t < 1:
                    #wiggle: rotation between -2 and 2 degrees, 4 times
                    rotation = math.sin(t * math.pi * 4) * 2

        #"aura" effect
        if self.is_hover:
            for i in range(1, 16): #layers for glow
                glow_scale = scale + (i / 100.0)
                scaled_glow = pygame.transform.smoothscale(current_image,(int(current_image.get_width() * glow_scale), int(current_image.get_height() * glow_scale)))
                scaled_glow.set_alpha(int(128 / i))
                glow_rect = scaled_glow.get_rect(center=(self.x, self.y))
                surface.blit(scaled_glow, glow_rect)

        #draw main button image
        if scale != 1.0 or rotation != 0.0:
            transformed = pygame.transform.rotozoom(current_image, rotation, scale)
            rect = transformed.get_rect(center=(self.x, self.y))
            surface.blit(transformed, rect)
        else:
            surface.blit(current_image, self.rect)

class ButtonBack:
    def __init__(self, x, y, scale, action=None):
        self.x = x
        self.y = y
        self.scale = scale
        unpressed_img = pygame.image.load("/Graphics/UI Interface/Buttons/Back Button/button-back-unpressed.png").convert_alpha()
        pressed_img = pygame.image.load("/Graphics/UI Interface/Buttons/Back Button/button-back-pressed.png").convert_alpha()
        self.unpressed_image = pygame.transform.scale_by(unpressed_img, self.scale)
        self.pressed_image = pygame.transform.scale_by(pressed_img, self.scale)
        self.image = self.unpressed_image
        self.rect = self.image.get_rect(center=(x, y))
        self.action = action
        self.is_pressed = False
        self.is_hover = False
        self.hover_start = None
        self.wiggle_duration = 0.3 #seconds
        self.press_sound = pygame.mixer.Sound('../Assets/Sounds/Button Sounds/button-back/button-back-press.mp3')
        self.unpress_sound = pygame.mixer.Sound('../Assets/Sounds/Button Sounds/button-back/button-back-unpress.mp3')

    def update(self, events):
        mouse_pos = pygame.mouse.get_pos()
        hover = self.rect.collidepoint(mouse_pos)

        if hover and not self.is_hover:
            self.is_hover = True
            self.hover_start = pygame.time.get_ticks() / 1000.0
        elif not hover:
            self.is_hover = False
            self.hover_start = None

        for event in events:
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and hover:
                self.is_pressed = True
                self.image = self.pressed_image
                self.press_sound.play()
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.is_pressed and hover:
                    self.unpress_sound.play()
                    if self.action:
                        self.action()
                self.is_pressed = False
                self.image = self.unpressed_image

    def draw(self, surface):
        scale = 1.0
        rotation = 0.0
        current_image = self.image

        if self.is_pressed:
            scale = 0.95  #decrease by 5%
        elif self.is_hover:
            scale = 1.1  #enlarge by 10%
            if self.hover_start:
                t = (pygame.time.get_ticks() / 1000.0 - self.hover_start) / self.wiggle_duration
                if t < 1:
                    #wiggle: rotation between -2 and 2 degrees, 4 times
                    rotation = math.sin(t * math.pi * 4) * 2

        #"aura" effect
        if self.is_hover:
            for i in range(1, 16): #layers for glow
                glow_scale = scale + (i / 100.0)
                scaled_glow = pygame.transform.smoothscale(current_image,(int(current_image.get_width() * glow_scale), int(current_image.get_height() * glow_scale)))
                scaled_glow.set_alpha(int(128 / i))
                glow_rect = scaled_glow.get_rect(center=(self.x, self.y))
                surface.blit(scaled_glow, glow_rect)

        #draw main button image
        if scale != 1.0 or rotation != 0.0:
            transformed = pygame.transform.rotozoom(current_image, rotation, scale)
            rect = transformed.get_rect(center=(self.x, self.y))
            surface.blit(transformed, rect)
        else:
            surface.blit(current_image, self.rect)