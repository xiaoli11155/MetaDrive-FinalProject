from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from stable_baselines3.common.callbacks import BaseCallback


class CheckpointVideoCallback(BaseCallback):
    """Save a checkpoint and record one evaluation episode as MP4."""

    def __init__(
        self,
        save_freq: int,
        checkpoint_dir: Path,
        video_dir: Path,
        config_path: Path,
        record_video: bool = True,
    ) -> None:
        super().__init__(verbose=1)
        self.save_freq = save_freq
        self.checkpoint_dir = checkpoint_dir
        self.video_dir = video_dir
        self.config_path = config_path
        self.record_video = record_video

    def _on_step(self) -> bool:
        if self.num_timesteps % self.save_freq != 0:
            return True

        stem = f"ppo_metadrive_{self.num_timesteps}_steps"
        model_path = self.checkpoint_dir / stem
        self.model.save(model_path)
        saved_zip = model_path.with_suffix(".zip")
        print(f"Saved checkpoint: {saved_zip}")

        if self.record_video:
            output_path = self.video_dir / f"{stem}.mp4"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "metadrive_rl.record_video",
                    "--model",
                    str(saved_zip),
                    "--output",
                    str(output_path),
                    "--config",
                    str(self.config_path),
                ],
                cwd=self.config_path.parents[1],
                check=False,
            )
            if result.returncode != 0:
                print(f"Video recording failed for step {self.num_timesteps}; training will continue.")
        return True

