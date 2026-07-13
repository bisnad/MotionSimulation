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

    def __init__(self, obs_dim, act_dim, num_objectives, hidden_sizes, activation, act_limit_low, act_limit_high):
        super().__init__()

        self.log_std_min = -20.0
        self.log_std_max = 2.0
        self.obs_dim = obs_dim
        self.act_dim = act_dim
        self.num_objectives = num_objectives
        self.act_limit_low = act_limit_low
        self.act_limit_high = act_limit_high
        self.act_limit_range = act_limit_high - act_limit_low

        # Input dimension is expanded to accommodate preference weights `w`
        self.mlp = RLH.create_mlp([self.obs_dim + self.num_objectives] + list(hidden_sizes), activation, activation)
        self.mu_layer = nn.Linear(hidden_sizes[-1], self.act_dim)
        self.log_std_layer = nn.Linear(hidden_sizes[-1], self.act_dim)

    def forward(self, obs, w, deterministic=False, with_logprob=True):
        # Concatenate state observation with the preference weight vector w
        net_in = torch.cat([obs, w], dim=-1)
        net_out = self.mlp(net_in)
        
        mu = self.mu_layer(net_out)
        log_std = self.log_std_layer(net_out)
        log_std = torch.clamp(log_std, self.log_std_min, self.log_std_max)
        std = torch.exp(log_std)

        pi_distribution = Normal(mu, std)
        if deterministic:
            pi_action = mu
        else:
            pi_action = pi_distribution.rsample()

        if with_logprob:
            logp_pi = pi_distribution.log_prob(pi_action).sum(axis=-1)
            logp_pi -= (2*(np.log(2) - pi_action - F.softplus(-2*pi_action))).sum(axis=-1)
        else:
            logp_pi = None

        pi_action = torch.tanh(pi_action)
        scale = self.act_limit_range / 2.0
        shift = self.act_limit_low + scale
        pi_action = pi_action * scale + shift

        return pi_action, logp_pi
    
class SAC_MLPQFunction(nn.Module):

    def __init__(self, obs_dim, act_dim, num_objectives, hidden_sizes, activation):
        super().__init__() 
        # Input: obs, act, and weights w. Output: vector of Q-values of size num_objectives
        self.mlp = RLH.create_mlp([obs_dim + act_dim + num_objectives] + list(hidden_sizes) + [num_objectives], activation)

    def forward(self, obs, act, w):
        # Forward pass returning an un-squeezed vector Q-value [batch, num_objectives]
        q = self.mlp(torch.cat([obs, act, w], dim=-1))
        return q 

class SAC_MLPActorCritic(nn.Module):

    def __init__(self, observation_limits, action_limits, num_objectives, hidden_sizes=(256,256), activation=nn.ReLU):
        super().__init__()

        obs_dim = observation_limits.shape[0]
        act_dim = action_limits.shape[0]
        act_limit_low = action_limits[0,0]
        act_limit_high = action_limits[0,1]

        # build preference-conditioned policy and multi-objective value functions
        self.pi = SAC_SquashedGaussianMLPActor(obs_dim, act_dim, num_objectives, hidden_sizes, activation, act_limit_low, act_limit_high)
        self.q1 = SAC_MLPQFunction(obs_dim, act_dim, num_objectives, hidden_sizes, activation)
        self.q2 = SAC_MLPQFunction(obs_dim, act_dim, num_objectives, hidden_sizes, activation)

    def act(self, obs, w, deterministic=False):
        with torch.no_grad():
            a, _ = self.pi.forward(obs, w, deterministic=deterministic, with_logprob=False)
            return a.cpu().numpy()

class SAC(RL):
    # Added num_objectives to the constructor
    def __init__(self, observation_limits, action_limits, num_objectives, replay_size, mlp_hidden_sizes, mpl_activation, pi_learning_rate, q_learning_rate):
        super(SAC, self).__init__(observation_limits, action_limits, replay_size)

        self.num_objectives = num_objectives
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

        # Create actor-critic with num_objectives
        self.ac = SAC_MLPActorCritic(self.observation_limits, self.action_limits, self.num_objectives, mlp_hidden_sizes, mpl_activation).to(self.device)
        self.ac_target = deepcopy(self.ac).to(self.device)

        self.polyak = 0.995
        for p in self.ac_target.parameters():
            p.requires_grad = False

        self.q_params = itertools.chain(self.ac.q1.parameters(), self.ac.q2.parameters())

        # Experience buffer initialized to handle vectorized rewards
        self.replay_buffer = SAC_ReplayBuffer(obs_dim=observation_limits.shape[0], act_dim=action_limits.shape[0], size=replay_size, num_objectives=self.num_objectives)

        self.target_entropy = -float(action_limits.shape[0])
        self.log_alpha = torch.zeros(1, requires_grad=True, device=self.device)

        self.set_learning_rates(pi_learning_rate, q_learning_rate)
        self.alpha=0.1

    def set_learning_rates(self, pi_learning_rate, q_learning_rate):
        self.pi_learning_rate = pi_learning_rate
        self.q_learning_rate = q_learning_rate
        
        # Set up optimizers for policy, q-functions, and entropy temperature
        self.pi_optimizer = torch.optim.Adam(self.ac.pi.parameters(), lr=self.pi_learning_rate)
        self.q_optimizer = torch.optim.Adam(self.q_params, lr=self.q_learning_rate)
        self.alpha_optimizer = torch.optim.Adam([self.log_alpha], lr=self.pi_learning_rate)

    def set_alpha(self, alpha):
        self.alpha=alpha
        
    def load_models(self, file_path, epoch = 0):
        pi_model_full_file_name = "{}/sac_pi_epoch_{}.pth".format(file_path, epoch)
        q1_model_full_file_name = "{}/sac_q1_epoch_{}.pth".format(file_path, epoch)
        q2_model_full_file_name = "{}/sac_q2_epoch_{}.pth".format(file_path, epoch)
        pi_target_model_full_file_name = "{}/sac_pi_target_epoch_{}.pth".format(file_path, epoch)
        q1_target_model_full_file_name = "{}/sac_q1_target_epoch_{}.pth".format(file_path, epoch)
        q2_target_model_full_file_name = "{}/sac_q2_target_epoch_{}.pth".format(file_path, epoch)
        
        self.ac.pi = torch.load(pi_model_full_file_name, map_location=self.device)
        self.ac.q1 = torch.load(q1_model_full_file_name, map_location=self.device)
        self.ac.q2 = torch.load(q2_model_full_file_name, map_location=self.device)
        self.ac_target.pi = torch.load(pi_target_model_full_file_name, map_location=self.device)
        self.ac_target.q1 = torch.load(q1_target_model_full_file_name, map_location=self.device)
        self.ac_target.q2 = torch.load(q2_target_model_full_file_name, map_location=self.device)

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
        

        self.ac.pi.load_state_dict(torch.load(pi_weights_full_file_name, map_location=self.device))
        self.ac.q1.load_state_dict(torch.load(q1_weights_full_file_name, map_location=self.device))
        self.ac.q2.load_state_dict(torch.load(q2_weights_full_file_name, map_location=self.device))
        self.ac_target.pi.load_state_dict(torch.load(pi_target_weights_full_file_name, map_location=self.device))
        self.ac_target.q1.load_state_dict(torch.load(q1_target_weights_full_file_name, map_location=self.device))
        self.ac_target.q2.load_state_dict(torch.load(q2_target_weights_full_file_name, map_location=self.device))
        
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

    def compute_loss_q(self, data, w):
        o, a, r, o2, d = data['obs'], data['act'], data['rew'], data['obs2'], data['done']

        # Vectorized Q-values conditioned on w
        q1_vec = self.ac.q1(o, a, w)
        q2_vec = self.ac.q2(o, a, w)

        with torch.no_grad():
            a2, logp_a2 = self.ac.pi(o2, w)

            q1_pi_target_vec = self.ac_target.q1(o2, a2, w)
            q2_pi_target_vec = self.ac_target.q2(o2, a2, w)
            
            # Element-wise min for the Q-value vectors
            q_pi_target_vec = torch.min(q1_pi_target_vec, q2_pi_target_vec)

            alpha = self.log_alpha.exp().detach()
            
            # Broadcast dimensions to match [batch, num_objectives] for backup
            d_expanded = d.unsqueeze(-1)
            logp_expanded = logp_a2.unsqueeze(-1)
            
            # Bellman backup for vectors (Entropy subtracted from all objectives)
            backup = r + self.gamma * (1 - d_expanded) * (q_pi_target_vec - alpha * logp_expanded)

        # MSE loss on vectors
        loss_q1 = ((q1_vec - backup)**2).mean()
        loss_q2 = ((q2_vec - backup)**2).mean()
        loss_q = loss_q1 + loss_q2

        return loss_q

    def compute_loss_pi(self, data, w):
        o = data['obs']
        pi, logp_pi = self.ac.pi(o, w)
        
        q1_pi_vec = self.ac.q1(o, pi, w)
        q2_pi_vec = self.ac.q2(o, pi, w)
        
        # Scalarize Q-values using the specific preference vector w
        q1_pi_scalar = (q1_pi_vec * w).sum(dim=-1)
        q2_pi_scalar = (q2_pi_vec * w).sum(dim=-1)
        
        q_pi_scalar = torch.min(q1_pi_scalar, q2_pi_scalar)

        alpha = self.log_alpha.exp().detach()
        loss_pi = (alpha * logp_pi - q_pi_scalar).mean()

        return loss_pi, logp_pi

    def update(self, data):
        # Sample uniformly distributed preference weights w for this batch update
        batch_size = data['obs'].shape[0]
        w = torch.rand(batch_size, self.num_objectives, device=self.device)
        w = w / w.sum(dim=-1, keepdim=True) # Normalize so w sums to 1
        
        # 1. Update Q1 and Q2
        self.q_optimizer.zero_grad()
        loss_q = self.compute_loss_q(data, w)
        loss_q.backward()
        self.q_optimizer.step()

        for p in self.q_params:
            p.requires_grad = False

        # 2. Update pi
        self.pi_optimizer.zero_grad()
        loss_pi, logp_pi = self.compute_loss_pi(data, w)
        loss_pi.backward()
        self.pi_optimizer.step()

        for p in self.q_params:
            p.requires_grad = True

        # 3. Update alpha
        self.alpha_optimizer.zero_grad()
        loss_alpha = -(self.log_alpha * (logp_pi + self.target_entropy).detach()).mean()
        loss_alpha.backward()
        self.alpha_optimizer.step()

        # 4. Target networks polyak
        with torch.no_grad():
            for p, p_target in zip(self.ac.parameters(), self.ac_target.parameters()):
                p_target.data.mul_(self.polyak)
                p_target.data.add_((1 - self.polyak) * p.data)

    def get_action(self, o, w, deterministic=False):
        # Both observation and preference w must be passed in
        obs_tensor = torch.as_tensor(o, dtype=torch.float32).to(self.device)
        w_tensor = torch.as_tensor(w, dtype=torch.float32).to(self.device)
        return self.ac.act(obs_tensor, w_tensor, deterministic)

    def store_experience(self, o, a, r, o2, d):
        self.replay_buffer.store(o, a, r, o2, d)

    def replay_experience(self):
        for i in range(self.replay_count):
            batch = self.replay_buffer.sample_batch(self.batch_size)
            batch = {k: v.to(self.device) for k, v in batch.items()}
            self.update(data=batch)
