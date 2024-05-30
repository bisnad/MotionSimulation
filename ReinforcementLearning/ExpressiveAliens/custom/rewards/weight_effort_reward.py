from custom.rewards.custom_reward import CustomReward
from simulation.utils import Utils
from analysis.analysis import Analysis
from common.ringbuffer import RingBuffer
import numpy as np

# specify rewards
class WeightEffortReward(CustomReward):
    
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
        self.speed_history = None
        
    
    def init(self):
        self.parts = Utils.get_agent_parts(self.env.agent, self.part_names)
        self.normalised_masses = Utils.calc_normalised_masses(self.parts)
        
        part_count = len(self.parts)
        self.speed_history  = RingBuffer(self.history_length, np.zeros(shape=(part_count, 1), dtype=np.float32))
        
        super().init()

        
    def reset(self):
        if self.speed_history != None:
            part_count = len(self.parts)
            self.speed_history.clear(np.zeros(shape=(part_count, 1) ,dtype=np.float32))
            
        super().reset()

    def calc_value(self):
        #print("weight effort")
        
        agent = self.env.agent
        
        # get linear velocities
        velocities = [ part.get_velocity()[:3]  for part in self.parts ]
        velocites = np.stack(velocities, axis=0)
        velocities = np.expand_dims(velocities, axis=0)
        
        #print("velocities ", velocities)
        
        # get linear speeds
        speeds = Analysis.joint_speeds(velocities)
        speeds = np.squeeze(speeds, axis=0)
        
        #print("speeds ", speeds)
        
        # add speeds to ring buffer
        self.speed_history.write(speeds)
        
        #print("speed_history ", self.speed_history.read(self.history_length))
        
        # calculate weight effort
        kinetic_energy = Analysis.kinetic_energy(self.speed_history.read(self.history_length), self.normalised_masses)
        
        #print("kinetic_energy ", kinetic_energy)
        
        weight_effort = Analysis.weight_effort(kinetic_energy)
        
        self.value = weight_effort
        
        #print("weight effort direct value", self.value )

    
    """
    def get_reward(self):
        super().get_reward()

        agent = self.env.agent
        
        # get linear velocities
        velocities = [ part.get_velocity()[:3]  for part in self.parts ]
        velocites = np.stack(velocities, axis=0)
        velocities = np.expand_dims(velocities, axis=0)
        
        #print("velocities ", velocities)
        
        # get linear speeds
        speeds = Analysis.joint_speeds(velocities)
        speeds = np.squeeze(speeds, axis=0)
        
        #print("speeds ", speeds)
        
        # add speeds to ring buffer
        self.speed_history.write(speeds)
        
        #print("speed_history ", self.speed_history.read(self.history_length))
        
        # calculate weight effort
        kinetic_energy = Analysis.kinetic_energy(self.speed_history.read(self.history_length), self.normalised_masses)
        
        #print("kinetic_energy ", kinetic_energy)
        
        weight_effort = Analysis.weight_effort(kinetic_energy)
        
        #print("weight_effort ", weight_effort)
        
        weight_effort = min(weight_effort, self.max_weight_effort)
        weight_effort /= self.max_weight_effort
        
        #print("weight_effort ", weight_effort)
        
        # difference to target_weight_effort
        diff_effort = abs(self.target_weight_effort - weight_effort)

        
        self.reward = self.weight_effort_reward * (1.0 - diff_effort)
        
        self.reward *= self.reward_scale

        #print("diff_effort ", diff_effort, " reward ", self.reward)

        return self.reward
"""


