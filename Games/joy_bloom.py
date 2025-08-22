import math
import random
import sys
import time
import webbrowser

import pygame

# =======================
# CONFIG — EDIT THESE
# =======================
WINDOW_W, WINDOW_H = 960, 600
GAME_DURATION_SEC = 120  # 2 minutes
BACKGROUND_COLOR = (20, 22, 28)   # dark slate
HUD_COLOR = (240, 240, 240)
FLOWER_BASE_COLOR = (255, 183, 197)  # pastel pink
FLOWER_VARIANTS = [
    (255, 183, 197),  # pink
    (255, 221, 148),  # peach
    (182, 255, 182),  # mint
    (173, 216, 255),  # light blue
    (220, 200, 255),  # lavender
]
MIN_FLOWER_SIZE, MAX_FLOWER_SIZE = 14, 26  # "pixel" units (scaled up squares)
SPAWN_EVERY_MIN, SPAWN_EVERY_MAX = 250, 550  # ms between spawns (will scale down over time)
MAX_FLOWERS_ON_SCREEN = 100

# URLs to open on finish
RICKROLL_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
YOUR_URL = "https://15gay.itch.io"  # <- put your site or game page here

TITLE = "Joy Blooms"

# =======================
# GAME OBJECTS
# =======================

class Flower:
    def __init__(self, x, y, size, color):
        # size is the base pixel cell size (each petal is one cell)
        self.x = x
        self.y = y
        self.size = size
        self.color = color

        # gentle drift
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(0.1, 0.35)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed

        # wobble motion
        self.wobble_t = random.uniform(0, 1000)
        self.wobble_speed = random.uniform(0.01, 0.03)
        self.wobble_amp = random.uniform(0.5, 2.0)

        # "pixel" layout: plus shape (center + 4 petals)
        self.pixel_coords = [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)]
        # expand clickable rect to cover the plus shape
        extent = self.size * 3
        self.rect = pygame.Rect(self.x - extent / 2, self.y - extent / 2, extent, extent)

        # pop animation
        self.popping = False
        self.pop_t = 0.0

    def update(self, dt):
        if self.popping:
            self.pop_t += dt
            return

        self.wobble_t += self.wobble_speed
        wobble_x = math.sin(self.wobble_t) * self.wobble_amp
        wobble_y = math.cos(self.wobble_t * 0.8) * self.wobble_amp

        self.x += (self.vx + wobble_x * 0.02) * (dt * 60)
        self.y += (self.vy + wobble_y * 0.02) * (dt * 60)

        # bounce off edges softly
        margin = self.size * 2
        if self.x < margin or self.x > WINDOW_W - margin:
            self.vx *= -1
        if self.y < margin or self.y > WINDOW_H - margin:
            self.vy *= -1

        extent = self.size * 3
        self.rect.x = self.x - extent / 2
        self.rect.y = self.y - extent / 2

    def draw(self, surf):
        if self.popping:
            # scale up and fade out
            t = min(self.pop_t / 0.25, 1.0)
            scale = 1.0 + t * 1.2
            alpha = max(0, 255 - int(t * 255))
            self._draw_pixels(surf, scale=scale, alpha=alpha)
        else:
            self._draw_pixels(surf, scale=1.0, alpha=255)

    def _draw_pixels(self, surf, scale=1.0, alpha=255):
        # outline/bg darker color
        base = pygame.Color(*self.color)
        outline = pygame.Color(int(base.r * 0.6), int(base.g * 0.6), int(base.b * 0.6))
        center_color = pygame.Color(*self.color)
        center_color.g = min(255, center_color.g + 15)
        center_color.b = min(255, center_color.b + 15)

        s = max(2, int(self.size * scale))
        for (px, py) in self.pixel_coords:
            # shadow/outline offset
            ox = int(self.x + px * s - s / 2 + 2 * scale)
            oy = int(self.y + py * s - s / 2 + 2 * scale)
            rect_o = pygame.Rect(ox, oy, s, s)
            pygame.draw.rect(surf, outline, rect_o)

            # petal
            cx = int(self.x + px * s - s / 2)
            cy = int(self.y + py * s - s / 2)
            rect = pygame.Rect(cx, cy, s, s)

            # use a surface to control alpha
            petal = pygame.Surface((s, s), pygame.SRCALPHA)
            petal.fill((*self.color, alpha))
            surf.blit(petal, rect.topleft)

        # little yellow center
        center_size = int(s * 0.6)
        center = pygame.Surface((center_size, center_size), pygame.SRCALPHA)
        center.fill((250, 240, 150, alpha))
        surf.blit(center, (int(self.x - center_size / 2), int(self.y - center_size / 2)))

    def contains_point(self, pos):
        return self.rect.collidepoint(pos)

    def pop(self):
        self.popping = True
        self.pop_t = 0.0


def draw_hud(surf, font, score, time_left):
    pygame.draw.rect(surf, (0, 0, 0, 80), pygame.Rect(0, 0, WINDOW_W, 40))
    # time mm:ss
    mm = int(time_left) // 60
    ss = int(time_left) % 60
    time_txt = f"{mm:01d}:{ss:02d}"
    score_surf = font.render(f"Score: {score}", True, HUD_COLOR)
    time_surf = font.render(f"Time: {time_txt}", True, HUD_COLOR)

    surf.blit(score_surf, (12, 8))
    surf.blit(time_surf, (WINDOW_W - time_surf.get_width() - 12, 8))


def main():
    pygame.init()
    pygame.display.set_caption(TITLE)
    screen = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 22, bold=True)
    big_font = pygame.font.SysFont("arial", 48, bold=True)

    score = 0
    flowers = []
    start_time = time.time()
    time_left = GAME_DURATION_SEC

    # spawn pacing
    last_spawn = 0
    next_spawn_ms = random.randint(SPAWN_EVERY_MIN, SPAWN_EVERY_MAX)

    running = True
    game_over = False
    game_over_t = 0.0

    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and not game_over:
                pos = event.pos
                # click from topmost first
                for i in range(len(flowers) - 1, -1, -1):
                    f = flowers[i]
                    if not f.popping and f.contains_point(pos):
                        f.pop()
                        score += 1
                        break

        screen.fill(BACKGROUND_COLOR)

        # time
        if not game_over:
            elapsed = time.time() - start_time
            time_left = max(0.0, GAME_DURATION_SEC - elapsed)

            # spawn logic scales up over time (faster spawns)
            if len(flowers) < MAX_FLOWERS_ON_SCREEN:
                last_spawn += dt * 1000.0
                difficulty = 1.0 + (elapsed / GAME_DURATION_SEC) * 1.5
                target_interval = max(120, next_spawn_ms / difficulty)
                if last_spawn >= target_interval:
                    last_spawn = 0
                    next_spawn_ms = random.randint(SPAWN_EVERY_MIN, SPAWN_EVERY_MAX)

                    size = random.randint(MIN_FLOWER_SIZE, MAX_FLOWER_SIZE)
                    color = random.choice(FLOWER_VARIANTS)
                    x = random.randint(size * 3, WINDOW_W - size * 3)
                    y = random.randint(40 + size * 3, WINDOW_H - size * 3)
                    flowers.append(Flower(x, y, size, color))

            # update flowers
            for f in flowers:
                f.update(dt)

            # remove finished pops
            flowers = [f for f in flowers if not (f.popping and f.pop_t >= 0.25)]

            # end condition
            if time_left <= 0.0:
                game_over = True
                game_over_t = 0.0

        else:
            # simple end card
            game_over_t += dt
            over_text = big_font.render("Time!", True, (255, 255, 255))
            screen.blit(over_text, (WINDOW_W // 2 - over_text.get_width() // 2,
                                    WINDOW_H // 2 - over_text.get_height() // 2 - 20))

            fin_text = font.render(f"Final Score: {score}", True, (220, 220, 220))
            screen.blit(fin_text, (WINDOW_W // 2 - fin_text.get_width() // 2,
                                   WINDOW_H // 2 + 20))

            # after short pause, open links and exit
            if game_over_t > 1.0:
                try:
                    webbrowser.open(RICKROLL_URL, new=2)
                except Exception:
                    pass
                if YOUR_URL and YOUR_URL.strip() != "https://15gay.itch.io":
                    try:
                        webbrowser.open(YOUR_URL, new=2)
                    except Exception:
                        pass
                pygame.quit()
                sys.exit(0)

        # draw
        for f in flowers:
            f.draw(screen)
        draw_hud(screen, font, score, time_left)

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
