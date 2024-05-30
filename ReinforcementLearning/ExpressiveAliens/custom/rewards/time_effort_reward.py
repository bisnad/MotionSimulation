from custom.rewards.custom_reward import CustomReward
from simulation.utils import Utils
from analysis.analysis import Analysis
from common.ringbuffer import RingBuffer
import numpy as np

# specify rewards
class TimeEffortReward(CustomReward):
    
    def __init__(self):
        super().__init__()
        
        self.value = 0.0
        self.min_value = 0.0
        self.max_value = 100.0
        self.target_value = 1.0 
        self.abs_difference_value = False
        
        self.value_reward_scale = 1.0 
        self.reward = 0.0 
        self.reward_scale = 1.0
        
        self.part_names = []
        self.parts = []
        self.normalised_masses = None

        self.history_length = 10
        self.acceleration_history = None
        self.joint_velocities = None
        self.timestep = 0.0
    
        
    def init(self):
        self.parts = Utils.get_agent_parts(self.env.agent, self.part_names)
        self.normalised_masses = Utils.calc_normalised_masses(self.parts)
        
        part_count = len(self.parts)
        joint_dim = 3
        self.acceleration_history  = RingBuffer(self.history_length, np.zeros(shape=(part_count, joint_dim), dtype=np.float32))
        
        super().init()
        
    def reset(self):
        if self.acceleration_history != None:
            part_count = len(self.parts)
            joint_dim = 3
            self.acceleration_history.clear(np.zeros(shape=(part_count, joint_dim) ,dtype=np.float32))
        
        self.joint_velocities = None
        
        super().reset()

    def calc_value(self):
        agent = self.env.agent
        
        # get world velocities
        part_count = len(self.parts)
        new_velocities = [ part.get_velocity()[:3]  for part in self.parts ]
        new_velocities = np.stack(new_velocities, axis=0)
        
        #print("new_velocities ", new_velocities)
        #print("self.joint_velocities ", self.joint_velocities)
        
        if self.joint_velocities is not None:
            accelerations = (self.joint_velocities - new_velocities) / (self.env.sim_time_step * self.env.sim_sub_steps)
        else:
            accelerations = np.zeros(shape=(part_count, 3), dtype=np.float32)

        self.joint_velocities = new_velocities
    
        #print("accelerations ", accelerations)
        
        # add positions to ring buffer
        self.acceleration_history.write(accelerations)
        
        #print("acceleration_history ", self.acceleration_history.read(self.history_length))
        
        # calculate time effort
        time_effort = Analysis.time_effort(self.acceleration_history.read(self.history_length), self.normalised_masses)
        
        self.value = time_effort
