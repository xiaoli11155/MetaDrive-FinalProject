from __future__ import annotations

import numpy as np
from metadrive import MetaDriveEnv
from metadrive.component.lane.circular_lane import CircularLane
from metadrive.policy.idm_policy import FrontBackObjects


class SmoothDrivingEnv(MetaDriveEnv):
    """MetaDrive reward with explicit lane, heading and control penalties."""

    def __init__(self, config, smooth_reward_config):
        self.smooth_reward_config = smooth_reward_config
        super().__init__(config)

    def reward_function(self, vehicle_id: str):
        reward, info = super().reward_function(vehicle_id)
        vehicle = self.agents[vehicle_id]

        # Keep terminal rewards unambiguous.
        if (
            self._is_arrive_destination(vehicle)
            or self._is_out_of_road(vehicle)
            or vehicle.crash_vehicle
            or vehicle.crash_object
        ):
            return reward, info

        lane = (
            vehicle.lane
            if vehicle.lane in vehicle.navigation.current_ref_lanes
            else vehicle.navigation.current_ref_lanes[0]
        )
        _, lateral = lane.local_coordinates(vehicle.position)
        half_width = max(vehicle.navigation.get_current_lane_width() / 2, 0.1)
        lateral_error = min(abs(lateral) / half_width, 2.0)
        heading_error = 1.0 - vehicle.heading_diff(lane)

        steering = float(vehicle.current_action[0])
        previous_steering = float(vehicle.last_action[0])
        steering_change = abs(steering - previous_steering)

        is_curve = hasattr(lane, "radius")
        target_speed = (
            self.smooth_reward_config["curve_target_speed"]
            if is_curve
            else self.smooth_reward_config["straight_target_speed"]
        )
        overspeed = max(vehicle.speed_km_h - target_speed, 0.0) / max(vehicle.max_speed_km_h, 1.0)
        speed_tracking = min(max(vehicle.speed_km_h, 0.0) / max(target_speed, 1.0), 1.0)
        idle = max(self.smooth_reward_config["minimum_speed"] - vehicle.speed_km_h, 0.0) / max(
            self.smooth_reward_config["minimum_speed"], 1.0
        )

        base_reward = reward
        lateral_cost = self.smooth_reward_config["lateral_penalty"] * lateral_error
        heading_cost = self.smooth_reward_config["heading_penalty"] * heading_error
        steering_cost = self.smooth_reward_config["steering_penalty"] * abs(steering)
        steering_change_cost = self.smooth_reward_config["steering_change_penalty"] * steering_change
        overspeed_cost = self.smooth_reward_config["curve_overspeed_penalty"] * overspeed
        idle_cost = self.smooth_reward_config["idle_penalty"] * idle
        speed_bonus = self.smooth_reward_config["speed_tracking_reward"] * speed_tracking
        reward += speed_bonus
        reward -= lateral_cost + heading_cost + steering_cost + steering_change_cost + overspeed_cost + idle_cost

        info.update(
            lateral_error=lateral_error,
            heading_error=heading_error,
            steering_change=steering_change,
            overspeed=overspeed,
            reward_base=base_reward,
            cost_lateral=lateral_cost,
            cost_heading=heading_cost,
            cost_steering=steering_cost,
            cost_steering_change=steering_change_cost,
            cost_overspeed=overspeed_cost,
            cost_idle=idle_cost,
            reward_speed_tracking=speed_bonus,
        )
        return reward, info


class SkillRewardEnv(MetaDriveEnv):
    """Stage-1 skill reward adapted from an open-source MetaDrive project."""

    def __init__(self, config, skill_reward_config):
        self.skill_reward_config = skill_reward_config
        super().__init__(config)

    def reward_function(self, vehicle_id: str):
        vehicle = self.agents[vehicle_id]

        if vehicle.lane in vehicle.navigation.current_ref_lanes:
            lane = vehicle.lane
            positive_road = 1.0
        else:
            lane = vehicle.navigation.current_ref_lanes[0]
            positive_road = -1.0 if vehicle.navigation.current_road.is_negative_road() else 1.0

        long_last, _ = lane.local_coordinates(vehicle.last_position)
        long_now, lateral = lane.local_coordinates(vehicle.position)
        half_width = max(vehicle.navigation.get_current_lane_width() / 2.0, 1e-6)
        lateral_ratio = abs(lateral) / half_width

        lane_score = float(np.exp(-2.0 * lateral_ratio**2))
        heading_score = float(np.clip(vehicle.heading_diff(lane), 0.0, 1.0))

        is_curve = isinstance(lane, CircularLane)
        curvature = 1.0 / max(float(lane.radius), 1e-6) if is_curve else 0.0
        curve_factor = max(
            self.skill_reward_config["minimum_curve_speed_factor"],
            1.0 - self.skill_reward_config["curvature_speed_scale"] * curvature,
        )
        target_speed = max(
            self.skill_reward_config["minimum_curve_speed"],
            self.skill_reward_config["straight_target_speed"] * curve_factor,
        )
        normalized_speed_error = abs(vehicle.speed_km_h - target_speed) / max(target_speed, 1.0)
        raw_speed_score = float(np.exp(-2.0 * normalized_speed_error**2))
        # A Gaussian centered on the target still gives exp(-2) at zero speed.
        # Rebase it so stopping earns exactly zero instead of becoming a local optimum.
        stopped_score = float(np.exp(-2.0))
        speed_score = float(np.clip((raw_speed_score - stopped_score) / (1.0 - stopped_score), 0.0, 1.0))

        steering_change = abs(float(vehicle.current_action[0]) - float(vehicle.last_action[0]))
        throttle_change = abs(float(vehicle.current_action[1]) - float(vehicle.last_action[1]))
        steering_score = 1.0 - float(np.clip(steering_change, 0.0, 1.0))
        throttle_score = 1.0 - float(np.clip(throttle_change, 0.0, 1.0))
        straight_steering_score = 0.0 if is_curve else 1.0 - abs(float(vehicle.current_action[0]))
        lane_heading = float(lane.heading_theta_at(long_now))
        signed_heading_error = float(
            (vehicle.heading_theta - lane_heading + np.pi) % (2.0 * np.pi) - np.pi
        )
        guided_target = float(
            np.clip(
                self.skill_reward_config.get("guided_lateral_gain", 0.0) * np.clip(lateral_ratio, -2.0, 2.0) * np.sign(lateral)
                - self.skill_reward_config.get("guided_heading_gain", 0.0) * signed_heading_error,
                -1.0,
                1.0,
            )
        )
        guided_error = float(vehicle.current_action[0]) - guided_target
        guided_steering_score = float(np.exp(-2.0 * guided_error**2))
        # Local lane coordinates reset at segment boundaries. Clipping removes the
        # artificial jump while retaining the normal per-step progress signal.
        longitudinal = float(np.clip((long_now - long_last) * positive_road, -1.0, 1.0))

        # Lane-centering and smooth controls are useful only while actually driving.
        # Without this gate, a stationary car earns a large positive reward forever.
        motion_gate = float(np.clip(vehicle.speed_km_h / self.skill_reward_config["motion_gate_speed"], 0.0, 1.0))

        w = self.skill_reward_config["weights"]
        reward = (
            motion_gate * w["lane_keeping"] * lane_score
            + motion_gate * w["heading"] * heading_score
            + w["speed_tracking"] * speed_score
            + motion_gate * w["steering_smooth"] * steering_score
            + motion_gate * w.get("straight_steering", 0.0) * straight_steering_score
            + motion_gate * w.get("guided_steering", 0.0) * guided_steering_score
            + motion_gate * w["throttle_smooth"] * throttle_score
            + w["longitudinal"] * longitudinal
        )

        info = {
            "r_lane_keeping": lane_score,
            "r_heading": heading_score,
            "r_speed": speed_score,
            "r_steering_smooth": steering_score,
            "r_straight_steering": straight_steering_score,
            "r_guided_steering": guided_steering_score,
            "guided_steering_target": guided_target,
            "signed_heading_error": signed_heading_error,
            "r_throttle_smooth": throttle_score,
            "r_longitudinal": longitudinal,
            "lateral_offset": abs(float(lateral)),
            "is_curve": float(is_curve),
            "curvature": curvature,
            "target_speed": target_speed,
            "motion_gate": motion_gate,
            "route_completion": vehicle.navigation.route_completion,
        }

        if self._is_arrive_destination(vehicle):
            reward = self.config["success_reward"]
        elif self._is_out_of_road(vehicle):
            reward = -self.config["out_of_road_penalty"]
        elif vehicle.crash_vehicle:
            reward = -self.config["crash_vehicle_penalty"]
        elif vehicle.crash_object:
            reward = -self.config["crash_object_penalty"]
        elif vehicle.crash_sidewalk:
            reward = -self.config.get("crash_sidewalk_penalty", 0.0)

        info["step_reward"] = reward
        return reward, info


class TrafficAwareEnv(MetaDriveEnv):
    """Traffic reward with same-lane headway and intersection conflict prediction."""

    def __init__(self, config, traffic_reward_config):
        self.traffic_reward_config = traffic_reward_config
        self._intersection_decisions = {}
        self._traffic_observation_features = {}
        super().__init__(config)

    def reset(self, *args, **kwargs):
        self._intersection_decisions = {}
        self._traffic_observation_features = {}
        return super().reset(*args, **kwargs)

    def traffic_observation_features(self, vehicle_id: str = "default_agent") -> np.ndarray:
        """Normalized privileged traffic state exposed by the V2 observation wrapper."""
        return np.asarray(
            self._traffic_observation_features.get(vehicle_id, np.zeros(6, dtype=np.float32)),
            dtype=np.float32,
        )

    def reward_function(self, vehicle_id: str):
        vehicle = self.agents[vehicle_id]
        cfg = self.traffic_reward_config
        w = cfg["weights"]

        if vehicle.lane in vehicle.navigation.current_ref_lanes:
            lane = vehicle.lane
            positive_road = 1.0
        else:
            lane = vehicle.navigation.current_ref_lanes[0]
            positive_road = -1.0 if vehicle.navigation.current_road.is_negative_road() else 1.0

        long_now, lateral = lane.local_coordinates(vehicle.position)
        long_last, lateral_last = lane.local_coordinates(vehicle.last_position)
        half_width = max(vehicle.navigation.get_current_lane_width() / 2.0, 0.1)
        lateral_ratio = abs(float(lateral)) / half_width
        lane_score = float(np.exp(-2.0 * lateral_ratio**2))
        heading_score = float(np.clip(vehicle.heading_diff(lane), 0.0, 1.0))
        progress = float(np.clip((long_now - long_last) * positive_road, -1.0, 1.0))

        steering_change = abs(float(vehicle.current_action[0]) - float(vehicle.last_action[0]))
        throttle_change = abs(float(vehicle.current_action[1]) - float(vehicle.last_action[1]))
        smooth_steering = 1.0 - float(np.clip(steering_change, 0.0, 1.0))
        smooth_throttle = 1.0 - float(np.clip(throttle_change, 0.0, 1.0))

        surrounding = list(vehicle.lidar.get_surrounding_objects(vehicle))
        front_obj = None
        front_dist = float(cfg["traffic_query_distance"])
        try:
            found = FrontBackObjects.get_find_front_back_objs(
                surrounding, lane, vehicle.position, max_distance=front_dist
            )
            front_obj = found.front_object()
            front_dist = float(found.front_min_distance())
        except (AssertionError, IndexError, TypeError, ValueError):
            pass

        desired_gap = cfg["minimum_gap"] + cfg["time_headway"] * max(vehicle.speed, 0.0)
        headway_score = 0.0
        same_lane_ttc = float("inf")
        road_target = cfg["curve_target_speed"] if isinstance(lane, CircularLane) else cfg["straight_target_speed"]
        target_speed = float(road_target)
        if front_obj is not None:
            front_speed = max(float(front_obj.speed_km_h), 0.0)
            closing_speed = max((vehicle.speed_km_h - front_speed) / 3.6, 0.0)
            if closing_speed > 0.1:
                same_lane_ttc = front_dist / closing_speed
            headway_score = float(np.clip((front_dist - cfg["minimum_gap"]) / max(desired_gap, 0.1), 0.0, 1.0))
            if front_dist < cfg["adaptive_speed_distance"]:
                gap_speed = front_speed + cfg["gap_recovery_gain"] * (front_dist - desired_gap)
                target_speed = min(target_speed, max(gap_speed, 0.0))

        # Predict closest approach to every moving vehicle. This catches crossing
        # traffic at intersections even when it is not in the ego lane.
        conflict_risk = 0.0
        min_tcpa = float("inf")
        min_dcpa = float("inf")
        ego_velocity = np.asarray(vehicle.velocity_km_h, dtype=np.float64) / 3.6
        ego_position = np.asarray(vehicle.position, dtype=np.float64)
        for other in surrounding:
            if other is vehicle or not hasattr(other, "velocity_km_h"):
                continue
            relative_position = np.asarray(other.position, dtype=np.float64) - ego_position
            relative_velocity = np.asarray(other.velocity_km_h, dtype=np.float64) / 3.6 - ego_velocity
            relative_speed_sq = float(np.dot(relative_velocity, relative_velocity))
            if relative_speed_sq < 0.04:
                continue
            tcpa = float(-np.dot(relative_position, relative_velocity) / relative_speed_sq)
            if tcpa < 0.0 or tcpa > cfg["conflict_horizon"]:
                continue
            dcpa = float(np.linalg.norm(relative_position + relative_velocity * tcpa))
            if dcpa > cfg["conflict_distance"]:
                continue
            time_factor = 1.0 - tcpa / cfg["conflict_horizon"]
            distance_factor = 1.0 - dcpa / cfg["conflict_distance"]
            risk = float(np.clip(time_factor * distance_factor, 0.0, 1.0))
            if risk > conflict_risk:
                conflict_risk = risk
                min_tcpa = tcpa
                min_dcpa = dcpa

        same_lane_risk = 0.0
        if np.isfinite(same_lane_ttc):
            same_lane_risk = float(
                np.clip((cfg["safe_ttc"] - same_lane_ttc) / cfg["safe_ttc"], 0.0, 1.0)
            )
        total_risk = max(conflict_risk, same_lane_risk)
        decision = "none"
        decision_steps = 0
        stopping_distance = 0.0
        conflict_path_distance = float("inf")
        if cfg.get("commitment_enabled", False):
            previous_decision, decision_steps = self._intersection_decisions.get(vehicle_id, ("none", 0))
            if conflict_risk >= cfg["decision_risk_threshold"]:
                speed_ms = max(float(vehicle.speed), 0.0)
                stopping_distance = speed_ms**2 / (2.0 * cfg["comfortable_deceleration"])
                conflict_path_distance = speed_ms * min_tcpa if np.isfinite(min_tcpa) else float("inf")
                if previous_decision != "none" and decision_steps > 0:
                    decision = previous_decision
                    decision_steps -= 1
                else:
                    too_late_to_stop = (
                        stopping_distance + cfg["stopping_buffer"] >= conflict_path_distance
                        or min_tcpa <= cfg["go_tcpa_threshold"]
                    )
                    decision = "go" if too_late_to_stop else "yield"
                    decision_steps = int(cfg["decision_hold_steps"])
            elif previous_decision != "none" and decision_steps > 0:
                decision = previous_decision
                decision_steps -= 1
            self._intersection_decisions[vehicle_id] = (decision, decision_steps)

        if conflict_risk > 0.0:
            if decision == "go":
                target_speed = max(target_speed, cfg["intersection_go_speed"])
            else:
                target_speed = min(target_speed, cfg["intersection_yield_speed"] * (1.0 - conflict_risk))

        speed_error = abs(vehicle.speed_km_h - target_speed) / max(road_target, 1.0)
        speed_score = float(np.exp(-2.0 * speed_error**2))
        motion_gate = float(np.clip(vehicle.speed_km_h / cfg["motion_gate_speed"], 0.0, 1.0))
        brake_score = float(np.clip((1.0 - float(vehicle.current_action[1])) / 2.0, 0.0, 1.0))
        acceleration_score = float(np.clip((float(vehicle.current_action[1]) + 1.0) / 2.0, 0.0, 1.0))
        unsafe_acceleration = total_risk * max(float(vehicle.current_action[1]), 0.0)
        outward_drift = float(
            np.clip((abs(float(lateral)) - abs(float(lateral_last))) / half_width, 0.0, 1.0)
        )
        risk_lateral_deviation = total_risk * float(np.clip(lateral_ratio, 0.0, 2.0)) ** 2
        risk_outward_drift = total_risk * outward_drift
        decision_score = 0.0
        wrong_decision_action = 0.0
        if decision == "go":
            decision_score = conflict_risk * acceleration_score
            wrong_decision_action = conflict_risk * brake_score
            # Acceleration is intentional after committing to clear the junction.
            unsafe_acceleration = same_lane_risk * max(float(vehicle.current_action[1]), 0.0)
        elif decision == "yield":
            decision_score = conflict_risk * brake_score
            wrong_decision_action = conflict_risk * acceleration_score

        reward = (
            w["progress"] * progress
            + motion_gate * w["lane_keeping"] * lane_score
            + motion_gate * w["heading"] * heading_score
            + w["speed_tracking"] * speed_score
            + w["steering_smooth"] * smooth_steering
            + w["throttle_smooth"] * smooth_throttle
            + w["safe_headway"] * headway_score
            + w["yield_braking"] * total_risk * brake_score
            + w.get("decision_compliance", 0.0) * decision_score
            - w["traffic_risk"] * total_risk
            - w["unsafe_acceleration"] * unsafe_acceleration
            - w.get("risk_lateral_deviation", 0.0) * risk_lateral_deviation
            - w.get("risk_outward_drift", 0.0) * risk_outward_drift
            - w.get("decision_violation", 0.0) * wrong_decision_action
        )

        if self._is_arrive_destination(vehicle):
            reward = self.config["success_reward"]
        elif vehicle.crash_vehicle:
            reward = -self.config["crash_vehicle_penalty"]
        elif vehicle.crash_object:
            reward = -self.config["crash_object_penalty"]
        elif self._is_out_of_road(vehicle):
            reward = -self.config["out_of_road_penalty"]

        info = {
            "step_reward": reward,
            "r_progress": progress,
            "r_lane_keeping": lane_score,
            "r_heading": heading_score,
            "r_speed": speed_score,
            "r_safe_headway": headway_score,
            "r_smooth_steering": smooth_steering,
            "r_smooth_throttle": smooth_throttle,
            "front_distance": front_dist,
            "desired_gap": desired_gap,
            "same_lane_ttc": same_lane_ttc,
            "intersection_risk": conflict_risk,
            "traffic_risk": total_risk,
            "min_tcpa": min_tcpa,
            "min_dcpa": min_dcpa,
            "target_speed": target_speed,
            "unsafe_acceleration": unsafe_acceleration,
            "outward_drift": outward_drift,
            "risk_lateral_deviation": risk_lateral_deviation,
            "risk_outward_drift": risk_outward_drift,
            "intersection_decision": 1.0 if decision == "go" else -1.0 if decision == "yield" else 0.0,
            "decision_steps": decision_steps,
            "stopping_distance": stopping_distance,
            "conflict_path_distance": conflict_path_distance,
            "decision_score": decision_score,
            "wrong_decision_action": wrong_decision_action,
            "route_completion": vehicle.navigation.route_completion,
        }
        decision_value = 1.0 if decision == "go" else -1.0 if decision == "yield" else 0.0
        tcpa_normalized = (
            np.clip(min_tcpa / cfg["conflict_horizon"], 0.0, 1.0) if np.isfinite(min_tcpa) else 1.0
        )
        dcpa_normalized = (
            np.clip(min_dcpa / cfg["conflict_distance"], 0.0, 1.0) if np.isfinite(min_dcpa) else 1.0
        )
        stopping_ratio = np.clip(
            stopping_distance / max(conflict_path_distance, 0.1), 0.0, 2.0
        ) / 2.0 if np.isfinite(conflict_path_distance) else 0.0
        remaining_normalized = np.clip(
            decision_steps / max(float(cfg.get("decision_hold_steps", 1)), 1.0), 0.0, 1.0
        )
        self._traffic_observation_features[vehicle_id] = np.asarray(
            [decision_value, total_risk, tcpa_normalized, dcpa_normalized, stopping_ratio, remaining_normalized],
            dtype=np.float32,
        )
        return reward, info

