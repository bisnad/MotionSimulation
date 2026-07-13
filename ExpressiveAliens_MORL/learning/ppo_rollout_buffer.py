"""
Educational Rollout Buffer for Proximal Policy Optimization (PPO).

Unlike off-policy algorithms (like SAC or DQN) that use a Replay Buffer to store 
and randomly sample past experiences forever, PPO is an "on-policy" algorithm. 
This means it only learns from data collected by its *current* policy. 

Therefore, this Rollout Buffer fills up with a batch of experiences, uses them 
to update the neural networks once, and then completely empties itself to start fresh.
"""

import numpy as np
import scipy.signal
import torch

class PPO_RolloutBuffer:
    
    @staticmethod
    def combined_shape(length, shape=None):
        """Helper to create correct array shapes for our buffers."""
        if shape is None:
            return (length,)
        return (length, shape) if np.isscalar(shape) else (length, *shape)
    
    @staticmethod
    def discount_cumsum(x, discount):
        """
        Calculates the discounted cumulative sum of a sequence.
        
        If x is an array of rewards [x0, x1, x2] and discount is "d", this returns:
        [x0 + d*x1 + d^2*x2, 
         x1 + d*x2, 
         x2]
         
        This is a highly efficient way to calculate future rewards using 
        a signal processing function from SciPy, rather than a slow 'for' loop.
        """
        return scipy.signal.lfilter([1], [1, float(-discount)], x[::-1], axis=0)[::-1]

    def __init__(self, obs_dim, act_dim, size, gamma=0.99, lam=0.95):
        """
        Initializes arrays (buffers) to store one batch of experiences.
        
        Args:
            obs_dim: Size of the observation vector.
            act_dim: Size of the action vector.
            size: Maximum number of steps to store in the buffer (batch size).
            gamma: Discount factor for future rewards (usually 0.99).
            lam: Lambda parameter for GAE to balance bias/variance (usually 0.95).
        """
        # --- Standard Environment Buffers ---
        self.obs_buf = np.zeros(PPO_RolloutBuffer.combined_shape(size, obs_dim), dtype=np.float32)
        self.act_buf = np.zeros(PPO_RolloutBuffer.combined_shape(size, act_dim), dtype=np.float32)
        self.rew_buf = np.zeros(size, dtype=np.float32)
        
        # --- PPO-Specific Buffers ---
        # Advantage estimates: How much better or worse an action was than average.
        self.adv_buf = np.zeros(size, dtype=np.float32)
        
        # Returns (Rewards-to-go): The target values we train the Critic network to predict.
        self.ret_buf = np.zeros(size, dtype=np.float32)
        
        # Values: The Critic network's predicted value for each state at the time it was collected.
        self.val_buf = np.zeros(size, dtype=np.float32)
        
        # Log Probabilities: The chance of taking the action (used for the probability ratio in PPO).
        self.logp_buf = np.zeros(size, dtype=np.float32)
        
        # --- Hyperparameters & Pointers ---
        self.gamma = gamma 
        self.lam = lam     
        
        # ptr: Where to insert the next experience.
        # path_start_idx: Where the current episode started (used when an episode ends).
        # max_size: The total capacity of the buffer.
        self.ptr, self.path_start_idx, self.max_size = 0, 0, size

    def store(self, obs, act, rew, val, logp):
        """
        Save a single step of interaction into the buffer arrays.
        """
        assert self.ptr < self.max_size # Crash if we try to store more than capacity
        
        self.obs_buf[self.ptr] = obs
        self.act_buf[self.ptr] = act
        self.rew_buf[self.ptr] = rew
        self.val_buf[self.ptr] = val
        self.logp_buf[self.ptr] = logp
        
        self.ptr += 1 # Move pointer forward

    def finish_path(self, last_val=0):
        """
        Process the collected episode (or partial episode).
        
        This is called under two conditions:
        1. An episode finishes naturally (the agent wins, dies, etc.). `last_val` is 0.
        2. The buffer is full and cuts off an episode in the middle. `last_val` is 
           the Critic's value prediction for the final state, used to guess future rewards.
           
        This function computes two critical targets for PPO:
        - Advantages (for training the Actor)
        - Returns / Rewards-to-go (for training the Critic)
        """
        # Slice out just the steps belonging to the current episode
        path_slice = slice(self.path_start_idx, self.ptr)
        
        # Add the final state's value to the end of our arrays.
        # This helps calculate the Temporal Difference (TD) error for the very last step.
        rews = np.append(self.rew_buf[path_slice], last_val)
        vals = np.append(self.val_buf[path_slice], last_val)
        
        # -------------------------------------------------------------
        # Step 1: Compute Generalized Advantage Estimation (GAE)
        # -------------------------------------------------------------
        # The TD error (delta) for one step: delta_t = r_t + (gamma * V_t+1) - V_t
        deltas = rews[:-1] + self.gamma * vals[1:] - vals[:-1]
        
        # GAE calculates a smoothed, discounted sum of these TD errors over the episode.
        # We store these advantages to train the Actor network later.
        self.adv_buf[path_slice] = PPO_RolloutBuffer.discount_cumsum(deltas, self.gamma * self.lam)
        
        # -------------------------------------------------------------
        # Step 2: Compute Rewards-to-go (Returns)
        # -------------------------------------------------------------
        # The target for the Critic network is simply the sum of discounted future rewards.
        self.ret_buf[path_slice] = PPO_RolloutBuffer.discount_cumsum(rews, self.gamma)[:-1]
        
        # Update the path_start pointer to where the *next* episode will begin
        self.path_start_idx = self.ptr

    def get(self):
        """
        Retrieve all data from the buffer to train the networks, then reset the buffer.
        This should be called when `ptr` reaches `max_size`.
        """
        assert self.ptr == self.max_size # Ensure the buffer is totally full before training
        
        # Reset pointers to start filling the buffer from scratch next time
        self.ptr, self.path_start_idx = 0, 0
        
        # -------------------------------------------------------------
        # Step 3: Advantage Normalization (Important PPO Trick)
        # -------------------------------------------------------------
        # Standardizing advantages to have a mean of 0 and std deviation of 1.
        # This prevents the Actor network updates from being too erratic,
        # stabilizing and speeding up learning significantly.
        adv_mean, adv_std = np.mean(self.adv_buf), np.std(self.adv_buf)
        self.adv_buf = (self.adv_buf - adv_mean) / (adv_std + 1e-8) # 1e-8 prevents divide-by-zero errors
        
        # Package everything into a dictionary of PyTorch Tensors
        data = dict(obs=self.obs_buf, 
                    act=self.act_buf, 
                    ret=self.ret_buf,
                    adv=self.adv_buf, 
                    logp=self.logp_buf)
        
        return {k: torch.as_tensor(v, dtype=torch.float32) for k, v in data.items()}
