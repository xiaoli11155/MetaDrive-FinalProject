from __future__ import annotations

import argparse

from metadrive_rl.config import PROJECT_ROOT, load_config
from metadrive_rl.envs import make_env


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test MetaDrive with random actions")
    parser.add_argument("--steps", type=int, default=100)
    parser.add_argument("--render", action="store_true")
    parser.add_argument("--config", default=str(PROJECT_ROOT / "configs" / "default.yaml"))
    args = parser.parse_args()

    config = load_config(args.config)
    env = make_env(config, render=args.render, num_scenarios=1)
    try:
        observation, info = env.reset(seed=config["environment"]["start_seed"])
        print(f"observation shape: {observation.shape}")
        print(f"action space: {env.action_space}")
        for step in range(1, args.steps + 1):
            observation, reward, terminated, truncated, info = env.step(env.action_space.sample())
            if terminated or truncated:
                print(f"episode ended at step {step}: {info}")
                break
        else:
            print(f"completed {args.steps} random steps")
    finally:
        env.close()


if __name__ == "__main__":
    main()

