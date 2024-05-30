"""
base class for calculating reward
parameters:
    env: a reference to the training environment
    initialised: flag  indicating if some initial setup is required when the reward is calculated for the first time
    value: a scalar value directly derived from the agent and environment state
    target_value: the value that should be achieved by the agent, if this is None, then the value is directly used to calculate the reward, if not None, then the different between the value and target value is used to calculate the reward
    min_value: minimum possible value, if not None used for normalsing the value 
    max_value: maximum possible value, if not None used for normalsing the value
    value_reward_scale: scaling factor when converting teh value into a reward
    reward: the reward itself
    reward_scale: reward scaling function applied before returning the reward
    episode_done: flag indicating if episode should be stopped

functions:
    init: initialisation before a reward is calculated for the first time
    reset: called at the beginning of a new episode
    calc_reward: calculate and return reward

"""

class CustomReward:
    def __init__(self):
        self.env = None
        self.initialized = False
        
        self.orig_value = 0.0
        self.value = 0.0
        self.min_value = None
        self.max_value = None
        self.target_value = None 

        self.value_reward_scale = 1.0 
        self.reward = 0.0 
        self.reward_scale = 1.0
        
        self.episode_done = False

    def init(self):
        self.initialized = True
        
    def reset(self):
        pass
    
    def calc_value(self):
        pass
    
    def calc_reward(self):
        
        self.orig_value = self.value
        
        # normalise value if necessay
        if self.min_value != None and self.max_value != None:
            self.value = min(max(self.value, self.min_value), self.max_value)
            self.value = (self.value - self.min_value) / (self.max_value - self.min_value)
            
            #print("orig_value ", self.orig_value, " value ", self.value)
            
        # calculate difference to target value if necessary
        if self.target_value != None:
            self.value = 1.0 - abs(self.target_value - self.value)
                
        self.reward = self.value * self.value_reward_scale 
        self.reward *= self.reward_scale
        
    def get_reward(self):
        if self.initialized == False:
            self.init()
            
        #calculate value
        self.calc_value()
        
        # process value
        self.calc_reward()

        return self.reward