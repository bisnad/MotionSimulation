from custom.rewards.custom_reward import CustomReward
import numpy as np
import math


class TargetAlignmentReward(CustomReward):
    def __init__(self):
        super().__init__()

        self.misalignment_cost = -1.0
        self.value = 0.0

    def reset(self):
        self.value = 0.0

    def calc_value(self):
        agent = self.env.agent

        agent_body_pose = agent.body.get_pose()
        target_body_pose = self.env.target.body.get_pose()

        agent_body_rpy = agent.physics.getEulerFromQuaternion(agent_body_pose[3:])
        agent_body_yaw = agent_body_rpy[2]

        target_pos_xy = np.array(target_body_pose[:2], dtype=np.float32)
        agent_pos_xy = np.array(agent_body_pose[:2], dtype=np.float32)
        to_target_vec = target_pos_xy - agent_pos_xy
        to_target_dist = np.linalg.norm(to_target_vec)

        if to_target_dist < 1e-3:
            pass

        to_target_dir = to_target_vec / to_target_dist

        #print("agent_xy ", agent_pos_xy, " target_xy ", target_pos_xy, " dir ", to_target_dir)

        to_target_yaw = math.atan2(to_target_dir[1], to_target_dir[0])

        yaw_diff = to_target_yaw - agent_body_yaw
        yaw_diff = (yaw_diff + math.pi) % (2 * math.pi) - math.pi
        
        #yaw_alignment = abs(yaw_diff) / math.pi

        # Alignment score: 1 at perfect alignment, 0 at 180° off
        yaw_alignment = 1.0 - abs(yaw_diff) / math.pi  # in [0, 1]


        self.value = self.misalignment_cost * yaw_alignment

        #print("agent_yaw ", agent_body_yaw, " to_target_yaw ", to_target_yaw, " diff ", yaw_diff, " align ", yaw_alignment, " value ", self.value)