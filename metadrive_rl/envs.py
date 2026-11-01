from __future__ import annotations

from copy import deepcopy
from typing import Any

from metadrive import MetaDriveEnv


def make_env(
    config: dict[str, Any],
    *,
    render: bool = False,
    start_seed: int | None = None,
    num_scenarios: int | None = None,
) -> MetaDriveEnv:
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
    return MetaDriveEnv(env_config)

