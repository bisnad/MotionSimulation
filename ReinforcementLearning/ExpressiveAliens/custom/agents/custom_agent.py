"""
TODO: this is going to be an agent whose state can be customised similarly to the customised reward functions for the custom environment
But so far, this agent is identical to walker_agent_2 with the exception that there are no boundary objects 
"""

import numpy as np
import gym, gym.spaces, gym.utils
from simulation.agent import Agent

class CustomAgent(Agent):
    def __init__(self, name, body_file, body_index=0):
        super().__init__(name, body_file, body_index)
        
        self.env = None
        self.states = []
        self.state_names = []
        
        self.alive_states = []
        self.alive_state_names = []
        
        self.joint_reset_random_range = np.array([-0.1, 0.1], dtype=np.float32 )
    
    def add_state(self, state, state_name):
        state.agent = self
        self.states.append(state)
        self.state_names.append(state_name)
        
    def add_alive_state(self, state, state_name):
        state.agent = self
        self.alive_states.append(state)
        self.alive_state_names.append(state_name)

    def set_joint_position_reset_random_range(self, random_range):
        self.joint_reset_random_range = random_range
    
    def reset(self):
        super().reset()

        # reset agent states
        for state in self.states:
            state.reset()

        # create observation space
        if self.observation_space == None:
            obs_dim = 0
            for state in self.states:
                obs_dim += state.calc_state().flatten().shape[0]
            high = np.inf * np.ones([obs_dim])
            self.observation_space = gym.spaces.Box(-high, high)
        
        # randomize initial joint orientations
        for joint in self.body.active_joints:
            joint.set_state(joint.get_position() + np.random.uniform(low=self.joint_reset_random_range[0], high=self.joint_reset_random_range[1]), joint.get_velocity())
    
    def get_alive(self):
        
        alive = 0.0
        
        for state in self.alive_states:
            alive += np.sum(state.calc_state())

        return alive
        
    def calc_state(self):

        # this will replace agent state
        agent_state = []
        for state in self.states:
            agent_state.append(state.calc_state())
        agent_state = np.clip(np.concatenate(agent_state), -5, +5) # the fixed clipping values might need changing
        
        """
        print("new states begin")

        for state, state_name in zip(self.states, self.state_names): 
            print("state ", state_name, " ", state.state )
        
        print("new states end")
        """
        
        
        return agent_state
