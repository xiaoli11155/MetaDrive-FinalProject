from __future__ import annotations

import argparse
from collections import defaultdict
from pathlib import Path

from stable_baselines3 import PPO

from metadrive_rl.config import PROJECT_ROOT, load_config
from metadrive_rl.envs import make_env


REWARD_KEYS = (
    "reward_base",
    "cost_lateral",
    "cost_heading",
    "cost_steering",
    "cost_steering_change",
    "cost_overspeed",
    "cost_idle",
    "reward_speed_tracking",
    "r_lane_keeping",
    "r_heading",
    "r_speed",
    "r_steering_smooth",
    "r_straight_steering",
    "r_guided_steering",
    "r_throttle_smooth",
    "r_longitudinal",
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Inspect reward component scales")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--config", default=str(PROJECT_ROOT / "configs" / "v3_smooth_turning.yaml"))
    parser.add_argument("--episodes", type=int, default=5)
    parser.add_argument("--start-seed", type=int, default=0)
    args = parser.parse_args()

    config = load_config(args.config)
    env = make_env(config)
    model = PPO.load(args.model)

    try:
        for episode in range(args.episodes):
            seed = args.start_seed + episode
            observation, _ = env.reset(seed=seed)
            totals = defaultdict(float)
            min_reward = float("inf")
            max_reward = float("-inf")
            steps = 0
            terminated = truncated = False
            info = {}
            while not (terminated or truncated):
                action, _ = model.predict(observation, deterministic=True)
                observation, reward, terminated, truncated, info = env.step(action)
                reward = float(reward)
                totals["reward"] += reward
                min_reward = min(min_reward, reward)
                max_reward = max(max_reward, reward)
                for key in REWARD_KEYS:
                    totals[key] += float(info.get(key, 0.0))
                steps += 1
            outcome = "success" if info.get("arrive_dest") else "out_of_road" if info.get("out_of_road") else "other"
            values = " ".join(f"{key}={totals[key]:.2f}" for key in REWARD_KEYS)
            print(
                f"seed={seed} outcome={outcome} steps={steps} total={totals['reward']:.2f} "
                f"min={min_reward:.2f} max={max_reward:.2f} {values}"
            )
    finally:
        env.close()


if __name__ == "__main__":
    main()
