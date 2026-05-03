from custom.rewards.custom_reward import CustomReward
from simulation.utils import Utils
import numpy as np
from scipy.spatial.transform import Rotation as R


class TargetAlignmentReward(CustomReward):
    def __init__(self):
        super().__init__()

        self.target_align_cost = 1.0
        self.value = 0.0

        # Set this to the agent's forward axis in local/body coordinates.
        # Common choices are [1, 0, 0] or [0, 0, 1] depending on the model.
        self.body_forward_axis = np.array([1.0, 0.0, 0.0], dtype=np.float32)

    def reset(self):
        self.value = 0.0

    def calc_value(self):
        agent = self.env.agent

        # position and orientation of body
        agent_pose = agent.body.get_pose()
        agent_pos = np.array(agent_pose[:3], dtype=np.float32)
        agent_rot = np.array(agent_pose[3:], dtype=np.float32)  # expected [x, y, z, w]

        target_pos = np.array(
            Utils.average_body_position(self.env.target), dtype=np.float32
        )

        to_target_vec = target_pos - agent_pos
        target_dist = np.linalg.norm(to_target_vec)

        if target_dist < 1e-8:
            self.value = self.target_align_cost
            return

        to_target_dir = to_target_vec / target_dist

        # Rotate the body-forward axis into world space using the agent quaternion
        rot = R.from_quat(agent_rot)
        agent_forward_world = rot.apply(self.body_forward_axis)

        forward_norm = np.linalg.norm(agent_forward_world)
        
        if forward_norm < 1e-8:
            self.value = 0.0
            return

        agent_forward_world = agent_forward_world / forward_norm

        # Alignment in [-1, 1]:
        #  1.0 -> fully facing target
        #  0.0 -> orthogonal
        # -1.0 -> facing away
        alignment = float(np.dot(agent_forward_world, to_target_dir))

        reward = self.target_align_cost * ((alignment + 1.0) / 2.0)

        self.value = reward