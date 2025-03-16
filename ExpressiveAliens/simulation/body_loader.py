import pybullet
import os
from simulation.body_part import BodyPart
from simulation.body_joint import BodyJoint
from simulation.body import Body

class BodyLoader:
    
    @staticmethod
    def load(file_path, physics): 
        if file_path.endswith(".urdf"):
            return BodyLoader.loadURDF(file_path, physics)
        elif file_path.endswith(".mjcv"):
            return BodyLoader.loadMJCF(file_path, physics)
        elif file_path.endswith(".sdf"):
            return BodyLoader.loadSDF(file_path, physics)
        else:
            raise Exception("file format not recognized")
    
    @staticmethod
    def loadURDF(file_path, physics):  
        return BodyLoader.create_bodies(physics.loadURDF(file_path,
				flags=physics.URDF_USE_SELF_COLLISION),
                               physics=physics)

    # Untested
    @staticmethod
    def loadMJCF(file_path, physics):       
        return BodyLoader.create_bodies(physics.loadMJCF(file_path,
				flags=physics.URDF_USE_SELF_COLLISION),
                               physics=physics)
    
    # Untested
    @staticmethod
    def loadSDF(file_path, physics):       
        return BodyLoader.create_bodies(physics.loadSDF(file_path,
				flags=physics.URDF_USE_SELF_COLLISION),
                               physics=physics)

    # unclear if any of the supported file formats can contain multiple bodies (i.e. multiple root links)
    # but just in case, this code is supposed to handle this possibility
    # but unless I find an example of a multi body file, this code is untested
    @staticmethod
    def create_bodies(body_ids, physics):
        
       	if isinstance(body_ids, list) == False:
               body_ids = [body_ids] 

        bodies = []
        
        for body_id in body_ids:
            bodies.append(BodyLoader.create_body(body_id, physics))
            
        return bodies

    @staticmethod
    def create_body(body_id, physics):
        parts = {}
        ordered_parts = []
        joints = {}
        ordered_joints= []
        root_part = None

        # create root part
        part_name, body_name = physics.getBodyInfo(body_id)
        body_name = body_name.decode("utf8")
        part_name = part_name.decode("utf8")
        parts[part_name] = BodyPart(part_name, body_id, -1, physics)
        root_part = parts[part_name]
        ordered_parts.append(root_part)

        # create non-root parts and joints
        for joint_id in range(physics.getNumJoints(body_id)): # bodies with joints
            physics.setJointMotorControl2(body_id, joint_id, pybullet.POSITION_CONTROL, positionGain=0.1, velocityGain=0.1, force=0)
            jointInfo = physics.getJointInfo(body_id, joint_id)
            joint_name=jointInfo[1].decode("utf8")
            part_name=jointInfo[12].decode("utf8")
            
            #print("pn ", part_name, " b_id ", body_id , " ji ", joint_id)
                            
            parts[part_name] = BodyPart(part_name, body_id, joint_id, physics)
            ordered_parts.append(parts[part_name])
            
            if joint_name[:6] == "ignore":
                BodyJoint(joint_name, body_id, joint_id, physics).disable_motor()
                ordered_joints.append(joints[joint_name])
            
            if joint_name[:8] != "jointfix":
                joints[joint_name] = BodyJoint(joint_name, body_id, joint_id, physics)
                ordered_joints.append(joints[joint_name])
                joint_max_force = jointInfo[10]
                joints[joint_name].power_coeff = joint_max_force

                #print("jn ", joint_name, " b_id ", body_id, " ji ", joint_id, " power_coeff ", joint_max_force)

        # add joints to body parts and body parts to joints
        for joint in ordered_joints:
            jointInfo = physics.getJointInfo(joint.body_id, joint.joint_id)
            joint_child_part_name = jointInfo[12].decode("utf8")
            joint_parent_part_index = jointInfo[16]
            
            if joint_parent_part_index > -1:
                jointInfo = physics.getJointInfo(body_id, joint_parent_part_index)
                joint_parent_part_name=jointInfo[12].decode("utf8")
            else:
                joint_parent_part_name = root_part.part_name
            
            #print("joint ", joint.joint_name, " child part ", joint_child_part_name, " parent part", joint_parent_part_name)

            joint_child_part = parts[joint_child_part_name]
            joint_parent_part = parts[joint_parent_part_name]
            
            joint.set_child_part(joint_child_part)
            joint.set_parent_part(joint_parent_part)
            
            joint_child_part.set_parent_joint(joint)
            joint_parent_part.add_child_joint(joint)

        """
        # debug
        for joint_name, joint in joints.items():
            joint_parent_part_name = joint.parent_part.part_name
            joint_child_part_name = joint.child_part.part_name
            
            print("joint ", joint_name, " parent_part ", joint_parent_part_name, " child_part ", joint_child_part_name)

        for part_name, part in parts.items():
            print("part ", part_name)
            if part.parent_joint:
                print("parent_joint ", part.parent_joint.joint_name)
            else:
                print("parent_joint ", "None")
            for child_joint in part.child_joints:
                print("child joint ", child_joint.joint_name)
        """

        return Body(body_name, root_part, parts, ordered_parts, joints, ordered_joints, physics)