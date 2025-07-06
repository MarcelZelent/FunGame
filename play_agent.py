import time
import gymnasium as gym
from stable_baselines3 import PPO
from flappy_env import FlappyEnv

env = FlappyEnv(render_mode="human")
model = PPO.load("ppo_flappy", env=env)

obs, _ = env.reset()
while True:
    action, _ = model.predict(obs, deterministic=True)
    obs, reward, term, trunc, info = env.step(action)
    if term or trunc:
        print("Score:", info["score"])
        time.sleep(1)
        obs, _ = env.reset()
