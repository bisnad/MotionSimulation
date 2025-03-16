import pybullet
import numpy as np

class BodyJoint:
    JOINT_REVOLUTE_TYPE = 0
    JOINT_PLANAR_TYPE = 1
    JOINT_PRISMATIC_TYPE = 2
    JOINT_SPHERICAL_TYPE = 3
    JOINT_FIXED_TYPE = 4
    
    def __init__(self, joint_name, body_id, joint_id, physics):
        self.joint_name = joint_name
        self.body_id = body_id
        self.joint_id = joint_id
        self.physics = physics
        self.parent_part = None
        self.child_part = None
        
        # enable joint force tensor
        self.physics.enableJointForceTorqueSensor(self.body_id, self.joint_id, 1)

        joint_info = self.physics.getJointInfo(self.body_id, self.joint_id)
        self.joint_type = joint_info[2]
        self.lower_limit = joint_info[8]
        self.upper_limit = joint_info[9]
        self.joint_has_limits = self.lower_limit < self.upper_limit
        self.joint_max_velocity = joint_info[11]
        self.power_coeff = 1.0
        
        self.default_position, self.default_velocity = self.get_state()
        
        self.torque = 0.0
    
    def set_parent_part(self, parent_part):
        self.parent_part = parent_part

    def set_child_part(self, child_part):
        self.child_part = child_part
        
    def get_parent_part_index(self):
        return self.physics.getJointInfo(self.body_id, self.joint_id)[-1]
    
    def set_state(self, x, vx):
        self.physics.resetJointState(self.body_id, self.joint_id, x, vx)
        
    def get_state(self):
        x, vx,_,_ = self.physics.getJointState(self.body_id, self.joint_id)
        return x, vx
    
    def get_full_state(self):
        x, vx, rf, _ = self.physics.getJointState(self.body_id, self.joint_id)
        return x, vx, rf, self.torque
    
    def get_relative_state(self):
        pos, vel = self.get_state()
        if self.joint_has_limits:
            pos_mid = 0.5 * (self.lower_limit + self.upper_limit)
            
            #print("joint ", self.joint_name, " pos ", pos, " min ", self.lower_limit, " max ", self.upper_limit, " mid ", pos_mid)
            
            pos = 2 * (pos - pos_mid) / (self.upper_limit - self.lower_limit)
            
            #print("pos 2", pos)
        
        if self.joint_max_velocity > 0:
            vel /= self.joint_max_velocity
        elif self.joint_type == BodyJoint.JOINT_REVOLUTE_TYPE:
            vel *= 0.1
        else:
            vel *= 0.5
            
        return (pos, vel)
   
    def get_position(self):
        x, _ = self.get_state()
        return x
   
    def get_orientation(self):
        _,r = self.get_state()
        return r
    
    def get_velocity(self):
        _, vx = self.get_state()
        return vx
    
    def set_position(self, position):
        self.physics.setJointMotorControl2(self.body_id, self.joint_id, pybullet.POSITION_CONTROL, targetPosition=position)
        
    def set_velocity(self, velocity):
        self.physics.setJointMotorControl2(self.body_id, self.joint_id, pybullet.VELOCITY_CONTROL, targetVelocity=velocity)

    def set_torque(self, torque):
        self.torque = torque
        self.physics.setJointMotorControl2(self.body_id, self.joint_id, controlMode=pybullet.TORQUE_CONTROL, force=torque)
        
    def reset_position(self, position):
        self.default_position = position
        self.set_position(self.default_position)

    def reset_velocity(self, velocity):
        self.default_velocity = velocity
        self.set_velocity(self.default_velocity)
        
    def reset(self):
        self.set_state(self.default_position, self.default_velocity)
        self.disable_motor()

    def disable_motor(self):
        self.physics.setJointMotorControl2(self.body_id, self.joint_id, controlMode=pybullet.POSITION_CONTROL, targetPosition=0, targetVelocity=0, positionGain=0.1, velocityGain=0.1, force=0)
