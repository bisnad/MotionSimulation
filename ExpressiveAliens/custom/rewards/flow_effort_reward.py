from custom.rewards.custom_reward import CustomReward
from simulation.utils import Utils
from analysis.analysis import Analysis
from common.ringbuffer import RingBuffer
import numpy as np

# specify rewards
class FlowEffortReward(CustomReward):
    
    def __init__(self):
        super().__init__()
        
        self.value = 0.0
        self.min_value = 0.0
        self.max_value = 10000.0
        self.target_value = 1.0 
        self.abs_difference_value = False
        
        self.value_reward_scale = 1.0 
        self.reward = 0.0 
        self.reward_scale = 1.0
        
        self.part_names = []
        self.parts = []
        self.normalised_masses = None

        self.history_length = 10
        self.jerk_history = None
        self.joint_velocities = None
        self.joint_accelerations = None
        self.timestep = 0.0

    def init(self):
        self.parts = Utils.get_agent_parts(self.env.agent, self.part_names)
        self.normalised_masses = Utils.calc_normalised_masses(self.parts)
        
        part_count = len(self.parts)
        joint_dim = 3
        self.jerk_history  = RingBuffer(self.history_length, np.zeros(shape=(part_count, joint_dim), dtype=np.float32))
        
        super().init()

        
    def reset(self):
        if self.jerk_history != None:
            part_count = len(self.parts)
            joint_dim = 3
            self.jerk_history.clear(np.zeros(shape=(part_count, joint_dim) ,dtype=np.float32))
        
        self.joint_velocities = None
        
        super().reset()

    def calc_value(self):
        agent = self.env.agent
        
        # get world velocities
        part_count = len(self.parts)
        new_velocities = [ part.get_velocity()[:3]  for part in self.parts ]
        new_velocities = np.stack(new_velocities, axis=0)
        
        # get new accelerations
        if self.joint_velocities is not None:
            new_accelerations = (self.joint_velocities - new_velocities) / (self.env.sim_time_step * self.env.sim_sub_steps)
        else:
            new_accelerations = np.zeros(shape=(part_count, 3), dtype=np.float32)
         
        # get new jerk
        if self.joint_accelerations is not None:
            jerks = (self.joint_accelerations - new_accelerations) / (self.env.sim_time_step * self.env.sim_sub_steps)
        else:
            jerks = np.zeros(shape=(part_count, 3), dtype=np.float32)
        
        self.joint_velocities = new_velocities   
        self.joint_accelerations = new_accelerations   

        
        # add jerks to ring buffer
        self.jerk_history.write(jerks)
        
        #print("jerk_history ", self.jerk_history.read(self.history_length))
        
        # calculate time effort
        flow_effort = Analysis.flow_effort(self.jerk_history.read(self.history_length), self.normalised_masses)
        
        self.value = flow_effort
