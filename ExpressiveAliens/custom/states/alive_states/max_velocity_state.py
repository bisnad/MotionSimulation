"""
max velocity alive state
detects if the translational and rotational speed of the agent base is higher than some corresponing limits
If the one of the limits is exceeded, returns alife = 0
"""


from custom.states.custom_state import CustomState
import numpy as np

class MaxVelocityState(CustomState):
    def __init__(self):
        super().__init__()
        
        self.max_linear_speed = 40.0
        self.max_angular_speed = 100.0
        self.state = np.zeros([1], dtype=np.float32)
        
        # debug
        self.max_linear_speed2 = 0.0
        self.max_angular_speed2 = 0.0

    def init(self):
        self.initialized = True

    def calc_state(self):
        if self.initialized  == False:
            self.init()
            
        self.state[0] = 0.0
        
        body_velocity = self.agent.body.get_velocity()
        linear_velocity = body_velocity[:3]
        angular_velocity = body_velocity[3:]
        
        linear_speed = np.linalg.norm(linear_velocity)
        angular_speed = np.linalg.norm(angular_velocity)
        
        #print("lin_speed ", linear_speed, " max ", self.max_linear_speed )
        #print("ang_speed ", angular_speed, " max ", self.max_angular_speed )
        
        # debug
        if linear_speed > self.max_linear_speed2 :
            self.max_linear_speed2  = linear_speed
            print("max_lin ", self.max_linear_speed2)
            
        if angular_speed > self.max_angular_speed2 :
            self.max_angular_speed2  = angular_speed
            print("max_ang ", self.max_angular_speed2)
        

        if linear_speed > self.max_linear_speed :
            self.state[0] = -1.0
        if angular_speed > self.max_angular_speed :
            self.state[0] = -1.0
        
        return self.state
    
