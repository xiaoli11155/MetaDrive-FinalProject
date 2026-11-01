from __future__ import annotations

import argparse
from pathlib import Path

import cv2
from stable_baselines3 import PPO

from metadrive_rl.config import PROJECT_ROOT, load_config
from metadrive_rl.envs import make_env


def main() -> None:
    parser = argparse.ArgumentParser(description="Record one checkpoint evaluation as MP4")
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--config", default=str(PROJECT_ROOT / "configs" / "default.yaml"))
    parser.add_argument("--seed", type=int, help="Override the configured video scenario seed")
    args = parser.parse_args()

    config = load_config(args.config)
    video_config = config["video"]
    scenario_seed = args.seed if args.seed is not None else video_config["seed"]
    size = int(video_config["screen_size"])
    args.output.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(
        str(args.output),
        cv2.VideoWriter_fourcc(*"mp4v"),
        float(video_config["fps"]),
        (size, size),
    )
    if not writer.isOpened():
        raise RuntimeError(f"Could not open MP4 writer for {args.output}")

    env = make_env(config, start_seed=scenario_seed, num_scenarios=1)
    model = PPO.load(args.model)
    observation, _ = env.reset(seed=scenario_seed)
    terminated = truncated = False
    step = 0
    final_info = {}

    try:
        while not (terminated or truncated) and step < video_config["max_steps"]:
            action, _ = model.predict(observation, deterministic=True)
            observation, _, terminated, truncated, final_info = env.step(action)
            if step % video_config["frame_interval"] == 0:
                frame = env.render(
                    mode="topdown",
                    window=False,
                    screen_size=(size, size),
                    target_agent_heading_up=True,
                    draw_target_vehicle_trajectory=True,
                )
                writer.write(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            step += 1
    finally:
        writer.release()
        env.close()

    if final_info.get("arrive_dest"):
        outcome = "arrive_dest"
    elif final_info.get("out_of_road"):
        outcome = "out_of_road"
    elif final_info.get("crash_vehicle") or final_info.get("crash_object"):
        outcome = "collision"
    else:
        outcome = "timeout"
    print(f"Saved video: {args.output} ({step} environment steps, outcome={outcome}, seed={scenario_seed})")


if __name__ == "__main__":
    main()

