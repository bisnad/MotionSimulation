from custom.states.custom_state import CustomState
import numpy as np

class BodyTargetState(CustomState):
    def __init__(self):
        super().__init__()

    def calc_state(self):
        if self.initialized  == False:
            self.init()

        agent_pos = self.agent.body.get_position()
        agent_rot = self.agent.body.get_orientation()
        target_pos = self.agent.env.target.body.get_position()
        
        # agent body orientation (as euler angles)
        body_rpy = self.agent.physics.getEulerFromQuaternion(agent_rot)
        r, p, yaw = body_rpy
        
        walk_target_theta = np.arctan2(target_pos[1] - agent_pos[1],  target_pos[0] - agent_pos[0])
        walk_target_dist = np.linalg.norm([target_pos[1] - agent_pos[1], target_pos[0] - agent_pos[0]])
        angle_to_target = walk_target_theta - yaw
        
        self.state = np.array([np.sin(angle_to_target), np.cos(angle_to_target)], dtype=np.float32)
        
        #print("BodyTargetState state ", self.state)
        
        return self.state
    
