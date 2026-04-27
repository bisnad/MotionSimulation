from custom.rewards.custom_reward import CustomReward
from simulation.utils import Utils
import numpy as np

# specify rewards
class MoveToTargetReward(CustomReward):
    def __init__(self):
        super().__init__()

        self.prev_agent_pos = None
        self.dir_dist_cost = 1.0
        
    def reset(self):
        self.prev_agent_pos = None
        self.value = 0.0
        
    def calc_value(self):
        agent_pos = np.array(Utils.average_body_position(self.env.agent), dtype=np.float32)
        target_pos = np.array(Utils.average_body_position(self.env.target), dtype=np.float32)

        new_pos_xy = agent_pos[:2]

        if self.prev_agent_pos is None:
            self.prev_agent_pos = agent_pos
            self.value = 0.0
            return

        old_pos_xy = np.array(self.prev_agent_pos[:2], dtype=np.float32)
        move_vec = new_pos_xy - old_pos_xy
        move_dist = np.linalg.norm(move_vec)

        if move_dist <= 1e-8:
            self.value = 0.0
            self.prev_agent_pos = agent_pos
            return

        move_dir = move_vec / move_dist

        target_vec = np.array(target_pos[:2] - new_pos_xy, dtype=np.float32)  # agent -> target
        target_dist = np.linalg.norm(target_vec)

        if target_dist <= 1e-8:
            self.value = 0.0
            self.prev_agent_pos = agent_pos
            return

        target_dir = target_vec / target_dist
        alignment = float(np.dot(move_dir, target_dir))

        self.value = self.dir_dist_cost * alignment * move_dist
        self.prev_agent_pos = agent_pos

