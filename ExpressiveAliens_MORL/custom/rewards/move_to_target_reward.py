from custom.rewards.custom_reward import CustomReward
import numpy as np


class MoveToTargetReward(CustomReward):
    """
    Continuing-task reward:
    - Outside the target radius:
        positive for movement toward target,
        near zero for sideways motion,
        negative for motion away from target.
    - Inside the target radius:
        rewards standing still,
        penalizes motion,
        optionally penalizes drifting away from the target center.
    """

    def __init__(
        self,
        target_radius=0.10,
        approach_scale=1.0,
        stillness_scale=1.0,
        drift_scale=0.5,
        inside_target_bonus=0.5,
        only_positive_approach=False,
    ):
        super().__init__()

        self.target_radius = float(target_radius)
        self.approach_scale = float(approach_scale)
        self.stillness_scale = float(stillness_scale)
        self.drift_scale = float(drift_scale)
        self.inside_target_bonus = float(inside_target_bonus)
        self.only_positive_approach = bool(only_positive_approach)

        self.prev_body_pos_xy = None
        self.value = 0.0

    def reset(self):
        self.prev_body_pos_xy = None
        self.value = 0.0

    def calc_value(self):
        agent = self.env.agent
        target = self.env.target

        agent_body_pose = agent.body.get_pose()
        target_body_pose = target.body.get_pose()

        agent_pos_xy = np.array(
            [agent_body_pose[0], agent_body_pose[1]],
            dtype=np.float32
        )
        target_pos_xy = np.array(
            [target_body_pose[0], target_body_pose[1]],
            dtype=np.float32
        )

        dt = float(self.env.sim_time_step * self.env.sim_sub_steps)
        if dt <= 0.0:
            self.value = 0.0
            return

        if self.prev_body_pos_xy is None:
            self.prev_body_pos_xy = agent_pos_xy.copy()
            self.value = 0.0
            return

        delta_xy = agent_pos_xy - self.prev_body_pos_xy
        self.prev_body_pos_xy = agent_pos_xy.copy()

        move_velocity_xy = delta_xy / dt
        speed = np.linalg.norm(move_velocity_xy)

        to_target_vec = target_pos_xy - agent_pos_xy
        dist_to_target = np.linalg.norm(to_target_vec)

        # Outside target region: reward motion toward target
        if dist_to_target > self.target_radius:
            if dist_to_target < 1e-8:
                self.value = 0.0
                return

            to_target_dir = to_target_vec / (dist_to_target + 1e-8)
            projected_speed_toward_target = np.dot(move_velocity_xy, to_target_dir)

            reward = self.approach_scale * projected_speed_toward_target

            if self.only_positive_approach:
                reward = max(0.0, reward)

            self.value = reward
            return

        # Inside target region: reward standing still
        # Higher reward when speed is low
        stillness_reward = self.stillness_scale * max(0.0, 1.0 - speed)
        center_reward = self.inside_target_bonus - self.drift_scale * dist_to_target
        self.value = stillness_reward + center_reward