from custom.states.custom_state import CustomState
import numpy as np

class BodyInitialHeightDiffState(CustomState):
    def __init__(self):
        super().__init__()
        self.initial_height = None

    def init(self):
        self.initialized = True
    
    def reset(self):
        self.initial_height = None

    def calc_state(self):
        if self.initialized  == False:
            self.init()
        
        body_pose = self.agent.body.get_pose()
        body_height = body_pose[2]
        
        if self.initial_height  == None:
            self.initial_height= body_height
        
        self.state = np.array([body_height - self.initial_height], dtype=np.float32)
        
        return self.state
    
