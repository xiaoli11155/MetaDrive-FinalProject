from __future__ import annotations

import argparse
from functools import partial
from pathlib import Path
import traceback

from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor
from stable_baselines3.common.vec_env import SubprocVecEnv

from metadrive_rl.callbacks import CheckpointVideoCallback
from metadrive_rl.config import PROJECT_ROOT, load_config
from metadrive_rl.envs import make_env


def build_training_env(config: dict):
    """Top-level factory so Windows spawn can create MetaDrive workers."""
    return Monitor(make_env(config))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train PPO in MetaDrive")
    parser.add_argument("--config", default=str(PROJECT_ROOT / "configs" / "default.yaml"))
    parser.add_argument("--steps", type=int, help="Override total training timesteps")
    parser.add_argument("--resume", type=Path, help="Resume from a PPO .zip checkpoint")
    parser.add_argument(
        "--initialize-from",
        type=Path,
        help="Load policy/value weights but start a new experiment at step zero",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    train_config = config["training"]
    experiment_name = config.get("experiment", {}).get("name")
    checkpoint_dir = PROJECT_ROOT / "checkpoints"
    log_dir = PROJECT_ROOT / "logs"
    video_dir = PROJECT_ROOT / "videos"
    if experiment_name:
        checkpoint_dir /= experiment_name
        log_dir /= experiment_name
        video_dir /= experiment_name
    checkpoint_dir.mkdir(parents=True, exist_ok=True)
    log_dir.mkdir(parents=True, exist_ok=True)
    video_dir.mkdir(parents=True, exist_ok=True)

    num_envs = int(train_config.get("num_envs", 1))
    if num_envs > 1:
        env = SubprocVecEnv(
            [partial(build_training_env, config) for _ in range(num_envs)],
            start_method="spawn",
        )
    else:
        env = Monitor(make_env(config))
    if args.resume is not None and args.initialize_from is not None:
        raise ValueError("Use either --resume or --initialize-from, not both")
    is_resuming = args.resume is not None
    if is_resuming:
        model = PPO.load(args.resume, env=env, tensorboard_log=str(log_dir))
    else:
        model = PPO(
            "MlpPolicy",
            env,
            learning_rate=train_config["learning_rate"],
            n_steps=train_config["n_steps"],
            batch_size=train_config["batch_size"],
            n_epochs=train_config["n_epochs"],
            gamma=train_config["gamma"],
            gae_lambda=train_config["gae_lambda"],
            clip_range=train_config["clip_range"],
            ent_coef=train_config["ent_coef"],
            tensorboard_log=str(log_dir),
            seed=config["seed"],
            verbose=1,
            device="auto",
        )
        if args.initialize_from is not None:
            source_model = PPO.load(args.initialize_from, device=model.device)
            model.set_parameters(source_model.get_parameters(), exact_match=True)
            print(f"Initialized network weights from {args.initialize_from}; timestep counter reset to zero.")

    callback = CheckpointVideoCallback(
        save_freq=train_config["checkpoint_freq"],
        checkpoint_dir=checkpoint_dir,
        video_dir=video_dir,
        config_path=Path(args.config).resolve(),
        record_video=config["video"]["enabled"],
    )
    target_steps = args.steps or train_config["total_timesteps"]
    remaining_steps = target_steps - model.num_timesteps if is_resuming else target_steps
    if remaining_steps <= 0:
        print(f"Model already has {model.num_timesteps} steps (target: {target_steps}).")
        env.close()
        return
    print(
        f"Training from {model.num_timesteps} to {target_steps} total steps "
        f"({remaining_steps} remaining)."
    )
    try:
        model.learn(
            total_timesteps=remaining_steps,
            callback=callback,
            progress_bar=True,
            reset_num_timesteps=not is_resuming,
        )
        model.save(checkpoint_dir / "ppo_metadrive_final")
    except KeyboardInterrupt:
        interrupted_path = checkpoint_dir / f"ppo_metadrive_interrupted_{model.num_timesteps}_steps"
        model.save(interrupted_path)
        print(f"Training interrupted; saved model to {interrupted_path}.zip")
    except Exception:
        emergency_path = checkpoint_dir / f"ppo_metadrive_emergency_{model.num_timesteps}_steps"
        model.save(emergency_path)
        error_path = log_dir / "training_error.log"
        error_path.write_text(traceback.format_exc(), encoding="utf-8")
        print(f"Training failed; saved model to {emergency_path}.zip")
        print(f"Error details: {error_path}")
        raise
    finally:
        try:
            env.close()
        except (BrokenPipeError, EOFError):
            # A failed subprocess may already have closed its communication pipe.
            pass


if __name__ == "__main__":
    main()

