import math, random, sys, time, json, os
from datetime import datetime
import pygame

# =======================
# CONFIG
# =======================
WINDOW_W, WINDOW_H = 960, 600
GAME_DURATION_SEC = 30

TITLE   = "Joy Bloom"
VERSION = "v1.3"
EDITOR  = "By Joy"

SCORES_FILE = "highscores.json"

# File names (optional; the game won't crash if missing)
CLICK_SOUND     = "Game/click.wav"
POP_SOUND       = "Game/pop.wav"
BGM             = "Game/bgm.mp3"
BACKGROUND_IMG  = "Game/flower_field.png"   # pixel art 960x600 (optional)

# Colors
UI_FG       = (255, 255, 255)
UI_DIM      = (200, 200, 200)
BG_MENU     = (20, 22, 28)
GOLD        = (255, 215, 0)
SILVER      = (192, 192, 192)

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

def load_scores():
    """Load high score and recent scores list."""
    try:
        if os.path.exists(SCORES_FILE):
            with open(SCORES_FILE, "r") as f:
                data = json.load(f)
                highscore = data.get("highscore", 0)
                recent_scores = data.get("recent_scores", [])
                return int(highscore), recent_scores
    except Exception:
        pass
    return 0, []

def save_score(score: int):
    """Save a new score, update high score if needed, maintain recent scores list."""
    try:
        current_high, recent_scores = load_scores()
        
        # Add new score with timestamp
        score_entry = {
            "score": int(score),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        recent_scores.append(score_entry)
        
        # Keep only last 10 scores
        recent_scores = recent_scores[-10:]
        
        # Update high score if needed
        new_high = max(current_high, int(score))
        
        # Save back to file
        data = {
            "highscore": new_high,
            "recent_scores": recent_scores
        }
        with open(SCORES_FILE, "w") as f:
            json.dump(data, f, indent=2)
            
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
        self.font       = pygame.font.SysFont("arial", 24)
        self.small_font = pygame.font.SysFont("arial", 18)
        self.big_font   = pygame.font.SysFont("arial", 48, bold=True)

        # State
        self.state      = MENU
        self.score      = 0
        self.highscore, self.recent_scores = load_scores()
        self.flowers    = []  # reused for menu floaters or gameplay flowers
        self.particles  = []
        self.start_time = 0.0
        self.pause_time = 0.0  # Track cumulative pause time
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
                    if e.key == pygame.K_ESCAPE:
                        if self.state in (SETTINGS, SCORES, CREDITS, PAUSED):
                            self.state = MENU if self.state != PAUSED else GAME
                            self.play_sound(self.click_snd)
                    elif self.state == GAME and e.key == pygame.K_p:
                        self.toggle_pause()
                    elif self.state == PAUSED and e.key in (pygame.K_p, pygame.K_SPACE, pygame.K_RETURN):
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
            self.pause_start = time.time()
        elif self.state == PAUSED:
            self.state = GAME
            # Add the pause duration to our total pause time
            self.pause_time += time.time() - self.pause_start

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
        self.pause_time = 0.0

    def get_elapsed_game_time(self):
        """Get elapsed game time, excluding pause time."""
        current_time = time.time()
        if self.state == PAUSED:
            # Don't count current pause session
            return (self.pause_start - self.start_time) - self.pause_time
        else:
            return (current_time - self.start_time) - self.pause_time

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
            elapsed = self.get_elapsed_game_time()
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
                save_score(self.score)
                self.highscore, self.recent_scores = load_scores()

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
            elif self.button_rect("Settings", y0 + 60).collidepoint(pos): self.state = SETTINGS
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

        elif self.state == PAUSED:
            # Click anywhere to unpause, or use keys
            self.toggle_pause()

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
        # Distant "pixels" for a field
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
        elapsed   = self.get_elapsed_game_time()
        time_left = max(0, int(GAME_DURATION_SEC - elapsed))
        mm, ss    = divmod(time_left, 60)
        score_s   = self.font.render(f"Score: {self.score}", True, UI_FG)
        time_s    = self.font.render(f"Time: {mm}:{ss:02d}", True, UI_FG)
        self.screen.blit(score_s, (10, 10))
        self.screen.blit(time_s,  (WINDOW_W - time_s.get_width() - 10, 10))
        # Pause hint
        hint = self.small_font.render("Press P to Pause", True, UI_DIM)
        self.screen.blit(hint, (10, 38))

    def draw(self):
        self.draw_background()

        if self.state == MENU:
            # Title
            title = self.big_font.render(TITLE, True, UI_FG)
            self.screen.blit(title, (WINDOW_W // 2 - title.get_width() // 2, 100))
            y0 = WINDOW_H // 2 - 100
            self.draw_button("Play",        y0)
            self.draw_button("Settings",    y0 + 60)
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
            
            # Pause text and instructions
            txt = self.big_font.render("Paused", True, UI_FG)
            self.screen.blit(txt, (WINDOW_W // 2 - txt.get_width() // 2, WINDOW_H // 2 - 80))
            
            instructions = [
                "Press P, SPACE, or ENTER to continue",
                "Click anywhere to unpause",
                "Press ESC to return to menu"
            ]
            
            for i, instruction in enumerate(instructions):
                inst_text = self.small_font.render(instruction, True, UI_DIM)
                self.screen.blit(inst_text, (WINDOW_W // 2 - inst_text.get_width() // 2, WINDOW_H // 2 - 20 + i * 25))

        elif self.state == GAME_OVER:
            over = self.big_font.render("Time's Up!", True, UI_FG)
            self.screen.blit(over, (WINDOW_W // 2 - over.get_width() // 2, 180))
            final = self.font.render(f"Final Score: {self.score}", True, (230, 230, 230))
            self.screen.blit(final, (WINDOW_W // 2 - final.get_width() // 2, 250))
            
            # Show if it's a new high score
            if self.score == self.highscore and self.score > 0:
                new_high_text = self.font.render("New High Score!", True, GOLD)
                self.screen.blit(new_high_text, (WINDOW_W // 2 - new_high_text.get_width() // 2, 285))
            else:
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
            
            # Instructions
            esc_hint = self.small_font.render("Press ESC to go back", True, UI_DIM)
            self.screen.blit(esc_hint, (10, WINDOW_H - 60))

        elif self.state == SCORES:
            txt = self.big_font.render("Scores", True, UI_FG)
            self.screen.blit(txt, (WINDOW_W // 2 - txt.get_width() // 2, 80))
            
            # Personal Best
            pb_label = self.font.render("Personal Best:", True, UI_FG)
            self.screen.blit(pb_label, (WINDOW_W // 2 - pb_label.get_width() // 2, 140))
            
            pb_score = self.font.render(f"{self.highscore}", True, GOLD)
            self.screen.blit(pb_score, (WINDOW_W // 2 - pb_score.get_width() // 2, 170))
            
            # Recent Scores
            if self.recent_scores:
                recent_label = self.font.render("Recent Scores:", True, UI_FG)
                self.screen.blit(recent_label, (WINDOW_W // 2 - recent_label.get_width() // 2, 220))
                
                y_offset = 250
                # Show recent scores in reverse order (newest first)
                for i, score_data in enumerate(reversed(self.recent_scores)):
                    if i >= 8:  # Limit display to 8 recent scores to fit on screen
                        break
                    
                    score_val = score_data["score"]
                    date_str = score_data["date"]
                    
                    # Use gold for high scores, silver for good scores, white for others
                    if score_val == self.highscore:
                        color = GOLD
                    elif score_val >= self.highscore * 0.8:
                        color = SILVER
                    else:
                        color = (230, 230, 230)
                    
                    score_text = f"{score_val:3d}  -  {date_str}"
                    score_surface = self.small_font.render(score_text, True, color)
                    self.screen.blit(score_surface, (WINDOW_W // 2 - score_surface.get_width() // 2, y_offset))
                    y_offset += 22
            else:
                no_scores = self.font.render("No recent scores yet!", True, UI_DIM)
                self.screen.blit(no_scores, (WINDOW_W // 2 - no_scores.get_width() // 2, 250))
            
            self.draw_button("Back", WINDOW_H - 80)
            
            # Instructions
            esc_hint = self.small_font.render("Press ESC to go back", True, UI_DIM)
            self.screen.blit(esc_hint, (10, WINDOW_H - 60))

        elif self.state == CREDITS:
            txt = self.big_font.render("Credits", True, UI_FG)
            self.screen.blit(txt, (WINDOW_W // 2 - txt.get_width() // 2, 140))
            c1  = self.font.render("Made with Joy", True, (220, 220, 220))
            c2  = self.font.render("Python + Pygame", True, (220, 220, 220))
            c3  = self.small_font.render("Enhanced with improved pause system", True, UI_DIM)
            c4  = self.small_font.render("and detailed score tracking", True, UI_DIM)
            
            self.screen.blit(c1, (WINDOW_W // 2 - c1.get_width() // 2, 230))
            self.screen.blit(c2, (WINDOW_W // 2 - c2.get_width() // 2, 260))
            self.screen.blit(c3, (WINDOW_W // 2 - c3.get_width() // 2, 290))
            self.screen.blit(c4, (WINDOW_W // 2 - c4.get_width() // 2, 310))
            
            self.draw_button("Back", WINDOW_H - 80)
            
            # Instructions
            esc_hint = self.small_font.render("Press ESC to go back", True, UI_DIM)
            self.screen.blit(esc_hint, (10, WINDOW_H - 60))

        pygame.display.flip()

# ------------- Entry -------------
if __name__ == "__main__":
    Game().run()