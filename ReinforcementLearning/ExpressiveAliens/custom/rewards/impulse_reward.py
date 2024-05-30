from custom.rewards.custom_reward import CustomReward
from simulation.utils import Utils
from analysis.analysis import Analysis
from common.ringbuffer import RingBuffer
import numpy as np

# specify rewards
class ImpulseReward(CustomReward):
    
    def __init__(self):
        super().__init__()
        
        self.min_value = 0.0
        self.max_value = 100.0
        self.target_value = 1.0 
        self.value_reward_scale = 1.0
        
        self.part_names = []
        self.parts = []
        self.normalised_masses = None

    
    def init(self):
        self.parts = Utils.get_agent_parts(self.env.agent, self.part_names)
        self.normalised_masses = Utils.calc_normalised_massed(self.parts)
        
        super().init()
        
    def reset(self):
        super().reset()
    
    def calc_value(self):
        agent = self.env.agent
        
        # get body part velocities
        part_count = len(self.parts)
        velocities = [ part.get_velocity()[:3]  for part in self.parts ]
        velocities = np.stack(velocities, axis=0)
        
        #get body part scalar speeds
        velocities = np.expand_dims(velocities, axis=0)
        speeds = Analysis.joint_speeds(velocities)
        
        # get body part impulses
        self.value = speeds * self.normalised_masses

        # sum all impulses
        self.value = np.sum(self.value)

    
    """
    def get_reward(self):
        super().get_reward()

        agent = self.env.agent
        
        # get body part velocities
        part_count = len(self.parts)
        velocities = [ part.get_velocity()[:3]  for part in self.parts ]
        velocities = np.stack(velocities, axis=0)
        
        #get body part scalar speeds
        velocities = np.expand_dims(velocities, axis=0)
        speeds = Analysis.joint_speeds(velocities)
        
        # get body part impulses
        impulse = speeds * self.normalised_masses

        # sum all impulses
        impulse = np.sum(impulse)

        # normalise impulse
        impulse = min(impulse, self.max_impulse)
        impulse /= self.max_impulse
        
        
        # difference to target impulse
        diff_impulse = abs(self.target_impulse - impulse)
        
        self.reward = self.reward_scale * (1.0 - diff_impulse)

        #print("diff_effort ", diff_effort, " reward ", self.reward)

        return self.reward
    """
