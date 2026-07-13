import numpy as np
import gym, gym.spaces, gym.utils
from simulation.body import Body
from simulation.body_loader import BodyLoader


class Thing:
    def __init__(self, name, body_file, body_index=0):
        self.name = name
        self.body_file = body_file
        self.body_index = body_index
        self.body = None
        self.power = 0.0
        self.physics = None
        self.action_space = None
        self.observation_space = None
        self.reset_position = None
        self.reset_orientation = None
        self.action = None
        
    def set_reset_position(self, reset_position):
        
        #print("Thing name ", self.name, " reset pos ", reset_position)
        
        self.reset_position = reset_position
    
    def set_reset_orientation(self,  reset_orientation):
        self.reset_orientation = reset_orientation
    
    def reset(self):      
        assert(self.physics != None)

        if self.body == None:
            bodies = BodyLoader.load(self.body_file, self.physics)
            assert(self.body_index < len(bodies))
            self.body = bodies[self.body_index]
        
        self.body.reset()
        
        if self.action_space == None:
            action_dim = len(self.body.active_joints)
            
            if action_dim > 0:
                high = np.ones([action_dim])
                self.action_space = gym.spaces.Box(-high, high)
                
        if self.reset_position:
            self.body.reset_position(self.reset_position)
        
        if self.reset_orientation:
            self.body.reset_orientation(self.reset_orientation)
            
    def get_action_space(self):
        return self.action_space
    
    def get_observation_space(self):
        return self.observation_space
    
    def set_power(self, power):
        self.power = power
    
    def apply_action(self, action):
        self.action = action
        assert (np.isfinite(action).all())
        for n, joint in enumerate(self.body.active_joints):
            joint.set_torque(self.power * joint.power_coeff * float(np.clip(action[n], -1, +1)))
    