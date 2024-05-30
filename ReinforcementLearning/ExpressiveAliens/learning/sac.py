"""
Soft Actor-Critic (SAC) Reinforcement Learning
Adapted from pyTorch version of Soft Actor Critic Example
https://spinningup.openai.com/en/latest/algorithms/sac.html
"""

from copy import deepcopy
import itertools
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.distributions.normal import Normal
from learning.rl import RL
from learning.rl_helper import RLH
from learning.sac_replay_buffer import SAC_ReplayBuffer

class SAC_SquashedGaussianMLPActor(nn.Module):

    def __init__(self, obs_dim, act_dim, hidden_sizes, activation, act_limit_low, act_limit_high):
        super().__init__()
    
        self.log_std_min = -20.0
        self.log_std_max = 2.0
        self.obs_dim = obs_dim
        self.act_dim = act_dim
        self.act_limit_low = act_limit_low
        self.act_limit_high = act_limit_high
        self.act_limit_range = act_limit_high - act_limit_low
        
        self.mlp = RLH.create_mlp([self.obs_dim] + list(hidden_sizes), activation, activation)
        self.mu_layer = nn.Linear(hidden_sizes[-1], self.act_dim)
        self.log_std_layer = nn.Linear(hidden_sizes[-1], self.act_dim)

    def forward(self, obs, deterministic=False, with_logprob=True):
        net_out = self.mlp(obs)
        mu = self.mu_layer(net_out)
        log_std = self.log_std_layer(net_out)
        log_std = torch.clamp(log_std, self.log_std_min, self.log_std_max)
        std = torch.exp(log_std)

        # Pre-squash distribution and sample
        pi_distribution = Normal(mu, std)
        if deterministic:
            # Only used for evaluating policy at test time.
            pi_action = mu
        else:
            # verify that the sample function in tensorflow is equivalent to rsample in pytorch
            pi_action = pi_distribution.rsample()

        if with_logprob:
            # Compute logprob from Gaussian, and then apply correction for Tanh squashing.
            # NOTE: The correction formula is a little bit magic. To get an understanding 
            # of where it comes from, check out the original SAC paper (arXiv 1801.01290) 
            # and look in appendix C. This is a more numerically-stable equivalent to Eq 21.
            # Try deriving it yourself as a (very difficult) exercise. :)
            logp_pi = pi_distribution.log_prob(pi_action).sum(axis=-1)
            logp_pi -= (2*(np.log(2) - pi_action - F.softplus(-2*pi_action))).sum(axis=1)
        else:
            logp_pi = None

        pi_action = torch.sigmoid(pi_action)
        pi_action = self.act_limit_range * pi_action
        pi_action = self.act_limit_low + pi_action
    
        return pi_action, logp_pi
    
class SAC_MLPQFunction(nn.Module):

    def __init__(self, obs_dim, act_dim, hidden_sizes, activation):
        super().__init__()    
        self.mlp = RLH.create_mlp([obs_dim + act_dim] + list(hidden_sizes) + [1], activation)

    def forward(self, obs, act):
        q = self.mlp(torch.cat([obs, act], dim=-1))
        return torch.squeeze(q, -1) # Critical to ensure q has right shape.

class SAC_MLPActorCritic(nn.Module):

    # TODO: at the moment, all the action limits are assumed to be the same
    # TODO: observation limits are ignored
    def __init__(self, observation_limits, action_limits, hidden_sizes=(256,256), activation=nn.ReLU):
        super().__init__()

        obs_dim = observation_limits.shape[0]
        act_dim = action_limits.shape[0]
        act_limit_low = action_limits[0,0]
        act_limit_high = action_limits[0,1]

        # build policy and value functions
        self.pi = SAC_SquashedGaussianMLPActor(obs_dim, act_dim, hidden_sizes, activation, act_limit_low, act_limit_high)
        self.q1 = SAC_MLPQFunction(obs_dim, act_dim, hidden_sizes, activation)
        self.q2 = SAC_MLPQFunction(obs_dim, act_dim, hidden_sizes, activation)

    def act(self, obs, deterministic=False):
        with torch.no_grad():
            a, _ = self.pi.forward(obs, deterministic=deterministic, with_logprob=False)
            return a.numpy()

class SAC(RL):
    def __init__(self, observation_limits, action_limits, replay_size, mlp_hidden_sizes, mpl_activation, pi_learning_rate, q_learning_rate):
        super(SAC, self).__init__(observation_limits, action_limits, replay_size)
        
        # Create actor-critic
        self.ac = SAC_MLPActorCritic(self.observation_limits, self.action_limits, mlp_hidden_sizes, mpl_activation)
        self.ac_target = deepcopy(self.ac)
        
        # Freeze target networks with respect to optimizers (only update via polyak averaging)
        self.polyak = 0.995
        for p in self.ac_target.parameters():
            p.requires_grad = False
            
        # List of parameters for both Q-networks (save this for convenience)
        self.q_params = itertools.chain(self.ac.q1.parameters(), self.ac.q2.parameters())
        
        # Experience buffer
        self.replay_buffer = SAC_ReplayBuffer(obs_dim=observation_limits.shape[0], act_dim=action_limits.shape[0], size=replay_size)
        
        # Optimizers for policy and q-function
        self.set_learning_rates(1e-4, 1e-4)
        
        # Entropy regularization coefficient
        self.alpha=0.1

    def set_learning_rates(self, pi_learning_rate, q_learning_rate):
        self.pi_learning_rate = 1e-4
        self.q_learning_rate = 1e-4
        
        # Set up optimizers for policy and q-function
        self.pi_optimizer = torch.optim.Adam(self.ac.pi.parameters(), lr=self.pi_learning_rate)
        self.q_optimizer = torch.optim.Adam(self.q_params, lr=self.q_learning_rate)

    #   alpha (float): Entropy regularization coefficient. (Equivalent to 
    #   inverse of reward scale in the original SAC paper.)
    def set_alpha(self, alpha):
        self.alpha=alpha
        
    def load_models(self, file_path, epoch = 0):
        pi_model_full_file_name = "{}/sac_pi_epoch_{}.pth".format(file_path, epoch)
        q1_model_full_file_name = "{}/sac_q1_epoch_{}.pth".format(file_path, epoch)
        q2_model_full_file_name = "{}/sac_q2_epoch_{}.pth".format(file_path, epoch)
        pi_target_model_full_file_name = "{}/sac_pi_target_epoch_{}.pth".format(file_path, epoch)
        q1_target_model_full_file_name = "{}/sac_q1_target_epoch_{}.pth".format(file_path, epoch)
        q2_target_model_full_file_name = "{}/sac_q2_target_epoch_{}.pth".format(file_path, epoch)
        
        self.ac.pi = torch.load(pi_model_full_file_name)
        self.ac.q1 = torch.load(q1_model_full_file_name)
        self.ac.q2 = torch.load(q2_model_full_file_name)
        self.ac_target.pi = torch.load(pi_target_model_full_file_name)
        self.ac_target.q1 = torch.load(q1_target_model_full_file_name)
        self.ac_target.q2 = torch.load(q2_target_model_full_file_name)

    def save_models(self, file_path, epoch = 0):
        pi_model_full_file_name = "{}/sac_pi_epoch_{}.pth".format(file_path, epoch)
        q1_model_full_file_name = "{}/sac_q1_epoch_{}.pth".format(file_path, epoch)
        q2_model_full_file_name = "{}/sac_q2_epoch_{}.pth".format(file_path, epoch)
        pi_target_model_full_file_name = "{}/sac_pi_target_epoch_{}.pth".format(file_path, epoch)
        q1_target_model_full_file_name = "{}/sac_q1_target_epoch_{}.pth".format(file_path, epoch)
        q2_target_model_full_file_name = "{}/sac_q2_target_epoch_{}.pth".format(file_path, epoch)
        
        # save using pickle
        torch.save(self.ac.pi, pi_model_full_file_name)
        torch.save(self.ac.q1, q1_model_full_file_name)
        torch.save(self.ac.q2, q2_model_full_file_name)
        torch.save(self.ac_target.pi, pi_target_model_full_file_name)
        torch.save(self.ac_target.q1, q1_target_model_full_file_name)
        torch.save(self.ac_target.q2, q2_target_model_full_file_name)

    def load_weights(self, file_path, epoch = 0):
        pi_weights_full_file_name = "{}/sac_pi_epoch_{}".format(file_path, epoch)
        q1_weights_full_file_name = "{}/sac_q1_epoch_{}".format(file_path, epoch)
        q2_weights_full_file_name = "{}/sac_q2_epoch_{}".format(file_path, epoch)
        pi_target_weights_full_file_name = "{}/sac_pi_target_epoch_{}".format(file_path, epoch)
        q1_target_weights_full_file_name = "{}/sac_q1_target_epoch_{}".format(file_path, epoch)
        q2_target_weights_full_file_name = "{}/sac_q2_target_epoch_{}".format(file_path, epoch)
        

        self.ac.pi.load_state_dict(torch.load(pi_weights_full_file_name))
        self.ac.q1.load_state_dict(torch.load(q1_weights_full_file_name))
        self.ac.q2.load_state_dict(torch.load(q2_weights_full_file_name))
        self.ac_target.pi.load_state_dict(torch.load(pi_target_weights_full_file_name))
        self.ac_target.q1.load_state_dict(torch.load(q1_target_weights_full_file_name))
        self.ac_target.q2.load_state_dict(torch.load(q2_target_weights_full_file_name))
        
    def save_weights(self, file_path, epoch = 0):
        pi_weights_full_file_name = "{}/sac_pi_epoch_{}".format(file_path, epoch)
        q1_weights_full_file_name = "{}/sac_q1_epoch_{}".format(file_path, epoch)
        q2_weights_full_file_name = "{}/sac_q2_epoch_{}".format(file_path, epoch)
        pi_target_weights_full_file_name = "{}/sac_pi_target_epoch_{}".format(file_path, epoch)
        q1_target_weights_full_file_name = "{}/sac_q1_target_epoch_{}".format(file_path, epoch)
        q2_target_weights_full_file_name = "{}/sac_q2_target_epoch_{}".format(file_path, epoch)
        
        torch.save(self.ac.pi.state_dict(), pi_weights_full_file_name)
        torch.save(self.ac.q1.state_dict(), q1_weights_full_file_name)
        torch.save(self.ac.q2.state_dict(), q2_weights_full_file_name)
        torch.save(self.ac_target.pi.state_dict(), pi_target_weights_full_file_name)
        torch.save(self.ac_target.q1.state_dict(), q1_target_weights_full_file_name)
        torch.save(self.ac_target.q2.state_dict(), q2_target_weights_full_file_name)

    # Set up function for computing SAC Q-losses
    def compute_loss_q(self, data):
        o, a, r, o2, d = data['obs'], data['act'], data['rew'], data['obs2'], data['done']

        q1 = self.ac.q1(o,a)
        q2 = self.ac.q2(o,a)
        
        # Bellman backup for Q functions
        with torch.no_grad():
            # Target actions come from *current* policy
            a2, logp_a2 = self.ac.pi(o2)

            # Target Q-values
            q1_pi_target = self.ac_target.q1(o2, a2)
            q2_pi_target = self.ac_target.q2(o2, a2)
            q_pi_target = torch.min(q1_pi_target, q2_pi_target)
            backup = r + self.gamma * (1 - d) * (q_pi_target - self.alpha * logp_a2)
        
        # MSE loss against Bellman backup
        loss_q1 = ((q1 - backup)**2).mean()
        loss_q2 = ((q2 - backup)**2).mean()
        loss_q = loss_q1 + loss_q2
    
        return loss_q

    # Set up function for computing SAC pi loss
    def compute_loss_pi(self, data):
        o = data['obs']
        pi, logp_pi = self.ac.pi(o)
        q1_pi = self.ac.q1(o, pi)
        q2_pi = self.ac.q2(o, pi)
        q_pi = torch.min(q1_pi, q2_pi)
    
        # Entropy-regularized policy loss
        loss_pi = (self.alpha * logp_pi - q_pi).mean()
       
        return loss_pi
    
    def update(self, data):
        # First run one gradient descent step for Q1 and Q2
        self.q_optimizer.zero_grad()
        loss_q = self.compute_loss_q(data)
        loss_q.backward()
        self.q_optimizer.step()
        
        # Freeze Q-networks so you don't waste computational effort 
        # computing gradients for them during the policy learning step.
        for p in self.q_params:
            p.requires_grad = False
        
        # Next run one gradient descent step for pi.
        self.pi_optimizer.zero_grad()
        loss_pi = self.compute_loss_pi(data)
        loss_pi.backward()
        self.pi_optimizer.step()
        
        # Unfreeze Q-networks so you can optimize it at next DDPG step.
        for p in self.q_params:
            p.requires_grad = True
        
        #print("loss_q ", loss_q, " loss_pi ", loss_pi)
    
        # Finally, update target networks by polyak averaging.
        with torch.no_grad():
            for p, p_target in zip(self.ac.parameters(), self.ac_target.parameters()):
                # NB: We use an in-place operations "mul_", "add_" to update target
                # params, as opposed to "mul" and "add", which would make new tensors.
                p_target.data.mul_(self.polyak)
                p_target.data.add_((1 - self.polyak) * p.data)

    def get_action(self, o, deterministic=False):
        return self.ac.act(torch.as_tensor(o, dtype=torch.float32), deterministic)
    
    def store_experience(self, o, a, r, o2, d):
        self.replay_buffer.store(o, a, r, o2, d)
        
    def replay_experience(self):
        for i in range(self.replay_count):
            batch = self.replay_buffer.sample_batch(self.batch_size)
            self.update(data=batch)
