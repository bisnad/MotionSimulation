"""
Camera Class
"""

import numpy as np
import pybullet

class Camera:
    
    def __init__(self, physics):
        self.physics = physics
        self.target_pos = [0, 0, 0]
        self.distance = 5
        self.yaw = 10
        self.pitch = -20
        self.render_width = 1280
        self.render_height = 720
        physics.resetDebugVisualizerCamera(self.distance, self.yaw, self.pitch, self.target_pos)
        
    def look_at(self, target_pos, distance=None, yaw=None, pitch=None):
        
        self.target_pos = target_pos
        
        if distance != None:
            self.distance = distance    
        if yaw != None:
            self.yaw = yaw 
        if pitch != None:
            self.pitch = pitch
            
        self.physics.resetDebugVisualizerCamera(self.distance, self.yaw, self.pitch, self.target_pos)
        
    def render(self):
        view_matrix = self.physics.computeViewMatrixFromYawPitchRoll(
			cameraTargetPosition=self.target_pos,
			distance=self.distance,
			yaw=self.yaw,
			pitch=self.pitch,
			roll=0,
			upAxisIndex=2)
        
        proj_matrix = self.physics.computeProjectionMatrixFOV(
			fov=60, aspect=float(self.render_width)/self.render_height,
			nearVal=0.1, farVal=100.0)
        
        (_, _, px, _, _) = self.physics.getCameraImage(
            width=self.render_width, height=self.render_height, 
            viewMatrix=view_matrix,
			projectionMatrix=proj_matrix,
			renderer=pybullet.ER_BULLET_HARDWARE_OPENGL
			)
        
        rgb_array = np.array(px)
        rgb_array = rgb_array[:, :, :3]
        return rgb_array