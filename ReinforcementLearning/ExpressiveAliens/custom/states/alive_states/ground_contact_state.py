"""
ground contact alive state
detects if any of the specified body parts are in contact with the ground
For each body part for which this is the case, the alive state is reduced by 1
"""


from custom.states.custom_state import CustomState
from simulation.utils import Utils
import numpy as np

class GroundContactState(CustomState):
    def __init__(self):
        super().__init__()
        
        self.feet_names = []
        self.non_feet_names = []
        self.parts = []
        self.state = np.zeros([1], dtype=np.float32)

    def init(self):
        self.initialized = True
        self.non_feet_names = [ part.part_name for part in self.agent.body.ordered_parts if part.part_name not in self.feet_names ]
        self.parts = Utils.get_agent_parts(self.agent, self.non_feet_names)

    def calc_state(self):
        if self.initialized  == False:
            self.init()
            
        self.state[0] = 0.0
            
        # check for contact between agent parts and ground
        ground = self.agent.env.ground
        ground_body_id = ground.body.id
        for pI, part in enumerate(self.parts):
            for contact in part.get_contacts_with_body(ground_body_id):
                self.state[0] -= 1.0

        
        return self.state
    
