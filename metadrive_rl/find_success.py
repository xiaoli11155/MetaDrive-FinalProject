from __future__ import annotations

import argparse
from pathlib import Path

from stable_baselines3 import PPO

from metadrive_rl.config import PROJECT_ROOT, load_config
from metadrive_rl.envs import make_env


def main() -> None:
    parser = argparse.ArgumentParser(description="Find deterministic successful scenarios")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--config", default=str(PROJECT_ROOT / "configs" / "default.yaml"))
    parser.add_argument("--limit", type=int, default=5)
    args = parser.parse_args()

    config = load_config(args.config)
    start_seed = config["environment"]["start_seed"]
    num_scenarios = config["environment"]["num_scenarios"]
    env = make_env(config)
    model = PPO.load(args.model)
    successes: list[tuple[int, int]] = []

    try:
        for seed in range(start_seed, start_seed + num_scenarios):
            observation, _ = env.reset(seed=seed)
            terminated = truncated = False
            step = 0
            info = {}
            while not (terminated or truncated):
                action, _ = model.predict(observation, deterministic=True)
                observation, _, terminated, truncated, info = env.step(action)
                step += 1
            if info.get("arrive_dest"):
                successes.append((seed, step))
                print(f"success seed={seed} steps={step}")
                if len(successes) >= args.limit:
                    break
    finally:
        env.close()

    print(f"found {len(successes)} deterministic successes")


if __name__ == "__main__":
    main()
