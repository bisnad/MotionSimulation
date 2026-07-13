from custom.rewards.custom_reward import CustomReward
import numpy as np


class BodyVelocityAlignmentReward(CustomReward):
    def __init__(self):
        super().__init__()

        self.misalignment_cost = -1.0
    
    def calc_value(self):
        agent = self.env.agent

        # position and orientation of body
        body_pose = agent.body.get_pose()
        
        # body orientation (as euler angles)
        body_rpy = agent.physics.getEulerFromQuaternion(body_pose[3:])
        
        r, p, yaw = body_rpy
            
        # body linear and angular velocity relative to body yaw
        rot_speed = np.array(
            [[np.cos(-yaw), -np.sin(-yaw), 0],
             [np.sin(-yaw), np.cos(-yaw), 0],
             [		0,			 0, 1]])
        
        # relative linear body velocity
        vx, vy, vz = np.dot(rot_speed, agent.body.get_velocity()[:3])
        
        # velocity_body_alignment
        refDir = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        velDir = np.array([vx, vy, 0.0], dtype=np.float32)
        
        body_speed = np.linalg.norm(velDir)

        velDir /= np.linalg.norm(velDir) + 0.000001
        body_velocity_alignment = np.dot(refDir, velDir)
        
        self.value = body_velocity_alignment * body_speed * self.misalignment_cost
 