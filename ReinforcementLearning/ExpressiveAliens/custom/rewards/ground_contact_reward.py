from custom.rewards.custom_reward import CustomReward
from simulation.utils import Utils
import numpy as np

# specify rewards
class GroundContactReward(CustomReward):
    def __init__(self):
        super().__init__()
        
        self.feet_names = []
        self.non_feet_names = []
        self.parts = []
        self.state = np.zeros([1], dtype=np.float32)
        
        self.ground_collision_cost = -100.0	# touches another leg, or other objects, that cost makes robot avoid smashing feet into itself
        
    def init(self):
        self.initialized = True
        agent = self.env.agent
        
        self.non_feet_names = [ part.part_name for part in agent.body.ordered_parts if part.part_name not in self.feet_names ]
        
        if len(self.non_feet_names) > 0:
            self.parts = Utils.get_agent_parts(agent, self.non_feet_names)
        
        #print("self.feet_names ", self.feet_names)
        #print("self.non_feet_names ", self.non_feet_names)
        
    def calc_value(self):
        agent = self.env.agent
        ground = self.env.ground 
        self.value = 0.0
        
        ground_body_id = ground.body.id
        for pI, part in enumerate(self.parts):
            for contact in part.get_contacts_with_body(ground_body_id):

                self.value += self.ground_collision_cost
