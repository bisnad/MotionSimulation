import pybullet
import gym, gym.spaces, gym.utils
import numpy as np
from simulation.body_joint import BodyJoint

class Body:
    def __init__(self, name, root_part, body_parts, ordered_parts, body_joints, ordered_joints, physics):
        self.name = name
        self.id = root_part.body_id
        self.root_part = root_part
        self.body_parts = body_parts
        self.ordered_parts = ordered_parts
        self.body_joints = body_joints
        self.ordered_joints = ordered_joints
        self.active_joints = [ joint for joint in ordered_joints if (joint.power_coeff > 0.0 and joint.joint_type != BodyJoint.JOINT_FIXED_TYPE) ]
        self.physics = physics
        
        self.default_position = self.get_position()
        self.default_orientation = self.get_orientation()
        self.default_linear_velocity = self.get_velocity()[:3]
        self.default_angular_velocity = self.get_velocity()[3:]

    # deactivate self collision between body parts that are connected by a joint
    def deactivate_joint_collisions(self):
        for joint in self.ordered_joints:
            parent_part_id = joint.parent_part.part_id
            child_part_id = joint.child_part.part_id
            self.physics.setCollisionFilterPair(self.id, self.id, parent_part_id, child_part_id, 0)
            
    # deactivate self collision between any body parts
    def deactivate_self_collisions(self):
        for part1 in self.ordered_parts:
            part1_id = part1.part_id
            for part2 in self.ordered_parts:
                part2_id = part2.part_id
                if part1_id != part2_id:
                    self.physics.setCollisionFilterPair(self.id, self.id, part1_id, part2_id, 0)

    def get_pose(self):
        return self.root_part.get_pose()
    
    def get_velocity(self):
        return self.root_part.get_velocity()
    
    def get_position(self):
        return self.root_part.get_position()
    
    def get_orientation(self):
        return self.root_part.get_orientation()
    
    def set_position(self, position):
        self.physics.resetBasePositionAndOrientation(self.id, position, self.get_orientation())
        
    def set_orientation(self, orientation):
        self.physics.resetBasePositionAndOrientation(self.id, self.get_position(), orientation)
    
    def set_pose(self, position, orientation):
        self.physics.resetBasePositionAndOrientation(self.id, position, orientation)
    
    def set_velocity(self, linearVelocity=[0,0,0], angularVelocity =[0,0,0]):
        self.physics.resetBaseVelocity(self.id, linearVelocity, angularVelocity)    
    
    def reset_position(self, position):
        self.default_position = position
        self.set_position(self.default_position)
        
    def reset_orientation(self, orientation):
        self.default_orientation = orientation
        self.set_orientation(orientation)
    
    def reset_velocity(self, linearVelocity=[0,0,0], angularVelocity =[0,0,0]):
        self.default_linear_velocity = linearVelocity
        self.default_angular_velocity = angularVelocity
        self.set_velocity(linearVelocity, angularVelocity)
    
    def reset(self):
        self.set_pose(self.default_position, self.default_orientation)
        self.set_velocity(self.default_linear_velocity, self.default_angular_velocity)
        
        for joint in self.ordered_joints:
            joint.reset()
        
    def get_contacts(self):
        all_contact_points = []
        
        for part in self.ordered_parts:
            part_contact_points = part.get_contacts()
            all_contact_points.append(part_contact_points)

        return all_contact_points
    
    def get_contacts_with_body(self, body):
        return self.physics.getContactPoints(self.id, body.id)
    
    def get_contacts_with_body_part(self, part):
        return self.physics.getContactPoints(self.id, part.body_id, -1, part.part_id)
    
    def get_aabb(self):
        # get aabb encompassing all body parts 
        
        all_aabb = []
        
        for part in self.ordered_parts:
            part_aabb = part.get_aabb(self.id)
            all_aabb.append(part_aabb)
            
        all_aabb = np.stack(all_aabb, axis=0)
        all_aabb_min = all_aabb[:, :3]
        all_aabb_max = all_aabb[:, 3:]

        all_aabb_min = all_aabb_min.min(axis=0)
        all_aabb_max = all_aabb_max.max(axis=0)

        all_aabb = np.concatenate((all_aabb_min, all_aabb_max))
        
        return all_aabb