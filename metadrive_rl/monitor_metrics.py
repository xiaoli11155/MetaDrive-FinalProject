from __future__ import annotations

import argparse
import csv
import re
import time
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from stable_baselines3 import PPO

from metadrive_rl.config import PROJECT_ROOT, load_config
from metadrive_rl.envs import make_env


STEP_PATTERN = re.compile(r"ppo_metadrive_(\d+)_steps\.zip$")


def evaluate(model_path: Path, config: dict, episodes: int, start_seed: int) -> dict:
    env = make_env(config, start_seed=start_seed, num_scenarios=episodes)
    model = PPO.load(model_path)
    outcomes: Counter[str] = Counter()
    rewards = []
    try:
        for episode in range(episodes):
            observation, _ = env.reset(seed=start_seed + episode)
            total_reward = 0.0
            terminated = truncated = False
            info = {}
            while not (terminated or truncated):
                action, _ = model.predict(observation, deterministic=True)
                observation, reward, terminated, truncated, info = env.step(action)
                total_reward += float(reward)
            rewards.append(total_reward)
            if info.get("arrive_dest"):
                outcomes["success"] += 1
            elif info.get("crash_vehicle") or info.get("crash_object"):
                outcomes["collision"] += 1
            elif info.get("out_of_road"):
                outcomes["out_of_road"] += 1
            else:
                outcomes["timeout"] += 1
    finally:
        env.close()
    return {
        "mean_reward": float(np.mean(rewards)),
        "reward_std": float(np.std(rewards)),
        **{name: outcomes[name] / episodes for name in ("success", "collision", "out_of_road", "timeout")},
    }


def write_outputs(rows: list[dict], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "checkpoint_metrics.csv"
    fields = ["steps", "model", "mean_reward", "reward_std", "success", "collision", "out_of_road", "timeout"]
    with csv_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    steps = np.asarray([row["steps"] for row in rows]) / 1000.0
    plt.figure(figsize=(9, 5))
    for key, label in (("success", "Success"), ("collision", "Collision"), ("out_of_road", "Out of road"), ("timeout", "Timeout")):
        plt.plot(steps, [100 * row[key] for row in rows], marker="o", label=label)
    plt.xlabel("Training steps (thousands)")
    plt.ylabel("Episode rate (%)")
    plt.ylim(0, 100)
    plt.grid(alpha=0.3)
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_dir / "outcome_rates.png", dpi=160)
    plt.close()

    plt.figure(figsize=(9, 4.5))
    means = np.asarray([row["mean_reward"] for row in rows])
    stds = np.asarray([row["reward_std"] for row in rows])
    plt.plot(steps, means, marker="o", color="tab:blue")
    plt.fill_between(steps, means - stds, means + stds, alpha=0.2, color="tab:blue")
    plt.xlabel("Training steps (thousands)")
    plt.ylabel("Episode reward")
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_dir / "mean_reward.png", dpi=160)
    plt.close()

    best = max(rows, key=lambda row: (row["success"], -row["collision"], -row["out_of_road"], row["mean_reward"]))
    (output_dir / "best_checkpoint.txt").write_text(
        f"model={best['model']}\nsteps={best['steps']}\nsuccess={best['success']:.1%}\n"
        f"collision={best['collision']:.1%}\nout_of_road={best['out_of_road']:.1%}\n"
        f"mean_reward={best['mean_reward']:.2f}\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate and plot checkpoints while training")
    parser.add_argument("--config", required=True)
    parser.add_argument("--checkpoint-dir", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--start-seed", type=int, default=1000)
    parser.add_argument("--target-steps", type=int, required=True)
    parser.add_argument("--poll-seconds", type=int, default=20)
    args = parser.parse_args()
    config = load_config(args.config)
    rows: list[dict] = []
    completed: set[int] = set()

    while True:
        checkpoints = []
        for path in args.checkpoint_dir.glob("ppo_metadrive_*_steps.zip"):
            match = STEP_PATTERN.match(path.name)
            if match:
                checkpoints.append((int(match.group(1)), path))
        for steps, path in sorted(checkpoints):
            if steps in completed:
                continue
            print(f"Evaluating {path.name} on {args.episodes} episodes", flush=True)
            metrics = evaluate(path, config, args.episodes, args.start_seed)
            row = {"steps": steps, "model": path.name, **metrics}
            rows.append(row)
            rows.sort(key=lambda item: item["steps"])
            completed.add(steps)
            write_outputs(rows, args.output_dir)
            print(
                f"steps={steps} success={metrics['success']:.1%} collision={metrics['collision']:.1%} "
                f"out_of_road={metrics['out_of_road']:.1%} reward={metrics['mean_reward']:.2f}",
                flush=True,
            )
        if completed and max(completed) >= args.target_steps:
            break
        time.sleep(args.poll_seconds)


if __name__ == "__main__":
    main()
