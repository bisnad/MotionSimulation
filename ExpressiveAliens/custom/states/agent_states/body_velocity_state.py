from custom.states.custom_state import CustomState
import numpy as np

class BodyVelocityState(CustomState):
    def __init__(self):
        super().__init__()
        self.velocity_scale = 0.3

    def calc_state(self):
        if self.initialized  == False:
            self.init()
        
        physics = self.agent.physics
        body = self.agent.body
            
        # position and orientation of body
        body_pose = body.get_pose()
        
        # body orientation (as euler angles)
        body_rpy = physics.getEulerFromQuaternion(body_pose[3:])
        r, p, yaw = body_rpy
        
        # body linear and angular velocity relative to body yaw
        rot_speed = np.array(
            [[np.cos(-yaw), -np.sin(-yaw), 0],
             [np.sin(-yaw), np.cos(-yaw), 0],
             [		0,			 0, 1]])
        
        
        # relative linear body velocity
        vx, vy, vz = np.dot(rot_speed, body.get_velocity()[:3])
        
        # relative angular body velocity
        vr, vp, vw = np.dot(rot_speed, body.get_velocity()[3:])
        
        velocity = np.array([vx, vy, vz, vr, vp, vw], dtype=np.float32)
        
        velocity *= self.velocity_scale

        self.state = velocity
        
        return self.state
    
