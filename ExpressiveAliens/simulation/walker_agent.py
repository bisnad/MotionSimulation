"""
A classical walker agent that is supposed to reach a target.
"""

import numpy as np
import gym, gym.spaces, gym.utils
from simulation.agent import Agent

class WalkerAgent(Agent):
    def __init__(self, name, body_file, body_index=0):
        super(WalkerAgent, self).__init__(name, body_file, body_index)
        
        self.feet_names = []
        self.feet = []
        self.feet_contact = None
        
        self.initial_height = None
        self.joint_reset_random_range = np.array([-0.1, 0.1], dtype=np.float32 )
    
    def set_feet_names(self, feet_names):
        self.feet_names = feet_names
        
        self.feet = []
        self.observation_space = None
    
    def set_joint_position_reset_random_range(self, random_range):
        self.joint_reset_random_range = random_range
    
    def _find_feet(self):
        if len(self.feet_names) > 0: # gather feet based on part names
            self.feet = [ self.body.body_parts[feet_name] for feet_name in self.feet_names ] 
        else: # gather feet based on parts withouts child joints
            self.feet.clear()
            for body_part in self.body.ordered_parts:
                if len(body_part.child_joints) == 0:
                    self.feet.append(body_part)
                    self.feet_names.append(body_part.part_name)
    
    def reset(self):
        super(WalkerAgent, self).reset()

        # set feet if not yet done so
        if len(self.feet) == 0:
            self._find_feet()
            
        if self.observation_space == None:
            # obs_dim: hight, body angle to target, body velocity, body orientation, joint rel states, feet ground contact
            obs_dim = 1 + 2 + 3 + 2 + 2 * len(self.body.active_joints) + len(self.feet)
            high = np.inf * np.ones([obs_dim])
            self.observation_space = gym.spaces.Box(-high, high)
        
        # randomize joint orientations
        for joint in self.body.active_joints:
            joint.set_state(joint.get_position() + np.random.uniform(low=self.joint_reset_random_range[0], high=self.joint_reset_random_range[1]), joint.get_velocity())

        # reset feet contacts
        self.feet_contact = np.array([0.0 for _ in self.feet], dtype=np.float32)
        
        # reset body start height
        self.initial_height = None
    
    def get_alive(self, *args):
        assert(len(args) == 1)
        
        ground = args[0]
        ground_body_id = ground.body.id
        
        # dead if any body part except the feet touches the ground
        for body_part in self.body.ordered_parts:
            if body_part in self.feet:
                continue
            else:
                contacts = body_part.get_contacts()
                for contact in contacts:
                    contact_body_id = contact[2]
                    if contact_body_id == ground_body_id:
                        self.alive = -1.0
                        return self.alive
            
        self.alive = 1.0
        return self.alive 

        
    def calc_state(self, *args):
        
        if len(args) < 2:
            return None
        
        ground = args[0]
        target = args[1]
        
        if target:
            walk_target = target.body.get_position()
        else:
            walk_target = [0.0, 0.0, 0.0]
        
        # get relative state (pos & velocity) for all active joints
        # even elements [0::2] position, scaled to -1..+1 between limits
        # odd elements  [1::2] angular speed, scaled to show -1..+1
        joint_rel_states= np.array([joint.get_relative_state() for joint in self.body.active_joints], dtype=np.float32).flatten()
        
        # joint speeds
        self.joint_speeds = joint_rel_states[1::2]
        
        # joints close to limit positions
        self.joints_at_limit = np.count_nonzero(np.abs(joint_rel_states[0::2]) > 0.99)

        # position and orientation of body
        body_pose = self.body.get_pose()
        
        # positions of all body parts
        parts_xyz = np.array([body_part.get_pose()[:3] for body_part in self.body.ordered_parts]).flatten()
        
        # calculate body position
        # x: mean x of all body part positions
        # y: mean y of all body part positions
        # z: z of body position (is more informative than mean z of all body part positions)
        self.body_xyz = (
            parts_xyz[0::3].mean(), parts_xyz[1::3].mean(), body_pose[2])
        
        # body orientation (as euler angles)
        self.body_rpy = self.physics.getEulerFromQuaternion(body_pose[3:])

        # body height
        body_height = self.body_xyz[2]
        if self.initial_height is None:
            self.initial_height = body_height
            
        # calc angle and distance to walk target
        r, p, yaw = self.body_rpy
        self.walk_target_theta = np.arctan2(walk_target[1] - self.body_xyz[1],
                                            walk_target[0] - self.body_xyz[0])
        self.walk_target_dist = np.linalg.norm(
            [walk_target[1] - self.body_xyz[1], walk_target[0] - self.body_xyz[0]])
        angle_to_target = self.walk_target_theta - yaw
        
        # rotation speed matrix
        rot_speed = np.array(
            [[np.cos(-yaw), -np.sin(-yaw), 0],
             [np.sin(-yaw), np.cos(-yaw), 0],
             [		0,			 0, 1]])
        
        # rotate speed back to body point of view
        vx, vy, vz = np.dot(rot_speed, self.body.get_velocity()[:3])
        
        # check for contact between agent feet and ground
        ground_body_id = ground.body.id
        for fI, foot in enumerate(self.feet):
            
            self.feet_contact[fI] = 0.0
            
            for contact in foot.get_contacts():
                contact_body_id = contact[2]
                if contact_body_id == ground_body_id:
                    self.feet_contact[fI] = 1.0
                    break
        
        # gather the following state information
        # body height difference between reset and now
        # body orientation difference to target
        # body rotation velocity with respect to target
        # body roll and pitch orientation
        more = np.array([body_height - self.initial_height,
                         np.sin(angle_to_target), np.cos(angle_to_target),
                         0.3 * vx, 0.3 * vy, 0.3 * vz,  # 0.3 is just scaling typical speed into -1..+1, no physical sense here
                         r, p], dtype=np.float32)
        
        # add additional state information
        # relative state (pos & velocity) of all active joints
        # the list of feet contacts, this one will be updated by the environment 
        self.state = np.clip(np.concatenate([more] + [joint_rel_states] + [self.feet_contact]), -5, +5)
        
        return self.state
        