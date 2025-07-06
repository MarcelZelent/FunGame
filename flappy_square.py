#!/usr/bin/env python3
"""
Flappy‑Square – a minimal but addictive Pygame arcade game.

Controls
--------
Spacebar / ↑ arrow : “flap” (give the square an upward impulse)
Esc or Q           : quit

Goal
----
Survive as long as possible and fly through the gaps. Each pipe pair passed
adds one point. As you score higher, pipes speed up and gaps shrink.
"""

import sys
import random
from pathlib import Path

import pygame as pg

# -------------------------- Tunables & Constants --------------------------- #
WIDTH, HEIGHT = 480, 640          # Window size
FPS               = 60            # Target frames per second

GRAVITY           = 0.35          # Downwards acceleration
FLAP_STRENGTH     = -7.5          # Instant velocity change on flap
PIPE_SPEED_START  = 3.0           # Initial horizontal pipe speed
PIPE_SPEED_INC    = 0.15          # Speed increase per score
GAP_START         = 170           # Initial gap height between pipes
GAP_MIN           = 100           # Minimum gap (difficulty cap)
GAP_DEC           = 4             # Gap decrease per score

PIPE_INTERVAL     = 1500          # Milliseconds between spawns
SQUARE_SIZE       = 38            # Player size

BG_COL            = (20, 20, 30)
PIPE_COL          = (50, 200, 90)
SQUARE_COL        = (250, 240, 50)
TEXT_COL          = (240, 240, 240)

FONT_NAME         = pg.font.get_default_font()

# ----------------------------- Helper Classes ------------------------------ #
class Square:
    def __init__(self, x, y):
        self.rect = pg.Rect(x, y, SQUARE_SIZE, SQUARE_SIZE)
        self.vel  = 0.0

    def flap(self):
        self.vel = FLAP_STRENGTH

    def update(self):
        self.vel += GRAVITY
        self.rect.y += int(self.vel)

    def draw(self, surf):
        pg.draw.rect(surf, SQUARE_COL, self.rect, border_radius=6)

class PipePair:
    def __init__(self, x, gap_y, gap_height):
        self.x = x
        self.gap_y = gap_y
        self.gap_height = gap_height
        # Top and bottom rects (width grows automatically to window edge)
        self.rect_top    = pg.Rect(self.x, 0, 60, self.gap_y)
        self.rect_bottom = pg.Rect(self.x, self.gap_y + self.gap_height,
                                   60, HEIGHT - (self.gap_y + self.gap_height))
        self.passed = False

    def update(self, speed):
        self.x -= speed
        self.rect_top.x = self.rect_bottom.x = int(self.x)

    def draw(self, surf):
        pg.draw.rect(surf, PIPE_COL, self.rect_top,    border_radius=4)
        pg.draw.rect(surf, PIPE_COL, self.rect_bottom, border_radius=4)

    @property
    def off_screen(self):
        return self.x + self.rect_top.width < 0

# ---------------------------- Game Main Loop ------------------------------ #
def main():
    pg.init()
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    pg.display.set_caption("Flappy‑Square")
    clock = pg.time.Clock()
    font_big   = pg.font.Font(FONT_NAME, 56)
    font_small = pg.font.Font(FONT_NAME, 28)

    # Game objects
    square = Square(WIDTH // 4, HEIGHT // 2)
    pipes  = []
    score  = 0
    pipe_speed = PIPE_SPEED_START
    gap_height = GAP_START
    spawn_event = pg.USEREVENT + 1
    pg.time.set_timer(spawn_event, PIPE_INTERVAL)

    game_over = False
    running   = True

    while running:
        dt = clock.tick(FPS)  # dt in milliseconds; may be handy for future tweaks

        # ----- Event handling ----- #
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            elif event.type == pg.KEYDOWN:
                if event.key in (pg.K_ESCAPE, pg.K_q):
                    running = False
                elif event.key in (pg.K_SPACE, pg.K_UP):
                    if game_over:
                        # Restart
                        square = Square(WIDTH // 4, HEIGHT // 2)
                        pipes.clear()
                        score = 0
                        pipe_speed = PIPE_SPEED_START
                        gap_height = GAP_START
                        game_over = False
                    square.flap()
            elif event.type == spawn_event and not game_over:
                # Create a new PipePair
                gap_y = random.randint(60, HEIGHT - 60 - gap_height)
                pipes.append(PipePair(WIDTH, gap_y, gap_height))

        # ----- Update game state ----- #
        if not game_over:
            square.update()

            for pipe in pipes:
                pipe.update(pipe_speed)

                # Check pass for scoring
                if not pipe.passed and pipe.x + pipe.rect_top.width < square.rect.x:
                    pipe.passed = True
                    score += 1
                    pipe_speed += PIPE_SPEED_INC
                    gap_height = max(GAP_MIN, gap_height - GAP_DEC)

            # Remove off‑screen pipes
            pipes = [p for p in pipes if not p.off_screen]

            # Collision detection
            collided = any(square.rect.colliderect(p.rect_top) or
                           square.rect.colliderect(p.rect_bottom) for p in pipes)
            if collided or square.rect.top < 0 or square.rect.bottom > HEIGHT:
                game_over = True

        # ----- Draw everything ----- #
        screen.fill(BG_COL)

        for pipe in pipes:
            pipe.draw(screen)
        square.draw(screen)

        # Score / messages
        if game_over:
            msg1 = font_big.render("Game Over", True, TEXT_COL)
            msg2 = font_small.render("Press SPACE to restart", True, TEXT_COL)
            screen.blit(msg1, msg1.get_rect(center=(WIDTH//2, HEIGHT//2 - 30)))
            screen.blit(msg2, msg2.get_rect(center=(WIDTH//2, HEIGHT//2 + 25)))
        score_surf = font_small.render(f"Score: {score}", True, TEXT_COL)
        screen.blit(score_surf, (10, 10))

        pg.display.flip()

    pg.quit()
    sys.exit()

# ------------------------------ Entry Point ------------------------------- #
if __name__ == "__main__":
    main()
