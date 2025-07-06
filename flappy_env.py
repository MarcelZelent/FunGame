import math
import random
import pygame as pg
import gymnasium as gym
from gymnasium import spaces
import numpy as np

# ---------- copy / paste constants from flappy_square.py ---------------
WIDTH, HEIGHT = 480, 640
GRAVITY = 0.35
FLAP_STRENGTH = -7.5
PIPE_INTERVAL_TICKS = 90     # ~1.5 s at 60 FPS
PIPE_SPEED_START  = 3.0
GAP_START         = 170
GAP_MIN           = 100
GAP_DEC           = 4
SQUARE_SIZE       = 38
# ----------------------------------------------------------------------

class _Square:
    def __init__(self):
        self.y = HEIGHT / 2
        self.vel = 0.0

    def flap(self):
        self.vel = FLAP_STRENGTH

    def update(self):
        self.vel += GRAVITY
        self.y += self.vel

    @property
    def rect(self):
        return pg.Rect(WIDTH // 4, int(self.y), SQUARE_SIZE, SQUARE_SIZE)

class _Pipe:
    def __init__(self, x, gap_y, gap_h, w=60):
        self.x = x
        self.w = w
        self.gap_y = gap_y
        self.gap_h = gap_h
        self.passed = False

    def update(self, speed):
        self.x -= speed

    @property
    def rects(self):
        top = pg.Rect(self.x, 0, self.w, self.gap_y)
        bottom = pg.Rect(self.x, self.gap_y+self.gap_h, self.w,
                         HEIGHT - (self.gap_y+self.gap_h))
        return top, bottom

    @property
    def off_screen(self):
        return self.x + self.w < 0

class FlappyEnv(gym.Env):
    """
    Observation  (float32):
        0 : vertical distance (square→gap centre)  [‑∞, ∞]
        1 : horizontal distance to next pipe front [0, WIDTH]
        2 : square vertical velocity                [‑∞, ∞]
        3 : current gap height                      [GAP_MIN, GAP_START]
    Actions (Discrete):
        0 : do nothing
        1 : flap
    Reward:
        +1 for every pipe passed
        ‑0.01 each step alive (encourages speed)
        ‑1  on collision → episode terminated
    """
    metadata = {"render_modes": ["human", "rgb_array"], "render_fps": 60}

    def __init__(self, render_mode=None):
        super().__init__()
        self.render_mode = render_mode
        self.action_space = spaces.Discrete(2)
        # State values are normalised into ~[‑1, 1]
        high = np.array([ 1.0,  1.0,  1.0,  1.0], dtype=np.float32)
        self.observation_space = spaces.Box(-high, high, dtype=np.float32)

        # pygame init only if we need visuals
        if render_mode == "human":
            pg.init()
            self.screen = pg.display.set_mode((WIDTH, HEIGHT))
            pg.display.set_caption("Flappy‑Square RL")
            self.clock = pg.time.Clock()

    # --------------- Gym API ----------------
    def reset(self, *, seed=None, options=None):
        super().reset(seed=seed)
        self.square = _Square()
        self.pipes = []
        self.tick = 0
        self.pipe_speed = PIPE_SPEED_START
        self.gap_h = GAP_START
        self.score = 0
        obs = self._get_obs()
        return obs, {}

    def step(self, action):
        done = False
        reward = -0.01  # base survival penalty

        if action == 1:
            self.square.flap()

        self.square.update()

        # spawn pipes
        if self.tick % PIPE_INTERVAL_TICKS == 0:
            gap_y = random.randint(60, HEIGHT - 60 - self.gap_h)
            self.pipes.append(_Pipe(WIDTH, gap_y, self.gap_h))

        # update pipes
        for pipe in list(self.pipes):
            pipe.update(self.pipe_speed)
            if not pipe.passed and pipe.x + pipe.w < WIDTH // 4:
                pipe.passed = True
                self.score += 1
                reward += 1.0  # passing pipe reward
                self.pipe_speed += 0.15
                self.gap_h = max(GAP_MIN, self.gap_h - GAP_DEC)
            if pipe.off_screen:
                self.pipes.remove(pipe)

        # collision detection
        collided = (
            self.square.y < 0 or
            self.square.y + SQUARE_SIZE > HEIGHT or
            any(self.square.rect.colliderect(r)
                for p in self.pipes for r in p.rects)
        )
        if collided:
            reward = -1.0
            done = True

        # gap-center reward shaping
        next_pipe = min(
            (p for p in self.pipes if p.x + p.w >= WIDTH // 4),
            default=None,
            key=lambda p: p.x
        )
        if next_pipe:
            gap_centre = next_pipe.gap_y + next_pipe.gap_h / 2
            dist = abs(self.square.y - gap_centre)
            proximity_reward = 0.1 * (1.0 - dist / (HEIGHT / 2))
            reward += proximity_reward

        self.tick += 1
        obs = self._get_obs()
        info = {"score": self.score}

        if self.render_mode == "human":
            self._render()

        return obs, reward, done, False, info


    def _get_obs(self):
        # next pipe
        next_pipe = min(
            (p for p in self.pipes if p.x + p.w >= WIDTH//4),
            default=None, key=lambda p: p.x)
        if next_pipe is None:
            horiz = WIDTH
            vert  = 0
            gap_h = self.gap_h
        else:
            horiz = next_pipe.x + next_pipe.w - WIDTH//4
            gap_centre = next_pipe.gap_y + next_pipe.gap_h / 2
            vert = self.square.y - gap_centre
            gap_h = next_pipe.gap_h

        # normalise roughly to [‑1,1]
        v = np.array([
            vert / (HEIGHT/2),
            horiz / WIDTH,
            self.square.vel / 10,
            (gap_h - GAP_MIN) / (GAP_START - GAP_MIN)
        ], dtype=np.float32)
        return v

    def _render(self):
        for event in pg.event.get():
            if event.type == pg.QUIT:
                pg.quit(); raise SystemExit

        self.screen.fill((20,20,30))
        # draw pipes
        for p in self.pipes:
            for r in p.rects:
                pg.draw.rect(self.screen, (50,200,90), r, border_radius=4)
        pg.draw.rect(self.screen, (250,240,50), self.square.rect, border_radius=6)
        pg.display.flip()
        self.clock.tick(self.metadata["render_fps"])

    def close(self):
        if self.render_mode == "human":
            pg.quit()
