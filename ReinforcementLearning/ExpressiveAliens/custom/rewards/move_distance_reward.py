from custom.rewards.custom_reward import CustomReward
from simulation.utils import Utils
import numpy as np

# specify rewards
class MoveDistanceReward(CustomReward):
    def __init__(self):
        super().__init__()

        self.body_pos = None
        self.move_distance = 0.0
        
    def reset(self):
        self.body_pos = None
        
    def calc_value(self):
        
        #print("MoveDistanceReward calc_value begin")
        
        body_pos = Utils.average_body_position(self.env.agent)
        
        #print("body_pos ", body_pos)

        # calculate walk distance
        if self.body_pos is not None:
            old_pos_xy = np.array(self.body_pos[0], self.body_pos[1])
            new_pos_xy = np.array(body_pos[0], body_pos[1])
            self.move_distance = np.linalg.norm(new_pos_xy-old_pos_xy) / (self.env.sim_time_step * self.env.sim_sub_steps)
        
            #print("old_pos_xy ", old_pos_xy)
            #print("new_pos_xy ", new_pos_xy)
            #print("self.move_distance ", self.move_distance)
        
        else:
            self.move_distance = 0.0
            
        self.body_pos = body_pos
        self.value = self.move_distance 
        
        #print("self.value ", self.value)
        
        #print("MoveDistanceReward calc_value end")
