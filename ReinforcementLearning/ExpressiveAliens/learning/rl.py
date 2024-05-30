"""
reinforcement learning base class
"""

import numpy as np
import pickle

class RL:
    def __init__(self, observation_limits, action_limits, replay_size):
        self.observation_limits = observation_limits
        self.action_limits = action_limits
        self.replay_size = replay_size
        
        self.replay_buffer = None
        self.gamma=0.99
        
        # training settings
        self.batch_size=100
        self.replay_count=50
    
    def set_batch_size(self, batch_size):
        self.batch_size=100
    
    # number of times the replay buffer is sampled to obtain training data
    def set_replay_count(self, replay_count):
        self.replay_count = replay_count
    
    # gamma (float): Discount factor. (Always between 0 and 1.)
    def set_gamma(self, gamma):
        self.gamma = gamma
        
    def load_models(self, file_path, epoch = 0):
        pass
        
    def save_models(self, file_path, epoch = 0):
        pass

    def load_weights(self, file_path, epoch = 0):
        pass
        
    def save_weights(self, file_path, epoch = 0):
        pass
        
    def load_replay_buffer(self, file_path, epoch = 0):
        full_file_name = "{}/replay_epoch_{}.p".format(file_path, epoch)
        self.replay_buffer = pickle.load(open(full_file_name, "rb"))
        
    def save_replay_buffer(self, file_path, epoch = 0):
        if self.replay_buffer != None:
            full_file_name = "{}/replay_epoch_{}.p".format(file_path, epoch)
            pickle.dump(self.replay_buffer, open(full_file_name, "wb"))