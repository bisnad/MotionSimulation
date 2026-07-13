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
    
    def get_world_pose_of(self, body_id, link_id):
        if link_id == -1:
            # For the base, getBasePositionAndOrientation is the standard method
            (x, y, z), (a, b, c, d) = self.physics.getBasePositionAndOrientation(body_id)
        else:
            # Get the link state, explicitly asking PyBullet to compute the FK
            link_state = self.physics.getLinkState(body_id, link_id, computeForwardKinematics=1)
            
            # Extract indices 4 (world position) and 5 (world orientation) for the URDF link frame
            (x, y, z) = link_state[4]
            (a, b, c, d) = link_state[5]
        
        return np.array([x, y, z, a, b, c, d])
    
    def get_local_pose_of(self, body_id, link_id):
        # Base link has no parent (its parent is the world environment), 
        # so its local pose is equivalent to its world pose.
        if link_id == -1:
            (x, y, z), (a, b, c, d) = self.physics.getBasePositionAndOrientation(body_id)
            return np.array([x, y, z, a, b, c, d])

        # 1. Get the world pose of the specified link (child)
        # Using indices [4] and [5] for the URDF link frame (preferred for kinematics).
        # If you specifically need the Center of Mass, use indices [0] and [1] instead.
        link_state = self.physics.getLinkState(body_id, link_id, computeForwardKinematics=1)
        child_pos = link_state[4]
        child_orn = link_state[5]

        # 2. Get the parent link index
        # getJointInfo returns a tuple where index 16 is the parentIndex
        joint_info = self.physics.getJointInfo(body_id, link_id)
        parent_id = joint_info[16]

        # 3. Get the world pose of the parent link
        if parent_id == -1:
            parent_pos, parent_orn = self.physics.getBasePositionAndOrientation(body_id)
        else:
            parent_state = self.physics.getLinkState(body_id, parent_id, computeForwardKinematics=1)
            parent_pos = parent_state[4]
            parent_orn = parent_state[5]

        # 4. Compute the relative transform: T_local = T_parent^-1 * T_child
        inv_parent_pos, inv_parent_orn = self.physics.invertTransform(parent_pos, parent_orn)
        local_pos, local_orn = self.physics.multiplyTransforms(
            inv_parent_pos, inv_parent_orn, 
            child_pos, child_orn
        )

        return np.array([
            local_pos[0], local_pos[1], local_pos[2],
            local_orn[0], local_orn[1], local_orn[2], local_orn[3]
        ])

    def get_pose(self):
        return self.get_pose_of(self.body_id, self.part_id)

    def get_world_pose(self):
        return self.get_world_pose_of(self.body_id, self.part_id)

    def get_local_pose(self):
        return self.get_local_pose_of(self.body_id, self.part_id)

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

    def get_local_position(self):
        return self.get_local_pose()[:3]

    def get_world_position(self):
        return self.get_world_pose()[:3]
         
    def get_local_orientation(self):
        return self.get_local_pose()[3:]

    def get_world_orientation(self):
        return self.get_world_pose()[3:]

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