from custom.states.custom_state import CustomState
import numpy as np

class BodyRotationState(CustomState):
    def __init__(self):
        super().__init__()
        self.rotation_as_euler = True
        self.rotation_scale = 1.0

    def calc_state(self):
        if self.initialized  == False:
            self.init()
        
        physics = self.agent.physics
        body = self.agent.body
        
        # position and orientation of body
        body_pose = body.get_pose()

        # body orientation (as euler angles)
        if self.rotation_as_euler == True:
            body_rpy = physics.getEulerFromQuaternion(body_pose[3:])
            r, p, yaw = body_rpy
            self.state = np.array([r, p, yaw], dtype=np.float32)
        else:
            self.state  = body_pose[3:]
            
        self.state *= self.rotation_scale
        
        return self.state
    
