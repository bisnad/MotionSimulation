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
            pi_action = mu
        else:
            pi_action = pi_distribution.rsample()

        if with_logprob:
            # Compute logprob from Gaussian, and then apply correction for Tanh squashing.
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
            return a.cpu().numpy()

class SAC(RL):
    def __init__(self, observation_limits, action_limits, replay_size, mlp_hidden_sizes, mpl_activation, 
                 pi_learning_rate, q_learning_rate, auto_entropy=True, init_alpha=0.1, target_entropy=None,
                 reward_scale=1.0, reward_clip=10.0, target_q_clip=100.0):
        super(SAC, self).__init__(observation_limits, action_limits, replay_size)

        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.auto_entropy = auto_entropy
        self.reward_scale = reward_scale
        self.reward_clip = reward_clip
        self.target_q_clip = target_q_clip

        # Create actor-critic
        self.ac = SAC_MLPActorCritic(self.observation_limits, self.action_limits, mlp_hidden_sizes, mpl_activation).to(self.device)
        self.ac_target = deepcopy(self.ac).to(self.device)

        # Freeze target networks with respect to optimizers (only update via polyak averaging)
        self.polyak = 0.995
        for p in self.ac_target.parameters():
            p.requires_grad = False

        # List of parameters for both Q-networks (save this for convenience)
        self.q_params = itertools.chain(self.ac.q1.parameters(), self.ac.q2.parameters())

        # Experience buffer
        self.replay_buffer = SAC_ReplayBuffer(obs_dim=observation_limits.shape[0], act_dim=action_limits.shape[0], size=replay_size)

        # Entropy Tuning configuration
        if target_entropy is None:
            self.target_entropy = -float(action_limits.shape[0])
        else:
            self.target_entropy = float(target_entropy)

        # Start log_alpha at the log of init_alpha
        self.log_alpha = torch.tensor([np.log(init_alpha)], requires_grad=True, device=self.device, dtype=torch.float32)
        self.alpha = init_alpha

        # Optimizers for policy and q-function
        self.set_learning_rates(pi_learning_rate, q_learning_rate)
        
        self.lr_decay_enabled = False

    def set_learning_rates(self, pi_learning_rate, q_learning_rate):
        self.pi_learning_rate = pi_learning_rate
        self.q_learning_rate = q_learning_rate

        # Set up optimizers for policy, q-functions, and entropy temperature
        self.pi_optimizer = torch.optim.Adam(self.ac.pi.parameters(), lr=self.pi_learning_rate)
        self.q_optimizer = torch.optim.Adam(self.q_params, lr=self.q_learning_rate)
        
        if self.auto_entropy:
            self.alpha_optimizer = torch.optim.Adam([self.log_alpha], lr=self.pi_learning_rate)
            
    def configure_lr_decay(self, enabled=False, gamma=0.9995, min_pi_learning_rate=1e-6, min_q_learning_rate=1e-5):
        self.lr_decay_enabled = enabled
        if enabled:
            self.pi_scheduler = torch.optim.lr_scheduler.ExponentialLR(self.pi_optimizer, gamma=gamma)
            self.q_scheduler = torch.optim.lr_scheduler.ExponentialLR(self.q_optimizer, gamma=gamma)
            if self.auto_entropy:
                self.alpha_scheduler = torch.optim.lr_scheduler.ExponentialLR(self.alpha_optimizer, gamma=gamma)

    def step_lr_schedulers(self):
        if self.lr_decay_enabled:
            self.pi_scheduler.step()
            self.q_scheduler.step()
            if self.auto_entropy:
                self.alpha_scheduler.step()

    def load_models(self, file_path, epoch = 0):
        # omitted for brevity, keep your original implementation...
        pass

    def save_models(self, file_path, epoch = 0):
        # omitted for brevity, keep your original implementation...
        pass

    def load_weights(self, file_path, epoch = 0):
        # omitted for brevity, keep your original implementation...
        pass

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
        
        # Scale reward if requested
        r = r * self.reward_scale

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

            # Use dynamically computed alpha for backup or fixed if not auto
            alpha = self.log_alpha.exp().detach() if self.auto_entropy else self.alpha
            backup = r + self.gamma * (1 - d) * (q_pi_target - alpha * logp_a2)

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

        # Entropy-regularized policy loss using dynamically computed alpha
        alpha = self.log_alpha.exp().detach() if self.auto_entropy else self.alpha
        loss_pi = (alpha * logp_pi - q_pi).mean()

        # Return logp_pi so we can use it to train alpha later
        return loss_pi, logp_pi

    def update(self, data):
        # 1. First run one gradient descent step for Q1 and Q2
        self.q_optimizer.zero_grad()
        loss_q = self.compute_loss_q(data)
        loss_q.backward()
        self.q_optimizer.step()

        # Freeze Q-networks so you don't waste computational effort 
        # computing gradients for them during the policy learning step.
        for p in self.q_params:
            p.requires_grad = False

        # 2. Next run one gradient descent step for pi.
        self.pi_optimizer.zero_grad()
        loss_pi, logp_pi = self.compute_loss_pi(data)
        loss_pi.backward()
        self.pi_optimizer.step()

        # Unfreeze Q-networks so you can optimize it at next DDPG step.
        for p in self.q_params:
            p.requires_grad = True

        # 3. Update the temperature parameter (alpha)
        if self.auto_entropy:
            self.alpha_optimizer.zero_grad()
            # Alpha loss: move alpha towards the target entropy
            loss_alpha = -(self.log_alpha * (logp_pi + self.target_entropy).detach()).mean()
            loss_alpha.backward()
            self.alpha_optimizer.step()

        # 4. Finally, update target networks by polyak averaging.
        with torch.no_grad():
            for p, p_target in zip(self.ac.parameters(), self.ac_target.parameters()):
                p_target.data.mul_(self.polyak)
                p_target.data.add_((1 - self.polyak) * p.data)

    def get_action(self, o, deterministic=False):
        obs_tensor = torch.as_tensor(o, dtype=torch.float32).to(self.device)
        return self.ac.act(obs_tensor, deterministic)

    def store_experience(self, o, a, r, o2, d):
        self.replay_buffer.store(o, a, r, o2, d)

    def replay_experience(self):
        for i in range(self.replay_count):
            batch = self.replay_buffer.sample_batch(self.batch_size)
            batch = {k: v.to(self.device) for k, v in batch.items()}
            self.update(data=batch)