from __future__ import annotations

import argparse
import csv
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
    parser.add_argument("--output-csv", type=Path, help="Write one diagnostic row per episode")
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
    episode_rows: list[dict] = []

    try:
        for episode in range(episodes):
            observation, _ = env.reset(seed=start_seed + episode)
            episode_reward = 0.0
            terminated = truncated = False
            final_info = {}
            steps = 0
            max_traffic_risk = 0.0
            max_intersection_risk = 0.0
            max_wrong_decision_action = 0.0
            while not (terminated or truncated):
                action, _ = model.predict(
                    observation, deterministic=eval_config["deterministic"]
                )
                observation, reward, terminated, truncated, final_info = env.step(action)
                episode_reward += float(reward)
                steps += 1
                max_traffic_risk = max(max_traffic_risk, float(final_info.get("traffic_risk", 0.0)))
                max_intersection_risk = max(
                    max_intersection_risk, float(final_info.get("intersection_risk", 0.0))
                )
                max_wrong_decision_action = max(
                    max_wrong_decision_action,
                    float(final_info.get("wrong_decision_action", 0.0)),
                )
            rewards.append(episode_reward)
            if final_info.get("arrive_dest"):
                outcome = "success"
            elif final_info.get("crash_vehicle") or final_info.get("crash_object"):
                outcome = "collision"
            elif final_info.get("out_of_road"):
                outcome = "out_of_road"
            else:
                outcome = "timeout"
            outcomes[outcome] += 1
            episode_rows.append(
                {
                    "seed": start_seed + episode,
                    "outcome": outcome,
                    "reward": episode_reward,
                    "steps": steps,
                    "route_completion": float(final_info.get("route_completion", 0.0)),
                    "max_traffic_risk": max_traffic_risk,
                    "max_intersection_risk": max_intersection_risk,
                    "max_wrong_decision_action": max_wrong_decision_action,
                }
            )
    finally:
        env.close()

    print(f"episodes: {episodes}")
    print(f"mean reward: {np.mean(rewards):.2f} +/- {np.std(rewards):.2f}")
    for name in ("success", "collision", "out_of_road", "timeout"):
        print(f"{name}: {outcomes[name] / episodes:.1%}")
    if args.output_csv:
        args.output_csv.parent.mkdir(parents=True, exist_ok=True)
        with args.output_csv.open("w", newline="", encoding="utf-8") as file:
            writer = csv.DictWriter(file, fieldnames=episode_rows[0].keys())
            writer.writeheader()
            writer.writerows(episode_rows)
        print(f"episode diagnostics: {args.output_csv}")


if __name__ == "__main__":
    main()

