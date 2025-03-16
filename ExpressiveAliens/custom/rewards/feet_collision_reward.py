from custom.rewards.custom_reward import CustomReward
import numpy as np

# specify rewards
class FeetCollisionReward(CustomReward):
    def __init__(self):
        super().__init__()

        self.feet_collision_cost = -1.0	# touches another leg, or other objects, that cost makes robot avoid smashing feet into itself
        self.feet_names = []
        self.feet = []
    
    def init(self):
        self._find_feet()
        super().init()
        
    def _find_feet(self):
        agent = self.env.agent
        
        if len(self.feet_names) > 0: # gather feet based on part names
            self.feet = [ agent.body.body_parts[feet_name] for feet_name in self.feet_names ] 
        else: # gather feet based on parts withouts child joints
            self.feet.clear()
            for body_part in agent.body.ordered_parts:
                if len(body_part.child_joints) == 0:
                    self.feet.append(body_part)
                    self.feet_names.append(body_part.part_name)
    
    def calc_value(self):
        agent = self.env.agent
        ground = self.env.ground

        # calculate feet collision costs (of the feet touch something else than the ground)       
        self.value = 0.0
        ground_body_id = ground.body.id
        for foot in self.feet:
            for contact in foot.get_contacts():
                contact_body_id = contact[2]
                if contact_body_id != ground_body_id:
                    self.value += self.feet_collision_cost
        
        #print("feet collision ", self.value )
    
