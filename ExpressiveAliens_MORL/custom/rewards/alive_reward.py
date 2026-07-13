from custom.rewards.custom_reward import CustomReward

# specify rewards
class AliveReward(CustomReward):
    def __init__(self):
        super().__init__()
        
        self.alive_value = 1.0 # reward for each step where the agent is alife 
        self.not_alive_value = -100.0 # cost or agent no longer being alive (i.e. hitting the ground)
        self.reward_scale = 1.0
        
    def calc_value(self):
        agent = self.env.agent
        ground = self.env.ground 
        
        agent_alive = agent.get_alive()
        
        #print("AliveReward alive ", agent_alive)

        if agent_alive < 0:
            self.episode_done = True
            self.value = self.not_alive_value
        else:
            self.episode_done = False
            self.value = self.alive_value
