from custom.rewards.custom_reward import CustomReward
from simulation.utils import Utils
import numpy as np

# specify rewards
class MoveDirectionReward(CustomReward):
    def __init__(self):
        super().__init__()

        self.direction_cost = 1.0
        
    def reset(self):
        self.body_pos = None
        
    def calc_value(self):

        agent_pos = Utils.average_body_position(self.env.agent)
        target_pos = Utils.average_body_position(self.env.target)

        target_pos = np.array(target_pos[:2], dtype=np.float32)

        # desired direction: from origin to target
        target_dir = target_pos / (np.linalg.norm(target_pos) + 1e-8)

        agent_vel = self.env.agent.body.get_velocity()[:3]
        agent_vel = np.array(agent_vel[:2], dtype=np.float32)
        agent_dir = agent_vel / (np.linalg.norm(agent_vel) + 1e-8)

        agent_target_dir_alignment = float(np.dot(agent_dir, target_dir))
        
        self.value = agent_target_dir_alignment * self.direction_cost

