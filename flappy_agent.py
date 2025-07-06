import gymnasium as gym
from stable_baselines3 import PPO
from flappy_env import FlappyEnv
from gymnasium.envs.registration import register

# Only has an effect the first time it is executed
register(
    id="FlappyEnv-v0",
    entry_point="flappy_env:FlappyEnv",   # "module:class"
    max_episode_steps=10_000,             # optional
)

env = gym.make("flappy_env:FlappyEnv")        # gymnasium-style registration
eval_env = FlappyEnv(render_mode=None)

model = PPO(
    "MlpPolicy",
    env,
    verbose=1,
    batch_size=2048,
    learning_rate=3e-4,
    n_steps=2048,
    gamma=0.99,
    gae_lambda=0.95,
    clip_range=0.2,
    tensorboard_log="./tensorboard/"
)

# ~5–10 M steps = decent score (> 50) in < 1 h on a laptop CPU
model.learn(total_timesteps=1_000_000, progress_bar=True)
model.save("ppo_flappy")
env.close()
