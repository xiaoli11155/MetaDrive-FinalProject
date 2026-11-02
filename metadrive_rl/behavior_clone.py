from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import torch
from stable_baselines3 import PPO
from stable_baselines3.common.monitor import Monitor

from metadrive_rl.config import PROJECT_ROOT, load_config
from metadrive_rl.envs import make_env


def main() -> None:
    parser = argparse.ArgumentParser(description="Behavior-clone a PPO policy from IDM data")
    parser.add_argument("--config", default=str(PROJECT_ROOT / "configs" / "v3_imitation.yaml"))
    parser.add_argument("--dataset", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    config = load_config(args.config)
    train = config["training"]
    imitation = config["imitation"]
    dataset_path = args.dataset or PROJECT_ROOT / imitation["dataset"]
    output = args.output or PROJECT_ROOT / "checkpoints" / "v3_imitation" / "ppo_bc_pretrained.zip"

    data = np.load(dataset_path)
    observations = data["observations"].astype(np.float32)
    actions = data["actions"].astype(np.float32)
    episode_ids = data["episode_ids"]
    validation_fraction = float(imitation["validation_fraction"])
    split_episode = int((episode_ids.max() + 1) * (1.0 - validation_fraction))
    train_mask = episode_ids < split_episode
    val_mask = ~train_mask

    env = Monitor(make_env(config))
    expected_observation_size = int(np.prod(env.observation_space.shape))
    if observations.shape[1] < expected_observation_size:
        padding = np.zeros(
            (observations.shape[0], expected_observation_size - observations.shape[1]),
            dtype=np.float32,
        )
        observations = np.concatenate([observations, padding], axis=1)
        print(
            f"Padded demonstrations from {observations.shape[1] - padding.shape[1]} "
            f"to {expected_observation_size} observation features"
        )
    elif observations.shape[1] != expected_observation_size:
        raise ValueError(
            f"Dataset observation size {observations.shape[1]} does not match env size "
            f"{expected_observation_size}"
        )
    model = PPO(
        "MlpPolicy",
        env,
        learning_rate=train["learning_rate"],
        n_steps=train["n_steps"],
        batch_size=train["batch_size"],
        n_epochs=train["n_epochs"],
        gamma=train["gamma"],
        gae_lambda=train["gae_lambda"],
        clip_range=train["clip_range"],
        ent_coef=train["ent_coef"],
        seed=config["seed"],
        verbose=0,
    )
    device = model.device
    optimizer = torch.optim.Adam(
        model.policy.parameters(), lr=float(imitation["learning_rate"])
    )
    batch_size = int(imitation["batch_size"])
    rng = np.random.default_rng(config["seed"])
    train_indices = np.flatnonzero(train_mask)

    for epoch in range(1, int(imitation["epochs"]) + 1):
        rng.shuffle(train_indices)
        model.policy.set_training_mode(True)
        losses = []
        for start in range(0, len(train_indices), batch_size):
            idx = train_indices[start : start + batch_size]
            obs = torch.as_tensor(observations[idx], device=device)
            target = torch.as_tensor(actions[idx], device=device)
            mean_action = model.policy.get_distribution(obs).distribution.mean
            loss = torch.nn.functional.mse_loss(mean_action, target)
            optimizer.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.policy.parameters(), 1.0)
            optimizer.step()

        model.policy.set_training_mode(False)
        with torch.no_grad():
            val_obs = torch.as_tensor(observations[val_mask], device=device)
            val_target = torch.as_tensor(actions[val_mask], device=device)
            val_pred = model.policy.get_distribution(val_obs).distribution.mean
            val_loss = torch.nn.functional.mse_loss(val_pred, val_target).item()
        print(f"epoch={epoch} validation_mse={val_loss:.6f}")

    with torch.no_grad():
        model.policy.log_std.fill_(float(imitation.get("initial_log_std", -2.0)))
    output.parent.mkdir(parents=True, exist_ok=True)
    model.save(output)
    env.close()
    print(f"Saved behavior-cloned PPO policy to {output}")


if __name__ == "__main__":
    main()
