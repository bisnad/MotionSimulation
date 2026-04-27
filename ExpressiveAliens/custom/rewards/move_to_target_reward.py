from custom.rewards.custom_reward import CustomReward
from simulation.utils import Utils
import numpy as np


class MoveToTargetReward(CustomReward):
    def __init__(self):
        super().__init__()

        self.prev_agent_pos = None

        # approach reward
        self.dir_dist_cost = 1.0

        # goal / hold behavior
        self.goal_radius = 0.15
        self.goal_bonus = 1.0
        self.stay_bonus = 0.5
        self.leave_penalty = 1.0
        self.stillness_cost = 0.5

    def reset(self):
        self.prev_agent_pos = None
        self.value = 0.0

    def calc_value(self):
        agent_pos = np.array(Utils.average_body_position(self.env.agent), dtype=np.float32)
        target_pos = np.array(Utils.average_body_position(self.env.target), dtype=np.float32)

        agent_xy = agent_pos[:2]
        target_xy = target_pos[:2]

        if self.prev_agent_pos is None:
            self.prev_agent_pos = agent_pos
            self.value = 0.0
            return

        prev_xy = np.array(self.prev_agent_pos[:2], dtype=np.float32)

        move_vec = agent_xy - prev_xy
        move_dist = np.linalg.norm(move_vec)

        to_target_vec = target_xy - agent_xy
        target_dist = np.linalg.norm(to_target_vec)

        prev_target_dist = np.linalg.norm(target_xy - prev_xy)

        reward = 0.0

        # Case 1: inside goal region -> reward staying there
        if target_dist <= self.goal_radius:
            reward += self.goal_bonus

            # reward staying close to center of target region
            proximity = 1.0 - (target_dist / (self.goal_radius + 1e-8))
            reward += self.stay_bonus * proximity

            # penalize unnecessary movement while inside goal region
            reward -= self.stillness_cost * move_dist

            # extra penalty if agent was in goal region and moved farther away
            if prev_target_dist <= self.goal_radius and target_dist > prev_target_dist:
                reward -= self.leave_penalty * (target_dist - prev_target_dist)

        # Case 2: outside goal region -> directional movement reward
        else:
            if move_dist > 1e-8:
                move_dir = move_vec / move_dist
                target_dir = to_target_vec / (target_dist + 1e-8)
                alignment = float(np.dot(move_dir, target_dir))
                reward += self.dir_dist_cost * alignment * move_dist

            # optional small progress shaping
            reward += (prev_target_dist - target_dist)

        self.value = reward
        self.prev_agent_pos = agent_pos