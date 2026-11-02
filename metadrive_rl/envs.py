from __future__ import annotations

from copy import deepcopy
from typing import Any

import gymnasium as gym
import numpy as np
from metadrive import MetaDriveEnv

from metadrive_rl.reward import SkillRewardEnv, SmoothDrivingEnv, TrafficAwareEnv


class SmoothSteeringWrapper(gym.ActionWrapper):
    """Low-pass and rate-limit steering while preserving the action space."""

    def __init__(self, env: gym.Env, alpha: float, max_delta: float):
        super().__init__(env)
        self.alpha = alpha
        self.max_delta = max_delta
        self.previous_steering = 0.0

    def reset(self, **kwargs):
        self.previous_steering = 0.0
        return self.env.reset(**kwargs)

    def action(self, action):
        filtered = np.asarray(action, dtype=np.float32).copy()
        target = self.alpha * self.previous_steering + (1.0 - self.alpha) * float(filtered[0])
        target = np.clip(
            target,
            self.previous_steering - self.max_delta,
            self.previous_steering + self.max_delta,
        )
        filtered[0] = np.clip(target, -1.0, 1.0)
        self.previous_steering = float(filtered[0])
        return filtered

    def render(self, *args, **kwargs):
        """Forward MetaDrive's extended top-down rendering arguments."""
        return self.env.render(*args, **kwargs)


class TrafficStateObservationWrapper(gym.ObservationWrapper):
    """Append the reward's intersection decision state to the policy observation."""

    def __init__(self, env: gym.Env):
        super().__init__(env)
        if not isinstance(env.observation_space, gym.spaces.Box):
            raise TypeError("Traffic state augmentation requires a Box observation space")
        low = np.concatenate([env.observation_space.low, np.asarray([-1, 0, 0, 0, 0, 0], dtype=np.float32)])
        high = np.concatenate([env.observation_space.high, np.ones(6, dtype=np.float32)])
        self.observation_space = gym.spaces.Box(low=low, high=high, dtype=np.float32)

    def reset(self, *, seed=None, options=None):
        # MetaDrive 0.4.3 predates Gymnasium's ``options`` reset argument.
        observation, info = self.env.reset(seed=seed)
        return self.observation(observation), info

    def observation(self, observation):
        features = self.env.unwrapped.traffic_observation_features()
        return np.concatenate([np.asarray(observation, dtype=np.float32), features]).astype(np.float32)

    def render(self, *args, **kwargs):
        return self.env.render(*args, **kwargs)


def make_env(
    config: dict[str, Any],
    *,
    render: bool = False,
    start_seed: int | None = None,
    num_scenarios: int | None = None,
) -> gym.Env:
    """Build one MetaDrive environment with continuous ego control.

    The action is ``[steering, throttle_or_brake]`` and both values are in
    ``[-1, 1]``. Positive longitudinal values accelerate; negative values brake.
    """
    env_config = deepcopy(config["environment"])
    env_config["use_render"] = render
    if start_seed is not None:
        env_config["start_seed"] = start_seed
    if num_scenarios is not None:
        env_config["num_scenarios"] = num_scenarios
    use_custom_reward = env_config.pop("custom_smooth_reward", False)
    use_skill_reward = env_config.pop("skill_reward", False)
    use_traffic_reward = env_config.pop("traffic_aware_reward", False)
    use_traffic_state_observation = env_config.pop("traffic_state_observation", False)
    smoothing = env_config.pop("control_smoothing", None)
    reward_keys = (
        "lateral_penalty",
        "heading_penalty",
        "steering_penalty",
        "steering_change_penalty",
        "curve_overspeed_penalty",
        "straight_target_speed",
        "curve_target_speed",
        "minimum_speed",
        "idle_penalty",
        "speed_tracking_reward",
    )
    smooth_reward_config = {
        key: env_config.pop(key) for key in reward_keys if key in env_config
    }
    skill_reward_config = env_config.pop("skill_reward_config", None)
    traffic_reward_config = env_config.pop("traffic_reward_config", None)
    if use_traffic_reward:
        env = TrafficAwareEnv(env_config, traffic_reward_config)
    elif use_skill_reward:
        env = SkillRewardEnv(env_config, skill_reward_config)
    elif use_custom_reward:
        env = SmoothDrivingEnv(env_config, smooth_reward_config)
    else:
        env = MetaDriveEnv(env_config)
    if use_traffic_state_observation:
        env = TrafficStateObservationWrapper(env)
    if smoothing:
        env = SmoothSteeringWrapper(
            env,
            alpha=float(smoothing["alpha"]),
            max_delta=float(smoothing["max_delta"]),
        )
    return env


