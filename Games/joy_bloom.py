import math, random, sys, time, json, os
import pygame

# =======================
# CONFIG
# =======================
WINDOW_W, WINDOW_H = 960, 600
GAME_DURATION_SEC = 120

TITLE   = "Joy Bloom"
VERSION = "v1.2"
EDITOR  = "By Joy"

SCORES_FILE = "highscores.json"

# File names (optional; the game won’t crash if missing)
CLICK_SOUND     = "Game/click.wav"
POP_SOUND       = "Game/pop.wav"
BGM             = "Game/bgm.mp3"
BACKGROUND_IMG  = "Game/flower_field.png"   # pixel art 960x600 (optional)

# Colors
UI_FG       = (255, 255, 255)
UI_DIM      = (200, 200, 200)
BG_MENU     = (20, 22, 28)
GOLD        = (255, 215, 0)

# Flower palette
FLOWER_COLS = [
    (255, 183, 197),  # pink
    (255, 221, 148),  # peach
    (182, 255, 182),  # mint
    (173, 216, 255),  # light blue
    (220, 200, 255),  # lavender
]

# =======================
# UTILS
# =======================
def resource_path(rel_path: str) -> str:
    """Works both in development and when bundled with PyInstaller."""
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, rel_path)

def safe_load_image(filename: str):
    path = resource_path(filename)
    if os.path.exists(path):
        try:
            return pygame.image.load(path).convert()
        except pygame.error:
            return None
    return None

def safe_mixer_init():
    try:
        pygame.mixer.init()
        return True
    except pygame.error:
        return False

def safe_load_sound(filename: str, audio_ok: bool):
    if not audio_ok:
        return None
    path = resource_path(filename)
    if os.path.exists(path):
        try:
            return pygame.mixer.Sound(path)
        except pygame.error:
            return None
    return None

def safe_load_music(filename: str, audio_ok: bool):
    if not audio_ok:
        return False
    path = resource_path(filename)
    if os.path.exists(path):
        try:
            pygame.mixer.music.load(path)
            return True
        except pygame.error:
            return False
    return False

def load_highscore():
    try:
        if os.path.exists(SCORES_FILE):
            with open(SCORES_FILE, "r") as f:
                return int(json.load(f).get("highscore", 0))
    except Exception:
        pass
    return 0

def save_highscore(score: int):
    try:
        current = load_highscore()
        if score > current:
            with open(SCORES_FILE, "w") as f:
                json.dump({"highscore": int(score)}, f)
    except Exception:
        pass

# =======================
# PARTICLES
# =======================
class Particle:
    def __init__(self, x, y, color):
        self.x, self.y = float(x), float(y)
        self.vx = random.uniform(-2.2, 2.2)
        self.vy = random.uniform(-3.0, -1.2)
        self.life = 0.55
        self.color = color
        self.size = random.randint(2, 4)

    def update(self, dt):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.18   # gravity
        self.life -= dt

    def draw(self, surf):
        if self.life > 0:
            pygame.draw.rect(surf, self.color, (int(self.x), int(self.y), self.size, self.size))

# =======================
# FLOWER
# =======================
class Flower:
    def __init__(self, x, y, size, color):
        self.x, self.y = float(x), float(y)
        self.size  = size
        self.color = color
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(0.1, 0.35)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.pixel_coords = [(0,0),(1,0),(-1,0),(0,1),(0,-1)]
        extent = self.size * 3
        self.rect = pygame.Rect(self.x - extent/2, self.y - extent/2, extent, extent)

    def update(self, dt, bounds):
        self.x += self.vx * dt * 60
        self.y += self.vy * dt * 60
        left, top, right, bottom = bounds
        if self.x < left or self.x > right:  self.vx *= -1
        if self.y < top  or self.y > bottom: self.vy *= -1
        extent = self.size * 3
        self.rect.x = int(self.x - extent/2)
        self.rect.y = int(self.y - extent/2)

    def draw(self, surf):
        s = max(2, int(self.size))
        for (px, py) in self.pixel_coords:
            rect = pygame.Rect(int(self.x + px*s - s/2), int(self.y + py*s - s/2), s, s)
            pygame.draw.rect(surf, self.color, rect)
            pygame.draw.rect(surf, (60,60,60), rect, 1)
        cs = int(s * 0.6)
        c_rect = pygame.Rect(int(self.x - cs/2), int(self.y - cs/2), cs, cs)
        pygame.draw.rect(surf, (250,240,150), c_rect)

    def contains_point(self, pos):
        return self.rect.collidepoint(pos)

# =======================
# SCENES
# =======================
MENU, GAME, GAME_OVER, SETTINGS, SCORES, CREDITS, PAUSED = range(7)

class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption(TITLE)

        # Try audio; if it fails, keep running silently
        self.audio_ok = safe_mixer_init()

        # Window
        self.fullscreen = False
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))

        # Fonts
        self.font     = pygame.font.SysFont("arial", 24)
        self.big_font = pygame.font.SysFont("arial", 48, bold=True)

        # State
        self.state      = MENU
        self.score      = 0
        self.highscore  = load_highscore()
        self.flowers    = []  # reused for menu floaters or gameplay flowers
        self.particles  = []
        self.start_time = 0.0
        self.sound_on   = True
        self.music_on   = True

        # Assets (safe)
        self.click_snd  = safe_load_sound(CLICK_SOUND, self.audio_ok)
        self.pop_snd    = safe_load_sound(POP_SOUND,   self.audio_ok)
        self.music_loaded = safe_load_music(BGM, self.audio_ok)
        if self.music_loaded and self.music_on:
            try:
                pygame.mixer.music.play(-1)
            except pygame.error:
                self.music_loaded = False

        self.bg_image = safe_load_image(BACKGROUND_IMG)  # may be None

    # ------------- Core loop -------------
    def run(self):
        clock = pygame.time.Clock()
        while True:
            dt = clock.tick(60) / 1000.0
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if e.type == pygame.KEYDOWN:
                    if self.state == GAME and e.key == pygame.K_p:
                        self.toggle_pause()
                if e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    self.handle_click(e.pos)

            self.update(dt)
            self.draw()

    # ------------- Helpers -------------
    def toggle_pause(self):
        self.play_sound(self.click_snd)
        if self.state == GAME:
            self.state = PAUSED
        elif self.state == PAUSED:
            self.state = GAME

    def play_sound(self, snd):
        if self.audio_ok and self.sound_on and snd is not None:
            try:
                snd.play()
            except pygame.error:
                pass

    def set_fullscreen(self, enable: bool):
        self.fullscreen = enable
        flags = pygame.FULLSCREEN if enable else 0
        self.screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), flags)

    def start_game(self):
        self.state = GAME
        self.score = 0
        self.flowers = []
        self.particles = []
        self.start_time = time.time()

    def button_rect(self, label: str, center_y: int):
        # Return the clickable rect (inflated) so visual & hitbox match
        text_surf = self.font.render(label, True, UI_FG)
        rect = text_surf.get_rect(center=(WINDOW_W // 2, center_y))
        return rect.inflate(24, 12)

    def draw_button(self, label: str, center_y: int):
        rect = self.button_rect(label, center_y)
        pygame.draw.rect(self.screen, (80, 80, 80), rect, border_radius=8)
        text_surf = self.font.render(label, True, UI_FG)
        self.screen.blit(
            text_surf,
            text_surf.get_rect(center=rect.center)
        )
        return rect

    # ------------- Update / Draw per state -------------
    def update(self, dt):
        if self.state == GAME:
            elapsed = time.time() - self.start_time
            time_left = max(0.0, GAME_DURATION_SEC - elapsed)

            # Spawn flowers (cap)
            if random.random() < 0.035 and len(self.flowers) < 60:
                size = random.randint(14, 26)
                color = random.choice(FLOWER_COLS)
                x = random.randint(40, WINDOW_W - 40)
                y = random.randint(80, WINDOW_H - 40)
                self.flowers.append(Flower(x, y, size, color))

            # Update flowers within bounds (leave HUD zone at top)
            bounds = (20, 70, WINDOW_W - 20, WINDOW_H - 20)
            for f in self.flowers:
                f.update(dt, bounds)

            # Update particles
            for p in self.particles:
                p.update(dt)
            self.particles = [p for p in self.particles if p.life > 0]

            # End game
            if time_left <= 0:
                self.state = GAME_OVER
                save_highscore(self.score)
                self.highscore = load_highscore()

        elif self.state == MENU:
            # Floating decorative flowers
            if random.random() < 0.02 and len(self.flowers) < 20:
                size = random.randint(10, 18)
                color = random.choice(FLOWER_COLS)
                x = random.randint(40, WINDOW_W - 40)
                y = random.randint(80, WINDOW_H - 40)
                self.flowers.append(Flower(x, y, size, color))

            bounds = (20, 70, WINDOW_W - 20, WINDOW_H - 20)
            for f in self.flowers:
                f.update(dt, bounds)

        elif self.state == PAUSED:
            pass  # freeze everything

    def handle_click(self, pos):
        if self.state == MENU:
            self.play_sound(self.click_snd)
            y0 = WINDOW_H // 2 - 100
            if self.button_rect("Play", y0).collidepoint(pos):            self.start_game()
           # elif self.button_rect("Settings", y0 + 60).collidepoint(pos): self.state = SETTINGS
            elif self.button_rect("High Scores", y0 + 120).collidepoint(pos): self.state = SCORES
            elif self.button_rect("Credits", y0 + 180).collidepoint(pos): self.state = CREDITS

        elif self.state == GAME:
            # Pop topmost flower first
            for f in reversed(self.flowers):
                if f.contains_point(pos):
                    self.score += 1
                    self.play_sound(self.pop_snd)
                    for _ in range(12):
                        self.particles.append(Particle(pos[0], pos[1], f.color))
                    self.flowers.remove(f)
                    break

        elif self.state == GAME_OVER:
            self.play_sound(self.click_snd)
            if self.button_rect("Play Again", WINDOW_H // 2 + 40).collidepoint(pos):
                self.start_game()
            elif self.button_rect("Main Menu", WINDOW_H // 2 + 100).collidepoint(pos):
                self.state = MENU

        elif self.state in (SETTINGS, SCORES, CREDITS):
            if self.state == SETTINGS:
                # Toggles
                if self.button_rect(self.music_label(), 200).collidepoint(pos):
                    self.music_on = not self.music_on
                    if self.audio_ok and self.music_loaded:
                        try:
                            if self.music_on: pygame.mixer.music.play(-1)
                            else: pygame.mixer.music.stop()
                        except pygame.error:
                            pass
                    self.play_sound(self.click_snd)

                elif self.button_rect(self.sound_label(), 260).collidepoint(pos):
                    self.sound_on = not self.sound_on
                    # play a click if we just turned it on (feedback)
                    if self.sound_on: self.play_sound(self.click_snd)

                elif self.button_rect(self.fullscreen_label(), 320).collidepoint(pos):
                    self.set_fullscreen(not self.fullscreen)
                    self.play_sound(self.click_snd)

            # Back button (shared)
            if self.button_rect("Back", WINDOW_H - 80).collidepoint(pos):
                self.play_sound(self.click_snd)
                self.state = MENU

    # Labels that reflect current state
    def music_label(self):     return f"Music: {'On' if self.music_on else 'Off'}"
    def sound_label(self):     return f"Sound: {'On' if self.sound_on else 'Off'}"
    def fullscreen_label(self):return f"Fullscreen: {'On' if self.fullscreen else 'Off'}"

    # ----- Drawing helpers -----
    def draw_generated_background(self):
        # Simple sky + ground + dotted flowers if no image asset present
        # Sky
        self.screen.fill((120, 180, 255))
        pygame.draw.rect(self.screen, (110, 200, 110), (0, WINDOW_H // 2, WINDOW_W, WINDOW_H // 2))
        # Distant “pixels” for a field
        for _ in range(220):
            x = random.randint(0, WINDOW_W - 1)
            y = random.randint(WINDOW_H // 2 + 10, WINDOW_H - 10)
            col = random.choice(FLOWER_COLS)
            pygame.draw.rect(self.screen, col, (x, y, 2, 2))

    def draw_background(self):
        # In GAME: show pixel field (image if available, else generated)
        if self.state == GAME:
            if self.bg_image:
                self.screen.blit(self.bg_image, (0, 0))
            else:
                self.draw_generated_background()
        else:
            # Menu/Other states: dark background for contrast
            self.screen.fill(BG_MENU)

    def draw_hud_timer_score(self):
        elapsed   = time.time() - self.start_time
        time_left = max(0, int(GAME_DURATION_SEC - elapsed))
        mm, ss    = divmod(time_left, 60)
        score_s   = self.font.render(f"Score: {self.score}", True, UI_FG)
        time_s    = self.font.render(f"Time: {mm}:{ss:02d}", True, UI_FG)
        self.screen.blit(score_s, (10, 10))
        self.screen.blit(time_s,  (WINDOW_W - time_s.get_width() - 10, 10))
        # Pause hint
        hint = self.font.render("Press P to Pause", True, UI_DIM)
        self.screen.blit(hint, (10, 38))

    def draw(self):
        self.draw_background()

        if self.state == MENU:
            # Title
            title = self.big_font.render(TITLE, True, UI_FG)
            self.screen.blit(title, (WINDOW_W // 2 - title.get_width() // 2, 100))
            y0 = WINDOW_H // 2 - 100
            self.draw_button("Play",        y0)
           # self.draw_button("Settings",    y0 + 60)
            self.draw_button("High Scores", y0 + 120)
            self.draw_button("Credits",     y0 + 180)
            # Footer
            footer = self.font.render(f"{VERSION} | {EDITOR}", True, UI_DIM)
            self.screen.blit(footer, (10, WINDOW_H - 30))
            # Decorative flowers
            for f in self.flowers:
                f.draw(self.screen)

        elif self.state == GAME:
            for f in self.flowers:
                f.draw(self.screen)
            for p in self.particles:
                p.draw(self.screen)
            self.draw_hud_timer_score()

        elif self.state == PAUSED:
            # Draw the gameplay behind (frozen), then overlay
            for f in self.flowers:
                f.draw(self.screen)
            for p in self.particles:
                p.draw(self.screen)
            self.draw_hud_timer_score()
            overlay = pygame.Surface((WINDOW_W, WINDOW_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            self.screen.blit(overlay, (0, 0))
            txt = self.big_font.render("Paused", True, UI_FG)
            self.screen.blit(txt, (WINDOW_W // 2 - txt.get_width() // 2, WINDOW_H // 2 - txt.get_height() // 2))

        elif self.state == GAME_OVER:
            over = self.big_font.render("Time!", True, UI_FG)
            self.screen.blit(over, (WINDOW_W // 2 - over.get_width() // 2, 180))
            final = self.font.render(f"Final Score: {self.score}", True, (230, 230, 230))
            self.screen.blit(final, (WINDOW_W // 2 - final.get_width() // 2, 250))
            hs = self.font.render(f"High Score: {self.highscore}", True, GOLD)
            self.screen.blit(hs, (WINDOW_W // 2 - hs.get_width() // 2, 285))
            self.draw_button("Play Again", WINDOW_H // 2 + 40)
            self.draw_button("Main Menu",  WINDOW_H // 2 + 100)

        elif self.state == SETTINGS:
            txt = self.big_font.render("Settings", True, UI_FG)
            self.screen.blit(txt, (WINDOW_W // 2 - txt.get_width() // 2, 100))
            self.draw_button(self.music_label(),      200)
            self.draw_button(self.sound_label(),      260)
            self.draw_button(self.fullscreen_label(), 320)
            self.draw_button("Back",                  WINDOW_H - 80)

        elif self.state == SCORES:
            txt = self.big_font.render("High Scores", True, UI_FG)
            self.screen.blit(txt, (WINDOW_W // 2 - txt.get_width() // 2, 140))
            hs = self.font.render(f"High Score: {self.highscore}", True, GOLD)
            self.screen.blit(hs, (WINDOW_W // 2 - hs.get_width() // 2, 240))
            final = self.font.render(f"Last Score: {self.score}", True, (230, 230, 230))
            self.screen.blit(final, (WINDOW_W // 2 - final.get_width() // 2, 290))
            self.draw_button("Back", WINDOW_H - 80)

        elif self.state == CREDITS:
            txt = self.big_font.render("Credits", True, UI_FG)
            self.screen.blit(txt, (WINDOW_W // 2 - txt.get_width() // 2, 140))
            c1  = self.font.render("Made with Joy", True, (220, 220, 220))
            c2  = self.font.render("Python + Pygame", True, (220, 220, 220))
            self.screen.blit(c1, (WINDOW_W // 2 - c1.get_width() // 2, 230))
            self.screen.blit(c2, (WINDOW_W // 2 - c2.get_width() // 2, 260))
            self.draw_button("Back", WINDOW_H - 80)

        pygame.display.flip()

# ------------- Entry -------------
if __name__ == "__main__":
    Game().run()
