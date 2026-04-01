import numpy as np
import torch
import torch.nn as nn
from torch.optim import Adam
from torch.distributions.normal import Normal

from learning.rl import RL
from learning.rl_helper import RLH

class PPO_GaussianMLPActor(nn.Module):
    def __init__(self, obs_dim, act_dim, hidden_sizes, activation, action_limits):
        super().__init__()

        self.mu_net = RLH.create_mlp([obs_dim] + list(hidden_sizes) + [act_dim], activation)
        self.log_std = nn.Parameter(-0.5 * torch.ones(act_dim, dtype=torch.float32))

        action_limits = np.asarray(action_limits, dtype=np.float32)
        self.register_buffer("act_limit_low", torch.as_tensor(action_limits[:, 0], dtype=torch.float32))
        self.register_buffer("act_limit_high", torch.as_tensor(action_limits[:, 1], dtype=torch.float32))
        self.register_buffer("act_limit_range", self.act_limit_high - self.act_limit_low)

    def _distribution(self, obs):
        mu = self.mu_net(obs)
        std = torch.exp(self.log_std)
        return Normal(mu, std)

    def forward(self, obs, act=None):
        pi = self._distribution(obs)
        logp_a = None

        if act is not None:
            # act here is the raw Gaussian sample stored in the rollout buffer
            logp_a = pi.log_prob(act).sum(axis=-1)

        return pi, logp_a

    def raw_action_to_env_action(self, raw_action):
        if torch.is_tensor(raw_action):
            low = self.act_limit_low.to(raw_action.device)
            rng = self.act_limit_range.to(raw_action.device)
            return low + rng * torch.sigmoid(raw_action)

        raw_action = torch.as_tensor(raw_action, dtype=torch.float32)
        env_action = self.act_limit_low + self.act_limit_range * torch.sigmoid(raw_action)
        return env_action.cpu().numpy()


class PPO_MLPValueFunction(nn.Module):
    def __init__(self, obs_dim, hidden_sizes, activation):
        super().__init__()
        self.v_net = RLH.create_mlp([obs_dim] + list(hidden_sizes) + [1], activation)

    def forward(self, obs):
        return torch.squeeze(self.v_net(obs), -1)


class PPO_MLPActorCritic(nn.Module):
    def __init__(self, observation_limits, action_limits, hidden_sizes=(256, 256), activation=nn.ReLU):
        super().__init__()

        obs_dim = len(observation_limits)
        act_dim = len(action_limits)

        self.pi = PPO_GaussianMLPActor(obs_dim, act_dim, hidden_sizes, activation, action_limits)
        self.v = PPO_MLPValueFunction(obs_dim, hidden_sizes, activation)

    def step(self, obs):
        with torch.no_grad():
            pi = self.pi._distribution(obs)
            a = pi.sample()                      # raw Gaussian action for PPO training
            logp_a = pi.log_prob(a).sum(axis=-1)
            v = self.v(obs)

        return a.cpu().numpy(), v.cpu().numpy(), logp_a.cpu().numpy()

    def act(self, obs):
        a_raw, _, _ = self.step(obs)
        return self.pi.raw_action_to_env_action(a_raw)


class PPO:
    def __init__(
        self,
        observation_limits,
        action_limits,
        replay_size,
        hidden_sizes=(256, 256),
        activation=nn.ReLU,
        clip_ratio=0.2,
        pi_lr=3e-4,
        vf_lr=1e-3,
        train_pi_iters=80,
        train_v_iters=80,
        target_kl=0.01,
    ):
        self.clip_ratio = clip_ratio
        self.train_pi_iters = train_pi_iters
        self.train_v_iters = train_v_iters
        self.target_kl = target_kl

        self.ac = PPO_MLPActorCritic(
            observation_limits,
            action_limits,
            hidden_sizes=hidden_sizes,
            activation=activation,
        )

        self.pi_optimizer = Adam(self.ac.pi.parameters(), lr=pi_lr)
        self.v_optimizer = Adam(self.ac.v.parameters(), lr=vf_lr)

    def compute_loss_pi(self, data):
        obs, act, adv, logp_old = data["obs"], data["act"], data["adv"], data["logp"]

        _, logp = self.ac.pi(obs, act)
        ratio = torch.exp(logp - logp_old)

        clipped_ratio = torch.clamp(ratio, 1 - self.clip_ratio, 1 + self.clip_ratio)
        loss_pi = -(torch.min(ratio * adv, clipped_ratio * adv)).mean()

        approx_kl = (logp_old - logp).mean().item()
        return loss_pi, approx_kl

    def compute_loss_v(self, data):
        obs, ret = data["obs"], data["ret"]
        return ((self.ac.v(obs) - ret) ** 2).mean()

    def update(self, rollout_buffer):
        data = rollout_buffer.get()

        for i in range(self.train_pi_iters):
            self.pi_optimizer.zero_grad()
            loss_pi, kl = self.compute_loss_pi(data)

            if kl > 1.5 * self.target_kl:
                print(f"Early stopping at step {i} due to reaching max kl.")
                break

            loss_pi.backward()
            self.pi_optimizer.step()

        for _ in range(self.train_v_iters):
            self.v_optimizer.zero_grad()
            loss_v = self.compute_loss_v(data)
            loss_v.backward()
            self.v_optimizer.step()

    def load_models(self, file_path, epoch=0):
        pi_model_full_file_name = "{}/ppo_pi_epoch_{}.pth".format(file_path, epoch)
        v_model_full_file_name = "{}/ppo_v_epoch_{}.pth".format(file_path, epoch)

        self.ac.pi = torch.load(pi_model_full_file_name)
        self.ac.v = torch.load(v_model_full_file_name)

    def save_models(self, file_path, epoch=0):
        pi_model_full_file_name = "{}/ppo_pi_epoch_{}.pth".format(file_path, epoch)
        v_model_full_file_name = "{}/ppo_v_epoch_{}.pth".format(file_path, epoch)

        torch.save(self.ac.pi, pi_model_full_file_name)
        torch.save(self.ac.v, v_model_full_file_name)

    def load_weights(self, file_path, epoch=0):
        pi_weights_full_file_name = "{}/ppo_pi_epoch_{}".format(file_path, epoch)
        v_weights_full_file_name = "{}/ppo_v_epoch_{}".format(file_path, epoch)

        self.ac.pi.load_state_dict(torch.load(pi_weights_full_file_name))
        self.ac.v.load_state_dict(torch.load(v_weights_full_file_name))

    def save_weights(self, file_path, epoch=0):
        pi_weights_full_file_name = "{}/ppo_pi_epoch_{}".format(file_path, epoch)
        v_weights_full_file_name = "{}/ppo_v_epoch_{}".format(file_path, epoch)

        torch.save(self.ac.pi.state_dict(), pi_weights_full_file_name)
        torch.save(self.ac.v.state_dict(), v_weights_full_file_name)