from custom.rewards.custom_reward import CustomReward
from analysis.analysis import Analysis
from common.ringbuffer import RingBuffer
from simulation.utils import Utils
import numpy as np

# specify rewards
class MoveAreaReward(CustomReward):
    def __init__(self):
        super().__init__()

        self.body_position_history_length = 100
        self.body_position_history = None
        self.min_history_length = 4
        self.current_history_length = 0
        
        # for normalisation
        #self.position_limits = np.array([[-10.0, -10.0, -10.0],[10.0, 10.0, 10.0]], dtype=np.float32)
        
        
    def init(self):
        self.body_position_history = RingBuffer(self.body_position_history_length + 50, np.zeros(shape=(1, 3), dtype=np.float32))
        super().init()
        
    def reset(self):
        if self.body_position_history != None:
            
            agent_body_pos = Utils.average_body_position(self.env.agent)
            agent_body_pos = np.expand_dims(agent_body_pos, axis=0)
            self.body_position_history.clear(agent_body_pos.astype(np.float32))
            self.current_history_length = 0
            
        super().reset()
    
    def calc_value(self):
        agent_body_pos = Utils.average_body_position(self.env.agent)

        #print("agent_body_pos  ", agent_body_pos )
        
        agent_body_pos = np.expand_dims(agent_body_pos, axis=0)
        
        #print("agent_body_pos ", agent_body_pos)
        
        self.body_position_history.write(agent_body_pos.astype(np.float32))
        self.current_history_length += 1
        
        #print("body_position_history ", self.body_position_history.mBuffer)
        
        if self.current_history_length >= self.min_history_length:
            agent_walk_area = Analysis.area_travelled(self.body_position_history.read(self.body_position_history_length))
            agent_walk_area = (agent_walk_area.flatten())[0]
        else:
            agent_walk_area = 0.0

        #print("agent_walk_area ", agent_walk_area)
        
        self.value = agent_walk_area
