from custom.states.custom_state import CustomState
import numpy as np

class GroundContactState(CustomState):
    def __init__(self):
        super().__init__()
        
        self.part_names = []
        self.parts = []

    def init(self):
        self.initialized = True
        self._find_parts()
    
    def _find_parts(self):
        if len(self.part_names) > 0: # gather parts based on part names
            self.parts = [ self.agent.body.body_parts[part_name] for part_name in self.part_names ] 
        else: # gather gather all parts
            self.parts = [ part for part in self.agent.body.ordered_parts ]
            
        self.state = np.array([0.0 for _ in self.parts], dtype=np.float32)

    def calc_state(self):
        if self.initialized  == False:
            self.init()
            
        # check for contact between agent parts and ground
        ground = self.agent.env.ground
        ground_body_id = ground.body.id
        for pI, part in enumerate(self.parts):
            self.state[pI] = 0.0
            #for contact in foot.get_contacts():
            for contact in part.get_contacts_with_body(ground_body_id):
                    self.state[pI] = 1.0
                    break
        
        return self.state
    
