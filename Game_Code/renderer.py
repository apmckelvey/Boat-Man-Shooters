import moderngl
import numpy as np
import pygame
import pygame.freetype
import os

from pygame import Surface

from config import WIDTH, HEIGHT
from shaders import vertex_shader, fragment_shader


class Renderer:
    def __init__(self, ctx):
        self.ctx = ctx
        # changed aspect ratio to make map bigger - seems like a good size???
        self.viewport_width = 2.3
        self.viewport_height = 1.3

        self._load_boat_texture()
        self._compile_shaders()
        self._create_geometry()
        # overlay resources (for UI text rendered via pygame -> GL texture)
        self._create_overlay_resources()
        self.item_textures = {}
        self.item_textures_loaded = False
        # cached fullscreen surface used by overlay drawing functions
        self._overlay_surf = None
        self._overlay_surf_size = (WIDTH, HEIGHT)

        # preload health images so we don't hit disk each frame
        self.health_images = {}
        try:
            self.health_images['green'] = pygame.image.load("../Graphics/Overlay/boat-health-green.png").convert_alpha()
            self.health_images['yellow'] = pygame.image.load(
                "../Graphics/Overlay/boat-health-yellow.png").convert_alpha()
            self.health_images['orange'] = pygame.image.load(
                "../Graphics/Overlay/boat-health-orange.png").convert_alpha()
            self.health_images['red'] = pygame.image.load("../Graphics/Overlay/boat-health-red.png").convert_alpha()
        except Exception:
            # fallback if files missing — small tinted surfaces
            def _placeholder(c):
                s = pygame.Surface((48, 12), pygame.SRCALPHA)
                s.fill(c + (255,))
                return s

            self.health_images['green'] = _placeholder((80, 200, 120))
            self.health_images['yellow'] = _placeholder((240, 220, 80))
            self.health_images['orange'] = _placeholder((240, 150, 80))
            self.health_images['red'] = _placeholder((240, 80, 80))

    def render_menu(self, time):
        from config import WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT

        camera_x = WORLD_WIDTH / 2.0
        camera_y = WORLD_HEIGHT / 2.0

        self.program['time'].value = float(time)
        self.program['wakeFade'].value = 0.0
        self.program['cameraPos'].value = (float(camera_x), float(camera_y))
        self.program['viewportSize'].value = (float(self.viewport_width), float(self.viewport_height))
        self.program['worldSize'].value = (float(WORLD_WIDTH), float(WORLD_HEIGHT))
        self.program['numOtherPlayers'].value = 0

        try:
            self.program['numItems'].value = 0
        except Exception:
            pass

        self.ctx.clear(0.0, 0.35, 0.75)
        self.vao.render(mode=moderngl.TRIANGLE_STRIP)

        surf = self._get_overlay_surface()

        menu_image = pygame.image.load("../Graphics/UI Interface/Menus/main-menu.png").convert_alpha()
        resized_image = pygame.transform.smoothscale(menu_image, (463, 650))
        menu_rect = surf.get_rect(center=(WIDTH // 2, HEIGHT // 2))

        if self.overlay_font_large:
            try:
                surf.blit(resized_image, (WIDTH // 2 - 250, HEIGHT - HEIGHT))
            except Exception:
                pass

        button_rect = pygame.Rect(WIDTH // 2 - 100, HEIGHT // 2 - 30, 200, 60)
        mouse_pos = pygame.mouse.get_pos()
        is_hovering = button_rect.collidepoint(mouse_pos)

        if is_hovering:
            button_color = (100, 200, 100, 220)
            text_color = (255, 255, 255)
        else:
            button_color = (50, 150, 50, 200)
            text_color = (230, 230, 230)

        pygame.draw.rect(surf, button_color, button_rect, border_radius=10)
        pygame.draw.rect(surf, (255, 255, 255, 180), button_rect, 3, border_radius=10)

        if self.overlay_font_small:
            try:
                button_text = "START GAME"
                text_surf, _ = self.overlay_font_small.render(button_text, text_color)
                text_rect = text_surf.get_rect(center=button_rect.center)
                surf.blit(text_surf, text_rect)
            except Exception:
                pass

        data = pygame.image.tobytes(surf, 'RGBA', True)
        w, h = surf.get_size()

        try:
            if self.overlay_texture is None:
                self.overlay_texture = self.ctx.texture((w, h), 4, data)
                self.overlay_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            else:
                try:
                    self.overlay_texture.write(data)
                except Exception:
                    self.overlay_texture.release()
                    self.overlay_texture = self.ctx.texture((w, h), 4, data)
                    self.overlay_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)

            self.overlay_texture.use(location=2)
            try:
                self.overlay_program['overlayTexture'].value = 2
            except Exception:
                pass

            self.ctx.enable(moderngl.BLEND)
            self.overlay_vao.render(mode=moderngl.TRIANGLE_STRIP)
        except Exception:
            return

    def setup_item_textures(self, item_manager):
        if self.item_textures_loaded:
            return

        # create openGL textures from pygame surfaces
        item_manager.create_gl_textures(self.ctx)

        # bind each item texture to a texture unit
        for item_type in range(1, 6):
            if item_type in item_manager.textures:
                texture = item_manager.textures[item_type]
                texture.use(location=2 + item_type)
                self.item_textures[item_type] = texture

                try:
                    self.program[f'itemTexture{item_type}'].value = 2 + item_type
                    print(f"Bound itemTexture{item_type} to unit {2 + item_type}")
                except Exception as e:
                    print(f"Warning: Could not bind itemTexture{item_type}: {e}")

        self.item_textures_loaded = True
        print(f"Loaded {len(self.item_textures)} item textures")

    def world_to_screen(self, world_x, world_y, camera_x, camera_y, screen_width, screen_height):
        rel_x = world_x - camera_x
        rel_y = world_y - camera_y
        # conver to screen space
        screen_x = (rel_x / self.viewport_width) * screen_width + screen_width / 2.0
        screen_y = screen_height / 2 - (rel_y / self.viewport_height) * screen_height

        return screen_x, screen_y

    def _load_boat_texture(self):
        try:
            boat_image = pygame.image.load("../Graphics/Sprites/Boats/player.png").convert_alpha()
            self.boat_width, self.boat_height = boat_image.get_size()
            self.boat_aspect = float(self.boat_width) / float(self.boat_height) if self.boat_height else 1.0
            boat_data = pygame.image.tobytes(boat_image, "RGBA", True)
            print(f"Loaded boat.png ({self.boat_width}x{self.boat_height}), aspect={self.boat_aspect:.3f}")
        except Exception:
            print("boat.png not found — creating placeholder")
            self.boat_width, self.boat_height = 64, 64
            self.boat_aspect = 1.0
            surf = pygame.Surface((self.boat_width, self.boat_height), pygame.SRCALPHA)
            pygame.draw.polygon(surf, (139, 69, 19), [(50, 32), (10, 20), (10, 44)])
            pygame.draw.circle(surf, (255, 255, 255), (35, 32), 8)
            boat_data = pygame.image.tobytes(surf, "RGBA", True)

        self.boat_texture = self.ctx.texture((self.boat_width, self.boat_height), 4, boat_data)
        self.boat_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)

        # load enemy texture (used for other players)
        try:
            enemy_image = pygame.image.load("../Graphics/Sprites/Boats/enemy.png").convert_alpha()
            ew, eh = enemy_image.get_size()
            enemy_data = pygame.image.tobytes(enemy_image, "RGBA", True)
            self.enemy_width, self.enemy_height = ew, eh
            self.enemy_aspect = float(ew) / float(eh) if eh else 1.0
        except Exception:
            # fallback to boat texture if enemy not found
            enemy_data = boat_data
            self.enemy_width, self.enemy_height = self.boat_width, self.boat_height
            self.enemy_aspect = getattr(self, 'boat_aspect', 1.0)

        self.enemy_texture = self.ctx.texture((self.enemy_width, self.enemy_height), 4, enemy_data)
        self.enemy_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)

    def _compile_shaders(self):
        self.program = self.ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)
        # bind textures: player boat -> unit 0, enemy boat -> unit 1
        self.boat_texture.use(location=0)
        self.enemy_texture.use(location=1)
        self.program['boatTexture'].value = 0
        try:
            self.program['enemyTexture'].value = 1
        except Exception:
            pass
        # pass boat aspect ratio to shader to avoid width distortion
        try:
            self.program['boatAspect'].value = float(getattr(self, 'boat_aspect', 1.0))
        except Exception:
            pass
        try:
            self.program['enemyAspect'].value = float(getattr(self, 'enemy_aspect', 1.0))
        except Exception:
            pass

    def _create_geometry(self):
        vertices = np.array([-1.0, -1.0, 1.0, -1.0, -1.0, 1.0, 1.0, 1.0], dtype='f4')
        vbo = self.ctx.buffer(vertices.tobytes())
        self.vao = self.ctx.simple_vertex_array(self.program, vbo, 'in_vert')

    def _create_overlay_resources(self):

        overlay_vertex = '''
#version 330 core
in vec2 in_vert;
out vec2 v_uv;
void main() {
    v_uv = in_vert * 0.5 + 0.5;
    gl_Position = vec4(in_vert, 0.0, 1.0);
}
'''

        overlay_fragment = '''
#version 330 core
precision highp float;
in vec2 v_uv;
out vec4 fragColor;
uniform sampler2D overlayTexture;
void main() {
    vec4 c = texture(overlayTexture, v_uv);
    fragColor = c;
}
'''

        try:
            self.overlay_program = self.ctx.program(vertex_shader=overlay_vertex, fragment_shader=overlay_fragment)
            vertices = np.array([-1.0, -1.0, 1.0, -1.0, -1.0, 1.0, 1.0, 1.0], dtype='f4')
            vbo = self.ctx.buffer(vertices.tobytes())
            self.overlay_vao = self.ctx.simple_vertex_array(self.overlay_program, vbo, 'in_vert')
        except Exception:
            self.overlay_program = None
            self.overlay_vao = None

        self.overlay_texture = None
        # initialize pygame freetype for rendering text to surface
        try:
            pygame.freetype.init()
            # try a bundled TTF first (so DynaPuff looks identical across platforms if provided)
            font_paths = [
                # project-specific path
                os.path.join(os.path.dirname(__file__), "..", "Assets", "DynaPuff Font", "DynaPuffFont.ttf"),
                os.path.join(os.path.dirname(__file__), "..", "DynaPuffFont.ttf"),
                os.path.join(os.getcwd(), "Assets", "DynaPuff Font", "DynaPuffFont.ttf"),
                os.path.join(os.getcwd(), "DynaPuffFont.ttf"),
            ]

            found_ttf = None
            for p in font_paths:
                try:
                    if os.path.exists(p):
                        found_ttf = p
                        break
                except Exception:
                    continue

            if found_ttf:
                try:
                    self.overlay_font_large = pygame.freetype.Font(found_ttf, 63)
                    self.overlay_font_small = pygame.freetype.Font(found_ttf, 27)
                    self.nametag_font = pygame.freetype.Font(found_ttf, 18)
                    self.setting_font = pygame.freetype.Font(found_ttf, 25)
                except Exception:
                    # fallback to SysFont lookup
                    self.overlay_font_large = pygame.freetype.SysFont("DynaPuff", 63)
                    self.overlay_font_small = pygame.freetype.SysFont("DynaPuff", 27)
                    self.nametag_font = pygame.freetype.SysFont("DynaPuff", 18)
                    self.setting_font = pygame.freetype.SysFont("DynaPuff", 25)
            else:
                # prefer DynaPuff via system font name, fallback to default
                try:
                    self.overlay_font_large = pygame.freetype.SysFont("DynaPuff", 63)
                    self.overlay_font_small = pygame.freetype.SysFont("DynaPuff", 27)
                    self.nametag_font = pygame.freetype.SysFont("DynaPuff", 18)
                    self.setting_font = pygame.freetype.SysFont("DynaPuff", 25)
                except Exception:
                    self.overlay_font_large = pygame.freetype.SysFont(None, 63)
                    self.overlay_font_small = pygame.freetype.SysFont(None, 27)
                    self.nametag_font = pygame.freetype.SysFont(None, 18)
                    self.setting_font = pygame.freetype.SysFont(None, 25)
        except Exception:
            self.overlay_font_large = None
            self.overlay_font_small = None
            self.nametag_font = None
            self.setting_font = None

    def _get_overlay_surface(self):
        # return a cached fullscreen overlay surface, recreating only if size changed
        try:
            from config import WIDTH as W, HEIGHT as H
        except Exception:
            W, H = WIDTH, HEIGHT

        if self._overlay_surf is None or self._overlay_surf_size != (W, H):
            self._overlay_surf_size = (W, H)
            self._overlay_surf = pygame.Surface((W, H), pygame.SRCALPHA, 32)
            # convert surfaces once to match display format
            try:
                self._overlay_surf = self._overlay_surf.convert_alpha()
            except Exception:
                pass

        # clear surface for reuse
        self._overlay_surf.fill((0, 0, 0, 0))
        return self._overlay_surf

    def render(self, time, player, other_players_display, item_manager=None):
        from config import WORLD_WIDTH, WORLD_HEIGHT

        self.program['time'].value = float(time)
        self.program['boatPosition'].value = (float(player.x), float(player.y))
        self.program['boatRotation'].value = float(player.rotation)
        self.program['boatVelocity'].value = (float(player.velocity_x), float(player.velocity_y))
        self.program['wakeFade'].value = float(player.wake_fade)
        self.program['cameraPos'].value = (float(player.camera_x), float(player.camera_y))
        self.program['viewportSize'].value = (float(self.viewport_width), float(self.viewport_height))
        self.program['worldSize'].value = (float(WORLD_WIDTH), float(WORLD_HEIGHT))

        display_list = list(other_players_display.values())[:10]
        num_other = len(display_list)
        self.program['numOtherPlayers'].value = num_other

        pos_array = np.zeros(20, dtype='f4')
        rot_array = np.zeros(10, dtype='f4')
        speed_array = np.zeros(10, dtype='f4')
        sway_phase_array = np.zeros(10, dtype='f4')
        sway_amp_array = np.zeros(10, dtype='f4')

        for idx, e in enumerate(display_list):
            pos_array[idx * 2 + 0] = float(e['x'])
            pos_array[idx * 2 + 1] = float(e['y'])
            rot_array[idx] = float(e['rot'])
            speed_array[idx] = float(max(0.0, min(2.5, e.get('speed', 0.0))))
            sway_phase_array[idx] = float(e.get('sway_phase', 0.0))
            sway_amp_array[idx] = float(e.get('sway_amp', 1.0))

        try:
            self.program.get("otherBoatPositions").write(pos_array.tobytes())
            self.program.get("otherBoatRotations").write(rot_array.tobytes())
            self.program.get("otherBoatSpeeds").write(speed_array.tobytes())
            self.program.get("otherBoatSwayPhases").write(sway_phase_array.tobytes())
            self.program.get("otherBoatSwayAmps").write(sway_amp_array.tobytes())
        except Exception:
            try:
                self.program['otherBoatPositions'].value = tuple(pos_array.tolist())
                self.program['otherBoatRotations'].value = tuple(rot_array.tolist())
                self.program['otherBoatSpeeds'].value = tuple(speed_array.tolist())
                self.program['otherBoatSwayPhases'].value = tuple(sway_phase_array.tolist())
                self.program['otherBoatSwayAmps'].value = tuple(sway_amp_array.tolist())
            except Exception:
                pass
        if item_manager and not self.item_textures_loaded:
            self.setup_item_textures(item_manager)

            # set item uniforms
        if item_manager:
            # get items visible from camera
            visible_items = item_manager.get_visible_items(
                player.camera_x,
                player.camera_y,
                visible_radius=5.0
            )

            num_items = min(len(visible_items), 15)
            self.program['numItems'].value = num_items

            # prepare arrays
            pos_array = np.zeros(30, dtype='f4')
            type_array = np.zeros(15, dtype='i4')

            for idx, item in enumerate(visible_items[:15]):
                pos_array[idx * 2] = float(item.x)
                pos_array[idx * 2 + 1] = float(item.y)
                type_array[idx] = int(item.item_type)

            # send to shader
            try:
                self.program['itemPositions'].write(pos_array.tobytes())
                self.program['itemTypes'].write(type_array.tobytes())
            except Exception as e:
                try:
                    self.program['itemPositions'].value = tuple(pos_array.tolist())
                    self.program['itemTypes'].value = tuple(type_array.tolist())
                except Exception:
                    print(f"Could not set item uniforms: {e}")
        else:
            try:
                self.program['numItems'].value = 0
            except Exception:
                pass

        self.ctx.clear(0.0, 0.35, 0.75)
        self.vao.render(mode=moderngl.TRIANGLE_STRIP)

        if item_manager:
            visible_items = item_manager.get_visible_items(
                player.camera_x,
                player.camera_y,
                visible_radius=5.0
            )

            for item in visible_items:
                screen_x, screen_y = self.world_to_screen(
                    item.x, item.y,
                    player.camera_x, player.camera_y,
                    WIDTH, HEIGHT
                )

                if item.image:
                    # get image size
                    img_width, img_height = item.image.get_size()

                    # calculate screen size (scale based on viewport)
                    scale_factor = 80
                    draw_x = int(screen_x - img_width * scale_factor / (2 * img_width))
                    draw_y = int(screen_y - img_height * scale_factor / (2 * img_height))

    def draw_minimap(self, player, other_players_display):
        try:
            from config import WIDTH, HEIGHT, WORLD_WIDTH, WORLD_HEIGHT
        except Exception:
            WIDTH, HEIGHT = 1280, 720
            WORLD_WIDTH, WORLD_HEIGHT = 15, 15

        # create a pygame surface - SURF IS SURFACE!
        surf = self._get_overlay_surface()

        # minimap configuration
        map_size = 200
        map_margin = 20
        map_rect = pygame.Rect(map_margin, map_margin, map_size, map_size)

        # draw background
        pygame.draw.rect(surf, (50, 50, 50, 160), map_rect)
        pygame.draw.rect(surf, (200, 200, 200, 255), map_rect, 2)

        def world_to_map(wx, wy):
            # normalize coordinates 0..1, etc.
            nx = wx / WORLD_WIDTH
            ny = wy / WORLD_HEIGHT

            # map to rect
            mx = map_margin + nx * map_size
            # flip Y cause world Y is up, screen Y is down
            my = map_margin + map_size - (ny * map_size)
            return mx, my

        # draw other players (RED DOTS)
        for pid, p in other_players_display.items():
            mx, my = world_to_map(p['x'], p['y'])
            if map_rect.collidepoint(mx, my):
                pygame.draw.circle(surf, (255, 50, 50), (int(mx), int(my)), 4)

        # draw player that is playing the player-playable game (GREEN DOT)
        px, py = world_to_map(player.x, player.y)
        # clamp local player drawing to map bounds just in case
        px = max(map_rect.left + 2, min(map_rect.right - 2, px))
        py = max(map_rect.top + 2, min(map_rect.bottom - 2, py))
        pygame.draw.circle(surf, (50, 255, 50), (int(px), int(py)), 5)

        # render the overlay
        data = pygame.image.tobytes(surf, 'RGBA', True)
        w, h = surf.get_size()

        try:
            if self.overlay_texture is None:
                self.overlay_texture = self.ctx.texture((w, h), 4, data)
                self.overlay_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            else:
                self.overlay_texture.write(data)

            self.overlay_texture.use(location=2)
            if self.overlay_program:
                self.overlay_program['overlayTexture'].value = 2
                self.ctx.enable(moderngl.BLEND)
                if self.overlay_vao:
                    self.overlay_vao.render(mode=moderngl.TRIANGLE_STRIP)
        except Exception:
            pass

    def draw_overlay(self, main_text: str, sub_text: str = "", alpha: float = 1.0):
        # ensure overlay program exists
        if not getattr(self, 'overlay_program', None) or not getattr(self, 'overlay_vao', None):
            return

        # import sizes from config
        try:
            from config import WIDTH, HEIGHT
        except Exception:
            WIDTH, HEIGHT = 1280, 720

        # create an RGBA surface
        surf = self._get_overlay_surface()

        # draw semi-transparent dark background
        bg = (0, 0, 0, int(180 * alpha))
        surf.fill(bg)

        # render text
        if self.overlay_font_large:
            # center main text
            text_surf, _ = self.overlay_font_large.render(main_text, (255, 50, 50))
            tw, th = text_surf.get_size()
            surf.blit(text_surf, text_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2)))

        if sub_text and self.overlay_font_small:
            sub_surf, _ = self.overlay_font_small.render(sub_text, (230, 230, 230))
            surf.blit(sub_surf, sub_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70)))

        # upload to GPU as texture
        data = pygame.image.tobytes(surf, 'RGBA', True)
        w, h = surf.get_size()

        # create or write texture
        try:
            if self.overlay_texture is None:
                self.overlay_texture = self.ctx.texture((w, h), 4, data)
                self.overlay_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            else:
                # update existing texture
                try:
                    self.overlay_texture.write(data)
                except Exception:
                    # fallback to recreate
                    self.overlay_texture.release()
                    self.overlay_texture = self.ctx.texture((w, h), 4, data)
                    self.overlay_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)

            self.overlay_texture.use(location=2)
            try:
                self.overlay_program['overlayTexture'].value = 2
            except Exception:
                pass

            # enable blending and draw overlay quad
            self.ctx.enable(moderngl.BLEND)
            self.overlay_vao.render(mode=moderngl.TRIANGLE_STRIP)
            # leaving blending state as-is
        except Exception:
            return

    def draw_sprint_bar(self, player):
        try:
            from config import WIDTH, HEIGHT, SPRINT
        except Exception:
            WIDTH, HEIGHT = 1280, 720
            SPRINT = 100

        # create transparent surface
        surf = self._get_overlay_surface()

        # sprint bar dimensions and position
        bar_width = 200
        bar_height = 20
        x = WIDTH - bar_width - 20
        y = HEIGHT - bar_height - 20

        # draw background (empty bar)
        pygame.draw.rect(surf, (226, 140, 96, 80), (x, y, bar_width, bar_height))

        # draw foreground with color gradient based on sprint level
        sprint_frac = player.display_sprint / SPRINT  # 0.0 to 1.0
        current_width = sprint_frac * bar_width

        if current_width > 0:
            # color transitions smoothly from green (full) to red (empty)
            r = int(225 * (1.0 - sprint_frac))
            g = int(255 * sprint_frac)
            color = (r, g, 0, 220)

            pygame.draw.rect(surf, color, (x, y, current_width, bar_height))

        # add border for better visibility
        pygame.draw.rect(surf, (255, 255, 255, 100), (x, y, bar_width, bar_height), 2)

        # sprint label
        if self.nametag_font:
            try:
                label_surf, _ = self.nametag_font.render("SPRINT", (255, 255, 255))
                label_rect = label_surf.get_rect(bottomright=(x + (bar_width / 2) + 30, y + (
                            bar_height / 2) + 8))  # idk why this is the middle jus messed with it till it looked right
                surf.blit(label_surf, label_rect)
            except Exception:
                pass

        # upload to GPU and render
        data = pygame.image.tobytes(surf, 'RGBA', True)
        w, h = surf.get_size()

        try:
            if self.overlay_texture is None:
                self.overlay_texture = self.ctx.texture((w, h), 4, data)
                self.overlay_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            else:
                try:
                    self.overlay_texture.write(data)
                except Exception:
                    self.overlay_texture.release()
                    self.overlay_texture = self.ctx.texture((w, h), 4, data)
                    self.overlay_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)

            self.overlay_texture.use(location=2)
            try:
                self.overlay_program['overlayTexture'].value = 2
            except Exception:
                pass

            self.ctx.enable(moderngl.BLEND)
            self.overlay_vao.render(mode=moderngl.TRIANGLE_STRIP)
        except Exception:
            return

    def draw_player_nametags(self, player, other_players_display, names=None, y_offset=75):
        try:
            from config import WIDTH, HEIGHT
        except Exception:
            WIDTH, HEIGHT = 1280, 720

        # create transparent surface
        surf = self._get_overlay_surface()

        # helper to draw a nametag (text only) above screen position
        def draw_nametag(screen_x, screen_y, text=None):
            if not text:
                return
            font = getattr(self, 'nametag_font', None) or self.overlay_font_small
            if not font:
                return
            # position slightly higher
            pos = (int(screen_x), int(screen_y - y_offset))
            # draw shadow for readability
            try:
                shadow_surf, _ = font.render(text, (0, 0, 0))
                surf.blit(shadow_surf, shadow_surf.get_rect(center=(pos[0] + 1, pos[1] + 1)))
            except Exception:
                pass
            # draw main text in white
            try:
                txt_surf, _ = font.render(text, (255, 255, 255))
                surf.blit(txt_surf, txt_surf.get_rect(center=pos))
            except Exception:
                pass

        # draw for local player
        try:
            sx, sy = self.world_to_screen(player.x, player.y, player.camera_x, player.camera_y, WIDTH, HEIGHT)
            # local player label: if names dict provided and contains a special key 'local', use it
            local_label = None
            if isinstance(names, dict):
                local_label = names.get('local')
            draw_nametag(sx, sy, local_label or "You")
        except Exception:
            pass

        # draw for other players
        for pid, p in other_players_display.items():
            try:
                sx, sy = self.world_to_screen(p['x'], p['y'], player.camera_x, player.camera_y, WIDTH, HEIGHT)
                label = None
                if isinstance(names, dict):
                    label = names.get(pid)
                draw_nametag(sx, sy, label)
            except Exception:
                continue

        # upload to GPU as texture and render on top (reuse overlay texture logic)
        data = pygame.image.tobytes(surf, 'RGBA', True)
        w, h = surf.get_size()

        try:
            if self.overlay_texture is None:
                self.overlay_texture = self.ctx.texture((w, h), 4, data)
                self.overlay_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            else:
                try:
                    self.overlay_texture.write(data)
                except Exception:
                    self.overlay_texture.release()
                    self.overlay_texture = self.ctx.texture((w, h), 4, data)
                    self.overlay_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)

            self.overlay_texture.use(location=2)
            try:
                self.overlay_program['overlayTexture'].value = 2
            except Exception:
                pass

            self.ctx.enable(moderngl.BLEND)
            self.overlay_vao.render(mode=moderngl.TRIANGLE_STRIP)
        except Exception:
            return

    def draw_cannon_balls(self, cannon_balls, player):
        try:
            from config import WIDTH, HEIGHT
        except Exception:
            WIDTH, HEIGHT = 1280, 720

        surf = self._get_overlay_surface()

        for ball in cannon_balls:
            screen_x, screen_y = self.world_to_screen(
                ball.x, ball.y,
                player.camera_x, player.camera_y,
                WIDTH, HEIGHT
            )

            if hasattr(ball, 'image') and ball.image:
                img_rect = ball.image.get_rect()
                draw_x = int(screen_x - img_rect.width / 2)
                draw_y = int(screen_y - img_rect.height / 2)
                surf.blit(ball.image, (draw_x, draw_y))
            else:
                pygame.draw.circle(surf, (255, 255, 255), (int(screen_x), int(screen_y)), 8)

        data = pygame.image.tobytes(surf, 'RGBA', True)
        w, h = surf.get_size()

        try:
            if self.overlay_texture is None:
                self.overlay_texture = self.ctx.texture((WIDTH, HEIGHT), 4)
                self.overlay_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)

            self.overlay_texture.write(data)
            self.overlay_texture.use(location=2)

            if hasattr(self, 'overlay_program'):
                self.overlay_program['overlayTexture'].value = 2
                self.ctx.enable(moderngl.BLEND)
                if hasattr(self, 'overlay_vao'):
                    self.overlay_vao.render(mode=moderngl.TRIANGLE_STRIP)

        except Exception as e:
            print(f"Error drawing cannon balls: {e}")

    def draw_health_and_cannon_cd(self, player, left_cd_frac: float = 0.0, right_cd_frac: float = 0.0):
        try:
            from config import WIDTH, HEIGHT
        except Exception:
            WIDTH, HEIGHT = 1280, 720

        surf = self._get_overlay_surface()

        box_height = 200
        box_width = 200

        x = WIDTH - box_width - 20
        y = HEIGHT - box_height - 50

        # Box
        pygame.draw.rect(surf, (50, 50, 50, 160), (x, y, box_width, box_height))
        pygame.draw.rect(surf, (255, 255, 255, 100), (x, y, box_width, box_height), 2)

        # CD Bars visualising cooldown remaining (left_cd_frac/right_cd_frac: 1.0 = full cooldown)
        cd_bar_height = 150
        cd_bar_w = 20
        left_x = x + 20
        right_x = x + 160
        top_y = y + 25

        # draw background for both bars
        pygame.draw.rect(surf, (226, 140, 96, 80), (left_x, top_y, cd_bar_w, cd_bar_height))
        pygame.draw.rect(surf, (226, 140, 96, 80), (right_x, top_y, cd_bar_w, cd_bar_height))

        # borders

        def draw_cd_bar(base_x, frac):
            # frac in 0...1 where 1.0 means still cooling and 0.0 ready
            frac = max(0.0, min(1.0, float(frac)))
            fill_h = int((1.0 - frac) * cd_bar_height)
            fill_y = top_y + (cd_bar_height - fill_h)

            # color: green when ready, otherwise orange->red based on remaining fraction
            if frac <= 0.001:
                color = (0, 255, 0, 220)
            else:
                r = int(255 * frac)
                g = int(255 * (1.0 - frac))
                color = (r, g, 0, 220)

            if fill_h > 0:
                pygame.draw.rect(surf, color, (base_x, fill_y, cd_bar_w, fill_h))

            # draw a small label below each bar - % or ready
            try:
                label = 'READY' if frac <= 0.001 else f"{int(frac * 100)}%"
                if self.nametag_font:
                    lbl_surf, _ = self.nametag_font.render(label, (255, 255, 255))
                    surf.blit(lbl_surf, lbl_surf.get_rect(center=(base_x + cd_bar_w // 2, top_y + cd_bar_height + 14)))
            except Exception:
                pass

        draw_cd_bar(left_x, left_cd_frac)
        draw_cd_bar(right_x, right_cd_frac)

        pygame.draw.rect(surf, (255, 255, 255, 100), (left_x, top_y, cd_bar_w, cd_bar_height), 2)
        pygame.draw.rect(surf, (255, 255, 255, 100), (right_x, top_y, cd_bar_w, cd_bar_height), 2)

        data = pygame.image.tobytes(surf, 'RGBA', True)
        w, h = surf.get_size()

        # choose a preloaded health picture
        chosen_picture = self.health_images.get('green')

        try:
            if self.overlay_texture is None:
                self.overlay_texture = self.ctx.texture((w, h), 4, data)
                self.overlay_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            else:
                try:
                    self.overlay_texture.write(data)
                except Exception:
                    self.overlay_texture.release()
                    self.overlay_texture = self.ctx.texture((w, h), 4, data)
                    self.overlay_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)

            self.overlay_texture.use(location=2)
            try:
                self.overlay_program['overlayTexture'].value = 2
            except Exception:
                pass

            self.ctx.enable(moderngl.BLEND)
            self.overlay_vao.render(mode=moderngl.TRIANGLE_STRIP)
        except Exception:
            return

    def escape_menu(self, player):
        try:
            from config import WIDTH, HEIGHT
        except Exception:
            WIDTH, HEIGHT = 1280, 720

        surf = self._get_overlay_surface()

        xcor = WIDTH
        ycor = HEIGHT

        list_of_buttons = ["Menu", "Settings", "Cancel"]
        settings_image = pygame.image.load("../Logos/logo-borderless.png").convert_alpha()
        resized_image = pygame.transform.smoothscale(settings_image, (350, 350))
        menu_rect = surf.get_rect(center=(WIDTH // 1.17, HEIGHT // 2.25))

        if self.overlay_font_large:
            try:
                surf.blit(resized_image, menu_rect)
            except Exception:
                pass

        for i in range(len(list_of_buttons)):
            if self.setting_font:
                try:

                    shadow_surf, _ = self.setting_font.render(list_of_buttons[i], (0, 0, 0))
                    shadow_rect = shadow_surf.get_rect(center=(xcor // 2 + 2, ycor // 2 - i * 40 + 2))
                    surf.blit(shadow_surf, shadow_rect)
                    label_surf, _ = self.setting_font.render(list_of_buttons[i], (255, 255, 255))
                    label_rect = label_surf.get_rect(center=(xcor // 2, ycor // 2 - i * 40))
                    surf.blit(label_surf, label_rect)
                except Exception:
                    pass

        data = pygame.image.tobytes(surf, 'RGBA', True)
        w, h = surf.get_size()

        try:
            if self.overlay_texture is None:
                self.overlay_texture = self.ctx.texture((w, h), 4, data)
                self.overlay_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)
            else:
                try:
                    self.overlay_texture.write(data)
                except Exception:
                    self.overlay_texture.release()
                    self.overlay_texture = self.ctx.texture((w, h), 4, data)
                    self.overlay_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)

            self.overlay_texture.use(location=2)
            try:
                self.overlay_program['overlayTexture'].value = 2
            except Exception:
                pass

            self.ctx.enable(moderngl.BLEND)
            self.overlay_vao.render(mode=moderngl.TRIANGLE_STRIP)
        except Exception:
            return


