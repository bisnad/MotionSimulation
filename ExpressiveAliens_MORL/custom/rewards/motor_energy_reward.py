from custom.rewards.custom_reward import CustomReward
import numpy as np

# specify rewards
class MotorEnergyReward(CustomReward):
    def __init__(self):
        super().__init__()

        self.energy_cost = -2.0	 # cost for using motors -- this parameter should be carefully tuned against reward for making progress, other values less improtant
        self.stall_cost = -0.1  # cost for running electric current through a motor even at zero rotational speed, small
        self.limit_cost = -0.1 # discourage stuck joints
 
    def calc_value(self):
        agent = self.env.agent
        agent_action = agent.action
        
        # get relative state (pos & velocity) for all active joints
        # even elements [0::2] position, scaled to -1..+1 between limits
        # odd elements  [1::2] angular speed, scaled to show -1..+1
        joint_rel_states= np.array([joint.get_relative_state() for joint in agent.body.active_joints], dtype=np.float32).flatten()
        
        # joint speeds
        joint_speeds = joint_rel_states[1::2]
        
        # joints close to limit positions
        joints_at_limit = np.count_nonzero(np.abs(joint_rel_states[0::2]) > 0.99)

        cost1  = self.energy_cost * float(np.abs(agent_action*joint_speeds).mean())  # let's assume we have DC motor with controller, and reverse current braking
        cost2  = self.stall_cost * float(np.square(agent_action).mean())
        cost3 = float(self.limit_cost * joints_at_limit)
        
        """
        print("energy cost ", cost1)
        print("stall cost ", cost2)
        print("limit cost ", cost3)
        """
        
        self.value = cost1 + cost2 + cost3

 
    """
    def get_reward(self):
        super().get_reward()

        agent = self.env.agent
        agent_action = agent.action
        
        # get relative state (pos & velocity) for all active joints
        # even elements [0::2] position, scaled to -1..+1 between limits
        # odd elements  [1::2] angular speed, scaled to show -1..+1
        joint_rel_states= np.array([joint.get_relative_state() for joint in agent.body.active_joints], dtype=np.float32).flatten()
        
        # joint speeds
        joint_speeds = joint_rel_states[1::2]
        
        # joints close to limit positions
        joints_at_limit = np.count_nonzero(np.abs(joint_rel_states[0::2]) > 0.99)

        cost1  = self.energy_cost * float(np.abs(agent_action*joint_speeds).mean())  # let's assume we have DC motor with controller, and reverse current braking
        cost2  = self.stall_cost * float(np.square(agent_action).mean())
        cost3 = float(self.limit_cost * joints_at_limit)
        
        #print("energy cost ", cost1)
        #print("stall cost ", cost2)
        #print("limit cost ", cost3)
        
        self.reward = cost1 + cost2 + cost3
        
        
        self.reward *= self.reward_scale
        
        return self.reward
    """
