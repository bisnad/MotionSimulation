import numpy as np

class Utils:
    
    # calculate average body position of an agent
    @staticmethod
    def average_body_position(agent):
        body = agent.body
        
        # position and orientation of body
        body_pose = body.get_pose()
    
        # positions of all body parts
        parts_xyz = np.array([body_part.get_pose()[:3] for body_part in body.ordered_parts]).flatten()
                
        # calculate body position
        # x: mean x of all body part positions
        # y: mean y of all body part positions
        # z: z of body position (is more informative than mean z of all body part positions)
        body_pos = (parts_xyz[0::3].mean(), parts_xyz[1::3].mean(), body_pose[2])
        
        return body_pos
    
    @staticmethod
    def get_agent_joints(agent, joint_names):
        
        joints = []
        
        if len(joint_names) > 0: # gather feet based on part names
            joints = [ agent.body.body_joints[joint_name] for joint_name in joint_names ] 
        else: # gather all parts
            joints = agent.body.ordered_joints
            
        return joints

    @staticmethod
    def get_agent_parts(agent, part_names):
        
        parts = []
        
        if len(part_names) > 0: # gather feet based on part names
            parts = [ agent.body.body_parts[part_name] for part_name in part_names ] 
        else: # gather all parts
            parts = agent.body.ordered_parts
            
        return parts
    
    @staticmethod
    def calc_normalised_masses(parts):
        normalised_masses = [ part.get_mass() for part in parts ]
        normalised_masses = np.array(normalised_masses, dtype=np.float32)
        normalised_masses /= np.sum(normalised_masses ) 
        
        return normalised_masses