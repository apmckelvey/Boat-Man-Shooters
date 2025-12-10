"""
BUTTON BEHAVIORS:
    a.   When the cursor is hovered over the button, enlarge the button by 10%, wiggle it for a sec, and add "aura" effect
    b.  When the button is pressed, play press sound (../Assets/Sounds/Button Sounds/button-submit/button-submit-press.mp3) for normal button and change to pressed state graphic
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
        self.base_scale = scale

        # Load images without conversion first
        unpressed_img = pygame.image. load(unpressed_path)
        pressed_img = pygame.image.load(pressed_path)

        # Store original images for high-quality scaling
        self.unpressed_original = unpressed_img. convert_alpha()
        self.pressed_original = pressed_img.convert_alpha()

        # Calculate scaled size
        self.scaled_width = int(self.unpressed_original.get_width() * self.base_scale)
        self.scaled_height = int(self.unpressed_original.get_height() * self.base_scale)

        # Pre-scale to base size using smoothscale for quality
        self.unpressed_image = pygame.transform.smoothscale(self.unpressed_original, (self.scaled_width, self.scaled_height))
        self.pressed_image = pygame.transform.smoothscale(self.pressed_original, (self.scaled_width, self.scaled_height))

        self.image = self.unpressed_image
        self.rect = self.image.get_rect(center=(x, y))
        self.action = action
        self.is_pressed = False
        self.is_hover = False
        self.hover_start = None
        self.wiggle_duration = 0.3

        try:
            self.press_sound = pygame.mixer.Sound('../Assets/Sounds/Button Sounds/button-submit/button-submit-press.mp3')
            self.unpress_sound = pygame.mixer.Sound('../Assets/Sounds/Button Sounds/button-submit/button-submit-unpress.mp3')
        except:
            self.press_sound = None
            self.unpress_sound = None

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
                if self.press_sound:
                    self. press_sound.play()
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.is_pressed and hover:
                    if self.unpress_sound:
                        self.unpress_sound.play()
                    if self.action:
                        self.action()
                self.is_pressed = False
                self. image = self.unpressed_image

    def draw(self, surface):
        scale = 1.0
        rotation = 0.0

        if self. is_pressed:
            current_image = self.pressed_image
            scale = 0.95
        else:
            current_image = self.unpressed_image

        if self.is_hover:
            scale = 1.1
            if self.hover_start:
                t = (pygame.time.get_ticks() / 1000.0 - self.hover_start) / self.wiggle_duration
                if t < 1:
                    rotation = math. sin(t * math.pi * 4) * 2

        # Draw aura effect
        if self.is_hover:
            for i in range(1, 16):
                glow_scale = scale + (i / 100.0)
                glow_width = int(current_image.get_width() * glow_scale)
                glow_height = int(current_image.get_height() * glow_scale)
                scaled_glow = pygame.transform.smoothscale(current_image, (glow_width, glow_height))
                scaled_glow.set_alpha(int(128 / i))
                glow_rect = scaled_glow.get_rect(center=(self.x, self.y))
                surface. blit(scaled_glow, glow_rect)

        # Draw main button image
        if scale != 1.0 or rotation != 0.0:
            transformed = pygame.transform.rotozoom(current_image, rotation, scale)
            rect = transformed.get_rect(center=(self.x, self.y))
            surface.blit(transformed, rect)
        else:
            surface.blit(current_image, self. rect)

class ButtonBack:
    def __init__(self, x, y, scale, action=None):
        self.x = x
        self. y = y
        self.base_scale = scale

        # Load images without conversion first
        unpressed_img = pygame.image. load("../Graphics/UI Interface/Buttons/Back Button/button-back-unpressed.png")
        pressed_img = pygame.image.load("../Graphics/UI Interface/Buttons/Back Button/button-back-pressed.png")

        # Store original images for high-quality scaling
        self.unpressed_original = unpressed_img. convert_alpha()
        self.pressed_original = pressed_img. convert_alpha()

        # Calculate scaled size
        self. scaled_width = int(self. unpressed_original.get_width() * self.base_scale)
        self.scaled_height = int(self.unpressed_original.get_height() * self.base_scale)

        # Pre-scale to base size using smoothscale for quality
        self.unpressed_image = pygame. transform.smoothscale(self. unpressed_original, (self. scaled_width, self.scaled_height))
        self.pressed_image = pygame.transform.smoothscale(self.pressed_original, (self.scaled_width, self.scaled_height))

        self.image = self.unpressed_image
        self.rect = self.image.get_rect(center=(x, y))
        self.action = action
        self.is_pressed = False
        self.is_hover = False
        self.hover_start = None
        self.wiggle_duration = 0.3

        try:
            self. press_sound = pygame.mixer. Sound('../Assets/Sounds/Button Sounds/button-back/button-back-press.mp3')
            self.unpress_sound = pygame.mixer.Sound('../Assets/Sounds/Button Sounds/button-back/button-back-unpress.mp3')
        except:
            self. press_sound = None
            self.unpress_sound = None

    def update(self, events):
        mouse_pos = pygame. mouse.get_pos()
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
                if self.press_sound:
                    self.press_sound. play()
            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if self.is_pressed and hover:
                    if self.unpress_sound:
                        self.unpress_sound. play()
                    if self. action:
                        self.action()
                self.is_pressed = False
                self.image = self.unpressed_image

    def draw(self, surface):
        scale = 1.0
        rotation = 0.0

        if self.is_pressed:
            current_image = self.pressed_image
            scale = 0.95
        else:
            current_image = self.unpressed_image

        if self.is_hover:
            scale = 1.1
            if self.hover_start:
                t = (pygame. time.get_ticks() / 1000.0 - self.hover_start) / self.wiggle_duration
                if t < 1:
                    rotation = math.sin(t * math.pi * 4) * 2

        # Draw aura effect
        if self.is_hover:
            for i in range(1, 16):
                glow_scale = scale + (i / 100.0)
                glow_width = int(current_image.get_width() * glow_scale)
                glow_height = int(current_image.get_height() * glow_scale)
                scaled_glow = pygame.transform.smoothscale(current_image, (glow_width, glow_height))
                scaled_glow.set_alpha(int(128 / i))
                glow_rect = scaled_glow. get_rect(center=(self. x, self.y))
                surface.blit(scaled_glow, glow_rect)

        # Draw main button image
        if scale != 1.0 or rotation != 0.0:
            transformed = pygame.transform. rotozoom(current_image, rotation, scale)
            rect = transformed.get_rect(center=(self.x, self.y))
            surface.blit(transformed, rect)
        else:
            surface.blit(current_image, self.rect)