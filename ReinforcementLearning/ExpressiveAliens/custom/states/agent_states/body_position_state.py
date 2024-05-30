from custom.states.custom_state import CustomState
import numpy as np

class BodyPositionState(CustomState):
    def __init__(self):
        super().__init__()
        self.normalise = False

    def calc_state(self):
        if self.initialized  == False:
            self.init()
            
        # position and orientation of body
        body_pose = self.agent.body.get_pose()
        
        # positions of all body parts
        parts_xyz = np.array([body_part.get_pose()[:3] for body_part in self.agent.body.ordered_parts]).flatten()
        
        # calculate body position
        # x: mean x of all body part positions
        # y: mean y of all body part positions
        # z: z of body position (is more informative than mean z of all body part positions)
        body_xyz = (parts_xyz[0::3].mean(), parts_xyz[1::3].mean(), body_pose[2])
        
        if self.normalise == True:
            # normalise body position with respect to env position limits
            env = self.agent.env
            env_pos_limits = env.position_limits
            
            #print("env_pos_limits ", env_pos_limits)
            
            body_xyz = (body_xyz - env_pos_limits[0]) / (env_pos_limits[1] - env_pos_limits[0])
        
        self.state = np.array(body_xyz, dtype=np.float32)
        
        return self.state
    
