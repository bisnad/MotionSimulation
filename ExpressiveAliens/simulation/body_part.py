import pybullet
import numpy as np

class BodyPart:
    def __init__(self, part_name, body_id, part_id, physics):
        self.part_name = part_name
        self.body_id = body_id
        self.part_id = part_id
        self.physics = physics
        self.parent_joint = None
        self.child_joints = []
        
    def set_parent_joint(self, parent_joint):
        self.parent_joint = parent_joint
    
    def add_child_joint(self, child_joint):
        self.child_joints.append(child_joint)
        
    def get_mass_of(self, body_id, link_id):
        mass, _, _, _, _, _, _, _, _, _, _, _ = self.physics.getDynamicsInfo(body_id, link_id)
        return mass
        
    def get_mass(self):
        return self.get_mass_of(self.body_id, self.part_id)
    
    def get_pose_of(self, body_id, link_id):
        if link_id == -1:
            (x, y, z), (a, b, c, d) = self.physics.getBasePositionAndOrientation(body_id)
        else:
            (x, y, z), (a, b, c, d), _, _, _, _ = self.physics.getLinkState(body_id, link_id)
        return np.array([x, y, z, a, b, c, d])
    
    def get_pose(self):
        return self.get_pose_of(self.body_id, self.part_id)
    
    # get linear and angular velocity
    def get_velocity_of(self, body_id, link_id):
        if link_id == -1:
            (vx, vy, vz), (wx, wy, wz) = self.physics.getBaseVelocity(body_id)
        else:
            _, _, _, _, _, _, (vx, vy, vz), (wx, wy, wz) = self.physics.getLinkState(body_id, link_id, computeLinkVelocity=1)
        return np.array([vx, vy, vz, wx, wy, wz])
    
    def get_velocity(self):
        return self.get_velocity_of(self.body_id, self.part_id)
    
    def get_body_velocity(self):
        (vx, vy, vz), (wx, wy, wz) = self.physics.getBaseVelocity(self.body_id)
        return np.array([vx, vy, vz, wx, wy, wz])
    
    def get_position(self):
        return self.get_pose()[:3]
    
    def get_orientation(self):
        return self.get_pose()[3:]
         
    def get_contacts(self):
        return self.physics.getContactPoints(bodyA=self.body_id, linkIndexA=self.part_id)
    
    def get_contacts_with_body(self, contact_body_id):
        return self.physics.getContactPoints(bodyA=self.body_id, bodyB=contact_body_id, linkIndexA=self.part_id)
    
    def get_contacts_with_body_part(self, contact_body_id, contact_part_id):
        return self.physics.getContactPoints(bodyA=self.body_id, bodyB=contact_body_id, linkIndexA=self.part_id, linkIndexB=contact_part_id)
    
    def get_aabb_of(self, body_id, link_id):
        if link_id == -1:
            ((minx, miny, minz), (maxx, maxy, maxz)) = self.physics.getAABB(body_id)
        else:
            ((minx, miny, minz), (maxx, maxy, maxz)) = self.physics.getAABB(body_id, link_id)
        return np.array([minx, miny, minz, maxx, maxy, maxz])
    
    def get_aabb(self, body_id):
        return self.get_aabb_of(self.body_id, self.part_id)