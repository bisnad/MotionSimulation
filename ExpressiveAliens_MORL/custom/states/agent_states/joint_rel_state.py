from custom.states.custom_state import CustomState
import numpy as np

class JointRelState(CustomState):
    def __init__(self):
        super().__init__()
        
        self.joint_names = []
        self.joints = []

    def init(self):
        self.initialized = True
        self._find_joints()
    
    def _find_joints(self):
        if len(self.joint_names) > 0: # gather joints based on joint names
            self.joints = [ self.agent.body.body_joints[joint_name] for joint_name in self.joint_names ] 
        else: # gather gather all active joints
            self.joints = [ joint for joint in self.agent.body.active_joints ]

    def calc_state(self):
        if self.initialized  == False:
            self.init()
            
        self.state = np.array([joint.get_relative_state() for joint in self.joints], dtype=np.float32).flatten()
        
        return self.state