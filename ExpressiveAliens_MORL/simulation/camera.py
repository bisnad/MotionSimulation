"""
Camera Class
"""

import numpy as np
import pybullet
#import traceback

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

        # Get the current camera state from the debug visualizer
        try:
            cam_info = self.physics.getDebugVisualizerCamera()
            # cam_info index 8 is yaw, 9 is pitch, 10 is distance
            cam_yaw = cam_info[8]
            cam_pitch = cam_info[9]
            cam_dist = cam_info[10]
        except Exception:
            # Fallback if in a mode where getDebugVisualizerCamera fails
            cam_yaw = self.yaw
            cam_pitch = self.pitch
            cam_dist = self.distance
        
        # Override with explicit parameters if provided
        if distance != None:
            self.distance = distance  
        else:
            self.distance = cam_dist
        if yaw != None:
            self.yaw = yaw 
        else:
            self.yaw = cam_yaw 
        if pitch != None:
            self.pitch = pitch
        else:
            self.pitch = cam_pitch

        self.physics.resetDebugVisualizerCamera(
            cameraDistance=self.distance, 
            cameraYaw=self.yaw, 
            cameraPitch=self.pitch, 
            cameraTargetPosition=self.target_pos
        )
        

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