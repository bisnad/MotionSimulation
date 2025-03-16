"""
reinforcement learning helper functions
"""

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions.normal import Normal

class RLH:
    
    # static class variables
    EPS = 1e-8 # prevent division by zero
    
    # static helper functions
    
    # create multi layer perceptron
    @staticmethod
    # CAVE: creates one layer less than the tensorflow version
    def create_mlp(hidden_sizes, activation, output_activation=nn.Identity):
        layers = []
        for j in range(len(hidden_sizes)-2):
            layers += [nn.Linear(hidden_sizes[j], hidden_sizes[j+1]), activation()]
        layers += [nn.Linear(hidden_sizes[-2], hidden_sizes[-1]), output_activation()]
        return nn.Sequential(*layers)
    
    @staticmethod
    # TODO: untested
    def gaussian_likelihood(x, mu, log_std):
        pre_sum = -0.5 * (((x-mu)/(np.exp(log_std)+RLH.EPS))**2 + 2*log_std + np.log(2*np.pi))
        return np.sum(pre_sum, axis=1)

