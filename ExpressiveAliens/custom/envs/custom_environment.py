import numpy as np
from simulation.environment import Environment

class CustomEnvironment(Environment):
    def __init__(self):
        super(CustomEnvironment, self).__init__(display=False)
        
        self.ground = None 
        self.target = None # in case the agent is supposed to walk towards a target object

        self.rewards = []
        self.reward_names = []
        self.position_limits = np.array([[-10.0, -10.0, 0.0], [10.0, 10.0, 2.0]], dtype=np.float32)

    def add_agent(self, agent):
        agent.env = self
        super().add_agent(agent)
        
    def add_ground(self, ground):
        self.ground = ground
        self.add_thing(ground)
    
    def add_target(self, target):
        self.target = target
        self.add_thing(target)
        
    def add_reward(self, reward, reward_name=""):
        reward.env = self
        self.rewards.append(reward)
        self.reward_names.append(reward_name)
    
    def reset(self):
        _ = super().reset()
        
        for reward in self.rewards:
            reward.reset()

        agent_state = self.agent.calc_state()
        return agent_state
    
    def step(self, action):
        self.agent.apply_action(action)
        
        if self.sim_has_drag == True:
            self.apply_drag()
        
        self.physics.stepSimulation()
        
        agent_state = self.agent.calc_state()
        
        # check if agent is still alive
        agent_alive = self.agent.get_alive()
        
        if agent_alive < 0:
            #print("step alive ", agent_alive)
            self.episode_done = True
        
        # check if agent_state is valid
        if not np.isfinite(agent_state).all():
            print("~INF~", agent_state)
            self.episode_done = True
        
        step_reward = 0.0
        for reward in self.rewards:
            step_reward += reward.get_reward()

            if reward.episode_done == True:
                self.episode_done = True
                    
        # debug
        """
        for reward, reward_name in zip(self.rewards, self.reward_names):
            print("reward ", reward_name, " value ", reward.value, " reward ", reward.reward)
        """
        self.episode_reward += step_reward
        
        #print("total: ", step_reward)
        
        return agent_state, step_reward, bool(self.episode_done), {}
    
    def camera_adjust(self):
        agent_position = self.agent.body.get_position()
        self.camera.look_at(agent_position)
