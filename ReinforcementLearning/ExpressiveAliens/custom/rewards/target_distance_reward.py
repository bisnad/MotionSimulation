from custom.rewards.custom_reward import CustomReward
from simulation.utils import Utils
import numpy as np

# specify rewards
class TargetDistanceReward(CustomReward):
    def __init__(self):
        super().__init__()

        self.potential = None
        self.target_dist = None
        
    def reset(self):
        self.potential = None
        self.target_dist = None
 
    """
    def calc_value(self):
        
        #print("TargetDistanceReward calc_value")
    
        
        agent_pos = self.env.agent.body.get_position()
        target_pos = self.env.target.body.get_position()
        
        #print("agent_pos ", agent_pos)
        #print("target_pos ", target_pos)
        
        walk_target_dist = np.linalg.norm([target_pos[1] - agent_pos[1], target_pos[0] - agent_pos[0]])
        
        #print("walk_target_dist ", walk_target_dist)
        #print("self.env.sim_time_step ", self.env.sim_time_step)
        #print("self.env.sim_sub_steps ", self.env.sim_sub_steps)
        
        potential = walk_target_dist / (self.env.sim_time_step * self.env.sim_sub_steps)
        
        #print("potential ", potential)
        
        if self.potential is not None:
            progress = float(self.potential - potential)
        else:
            progress = 0.0
        
        #print("progress ", progress)
        
        self.potential = potential
        
        self.value = progress
        
        print("TargetDistanceReward value ", self.value)
    """

    def calc_value(self):
        
        #print("TargetDistanceReward calc_value begin")
        
        #agent_pos = self.env.agent.body.get_position()
        #target_pos = self.env.target.body.get_position()
        
        agent_pos = Utils.average_body_position(self.env.agent)
        target_pos = Utils.average_body_position(self.env.target)
        
        #print("agent_pos ", agent_pos)
        #print("target_pos ", target_pos)
        
        target_dist = np.linalg.norm([target_pos[1] - agent_pos[1], target_pos[0] - agent_pos[0]])
        
        #print("old target dist ", self.target_dist)
        #print("new target dist ", target_dist)
        
        if self.target_dist is not None:     
            progress = self.target_dist - target_dist
            
            #print("progress non-scaled ", progress)
            
            progress = progress / (self.env.sim_time_step * self.env.sim_sub_steps)
            
            #print("progress scaled ", progress)
        else:
            progress = 0.0
            
        #print("final progress ", progress)
            
            
        self.target_dist = target_dist
        self.value = progress
        
        #print("TargetDistanceReward value ", self.value)
        
        #print("TargetDistanceReward calc_value end")
