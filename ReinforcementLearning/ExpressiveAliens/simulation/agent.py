import numpy as np
import gym, gym.spaces, gym.utils
from simulation.thing import Thing

class Agent(Thing):
    def __init__(self, name, body_file, body_index=0):
        super(Agent, self).__init__(name, body_file, body_index)
        
        self.power = 1.0
        self.alive = 1.0
        self.state = None
                
    def reset(self):
        super(Agent, self).reset()
        
    def get_alive(self, *args):
        return self.alive
    
    def calc_state(self, *args):
        return self.state
        

    