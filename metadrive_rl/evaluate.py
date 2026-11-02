from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import numpy as np
from stable_baselines3 import PPO

from metadrive_rl.config import PROJECT_ROOT, load_config
from metadrive_rl.envs import make_env


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a trained PPO agent")
    parser.add_argument("model", type=Path)
    parser.add_argument("--episodes", type=int)
    parser.add_argument("--start-seed", type=int, help="Override evaluation start seed")
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--config", default=str(PROJECT_ROOT / "configs" / "default.yaml"))
    args = parser.parse_args()

    config = load_config(args.config)
    eval_config = config["evaluation"]
    episodes = args.episodes or eval_config["episodes"]
    start_seed = args.start_seed if args.start_seed is not None else eval_config["start_seed"]
    env = make_env(
        config,
        render=args.render,
        start_seed=start_seed,
        num_scenarios=episodes,
    )
    model = PPO.load(args.model)
    rewards: list[float] = []
    outcomes: Counter[str] = Counter()

    try:
        for episode in range(episodes):
            observation, _ = env.reset(seed=start_seed + episode)
            episode_reward = 0.0
            terminated = truncated = False
            final_info = {}
            while not (terminated or truncated):
                action, _ = model.predict(
                    observation, deterministic=eval_config["deterministic"]
                )
                observation, reward, terminated, truncated, final_info = env.step(action)
                episode_reward += float(reward)
            rewards.append(episode_reward)
            if final_info.get("arrive_dest"):
                outcomes["success"] += 1
            elif final_info.get("crash_vehicle") or final_info.get("crash_object"):
                outcomes["collision"] += 1
            elif final_info.get("out_of_road"):
                outcomes["out_of_road"] += 1
            else:
                outcomes["timeout"] += 1
    finally:
        env.close()

    print(f"episodes: {episodes}")
    print(f"mean reward: {np.mean(rewards):.2f} +/- {np.std(rewards):.2f}")
    for name in ("success", "collision", "out_of_road", "timeout"):
        print(f"{name}: {outcomes[name] / episodes:.1%}")


if __name__ == "__main__":
    main()

