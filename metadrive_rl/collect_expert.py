from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from metadrive.policy.idm_policy import IDMPolicy

from metadrive_rl.config import PROJECT_ROOT, load_config
from metadrive_rl.envs import make_env


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect IDM demonstrations")
    parser.add_argument("--config", default=str(PROJECT_ROOT / "configs" / "v3_imitation.yaml"))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--episodes", type=int)
    args = parser.parse_args()

    config = load_config(args.config)
    imitation = config["imitation"]
    episodes = args.episodes or int(imitation["episodes"])
    output = args.output or PROJECT_ROOT / imitation["dataset"]
    start_seed = int(config["environment"]["start_seed"])

    expert_config = load_config(args.config)
    expert_config["environment"]["agent_policy"] = IDMPolicy
    env = make_env(expert_config, start_seed=start_seed, num_scenarios=episodes)
    observations: list[np.ndarray] = []
    actions: list[np.ndarray] = []
    episode_ids: list[int] = []
    successes = 0

    try:
        for episode in range(episodes):
            seed = start_seed + episode
            observation, _ = env.reset(seed=seed)
            terminated = truncated = False
            final_info = {}
            while not (terminated or truncated):
                before = np.asarray(observation, dtype=np.float32).copy()
                observation, _, terminated, truncated, final_info = env.step(
                    np.zeros(2, dtype=np.float32)
                )
                expert_action = np.asarray(
                    env.unwrapped.agent.current_action, dtype=np.float32
                ).copy()
                observations.append(before)
                actions.append(expert_action)
                episode_ids.append(episode)
            successes += int(bool(final_info.get("arrive_dest")))
            print(
                f"episode={episode + 1}/{episodes} seed={seed} "
                f"outcome={'success' if final_info.get('arrive_dest') else 'failure'} "
                f"samples={len(observations)}"
            )
    finally:
        env.close()

    output.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output,
        observations=np.asarray(observations, dtype=np.float32),
        actions=np.asarray(actions, dtype=np.float32),
        episode_ids=np.asarray(episode_ids, dtype=np.int32),
    )
    print(f"Saved {len(observations)} samples from {episodes} episodes to {output}")
    print(f"Expert success rate: {successes / episodes:.1%}")


if __name__ == "__main__":
    main()

