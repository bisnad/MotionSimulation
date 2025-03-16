from custom.rewards.custom_reward import CustomReward
from simulation.utils import Utils
from analysis.analysis import Analysis
from common.ringbuffer import RingBuffer
import numpy as np

# specify rewards
class SpaceEffortReward(CustomReward):
    
    def __init__(self):
        super().__init__()
        
        self.value = 0.0
        self.min_value = 0.0
        self.max_value = 10.0
        self.target_value = 1.0 
        self.abs_difference_value = False
        
        self.value_reward_scale = 1.0 
        self.reward = 0.0 
        self.reward_scale = 1.0
        
        self.part_names = []
        self.parts = []
        self.normalised_masses = None

        self.history_length = 10
        self.position_history = None

        
    def init(self):
        self.parts = Utils.get_agent_parts(self.env.agent, self.part_names)
        self.normalised_masses = Utils.calc_normalised_masses(self.parts)
        
        part_count = len(self.parts)
        joint_dim = 3
        self.position_history  = RingBuffer(self.history_length, np.zeros(shape=(part_count, joint_dim), dtype=np.float32))
        
        super().init()

        
    def reset(self):
        if self.position_history != None:
            part_count = len(self.parts)
            joint_dim = 3
            self.position_history.clear(np.zeros(shape=(part_count, joint_dim) ,dtype=np.float32))
            
        super().reset()
    
    def calc_value(self):
        agent = self.env.agent
        
        # get world positions
        positions = [ part.get_position()  for part in self.parts ]
        positions = np.stack(positions, axis=0)
    
        #print("positions ", positions)
        
        # add positions to ring buffer
        self.position_history.write(positions)
        
        #print("position_history ", self.position_history.read(self.history_length))
        
        # calculate space effort
        space_effort = Analysis.space_effort(self.position_history.read(self.history_length), self.normalised_masses)
        
        self.value = space_effort


    
    """
    def get_reward(self):
        super().get_reward()

        agent = self.env.agent
        
        # get world positions
        positions = [ part.get_position()  for part in self.parts ]
        positions = np.stack(positions, axis=0)
    
        #print("positions ", positions)
        
        # add positions to ring buffer
        self.position_history.write(positions)
        
        #print("position_history ", self.position_history.read(self.history_length))
        
        # calculate space effort
        space_effort = Analysis.space_effort(self.position_history.read(self.history_length), self.normalised_masses)
        
        
        #print("space_effort ", space_effort)
        
        space_effort = min(space_effort, self.max_space_effort)
        space_effort /= self.max_space_effort
        
        #print("space_effort ", space_effort)
        
        # difference to target_space_effort
        diff_effort = abs(self.target_space_effort - space_effort)

        
        self.reward = self.space_effort_reward * (1.0 - diff_effort)
        
        self.reward *= self.reward_scale

        #print("diff_effort ", diff_effort, " reward ", self.reward)

        return self.reward
    """
