"""
this trains an agent with constant values for dist and effort
dist in this case is not movement distance but distance between agent and a target
replaced te non-feet floor contact with a non-live ending negative reward
also, there is no conditional control for the agent
"""

import sys
import math
import random
import numpy as np
import torch
import torch.nn as nn
import pybullet
import gym
import time
import json
import matplotlib
matplotlib.use('Agg') # Prevent flickering windows (Use the 'Agg' backend)
import matplotlib.pyplot as plt
from PIL import Image
from common.plot_utils import PlotUtils
from common.ringbuffer import RingBuffer
from matplotlib import animation
from simulation.thing import Thing
from simulation.utils import Utils
from custom.agents.custom_agent import CustomAgent
from analysis.analysis import Analysis

# import agent states
from custom.states.custom_state import CustomState
from custom.states.agent_states.body_initial_height_diff_state import BodyInitialHeightDiffState
from custom.states.agent_states.body_position_state import BodyPositionState
from custom.states.agent_states.body_rotation_state import BodyRotationState
from custom.states.agent_states.body_velocity_state import BodyVelocityState
from custom.states.agent_states.ground_contact_state import GroundContactState
from custom.states.agent_states.joint_rel_state import JointRelState
from custom.states.agent_states.body_target_state import BodyTargetState

# import alive states
from custom.states.alive_states.ground_contact_state import GroundContactState as GroundContactAliveState
from custom.states.alive_states.max_velocity_state import MaxVelocityState as MaxVelocityState

# import rewards
from custom.rewards.alive_reward import AliveReward
from custom.rewards.body_velocity_alignment_reward import BodyVelocityAlignmentReward
from custom.rewards.feet_collision_reward import FeetCollisionReward
from custom.rewards.joint_reward import JointReward
from custom.rewards.move_distance_reward import MoveDistanceReward
from custom.rewards.impulse_reward import ImpulseReward
from custom.rewards.weight_effort_reward import WeightEffortReward
from custom.rewards.time_effort_reward import TimeEffortReward
from custom.rewards.space_effort_reward import SpaceEffortReward
from custom.rewards.flow_effort_reward import FlowEffortReward
from custom.rewards.target_distance_reward import TargetDistanceReward
from custom.rewards.ground_contact_reward import GroundContactReward

# import PPO modules
from learning.ppo import PPO
from learning.ppo_rollout_buffer import PPO_RolloutBuffer

# custom environment
from custom.envs.custom_environment import CustomEnvironment
env_name = "Custom_Environment"

"""
configuration
"""

result_file_path = "results/biped_constant_ppo_run4"

"""
configuration: agent
"""

agent_model_file_path = "3d_models/insect_quadruped_v1/body.urdf"
agent_power = 4.0
agent_reset_position = [0.0, 0.0, 0.75]
agent_reset_orientation = [0.0, 0.0, 1.0, 0.0]
agent_feet_names = ["lowerlimb", "lowerlimb_2", "lowerlimb_3", "lowerlimb_4"]
agent_allow_self_collisions = True

"""
configuration: target
"""

target_min_center_dist = 4.
target_max_center_dist = 10.
target_reset_when_agent_close = True
target_reset_agent_max_distance = 0.5

"""
configuration: agent costs and rewards
"""

# alive
agent_alive_cost = 0.1
agent_not_alive_cost = -100
agent_alive_reward_scale = 1.0

# proprioception
agent_joint_comfort_rotation_range = 0.7
agent_joint_comfort_force_range = 5000
agent_joint_max_force = 10000.0
agent_joint_torque_cost = -0.5 # costs for applying torque to joint (exhaustion)
agent_joint_limit_cost = -0.2 # costs for joint rotation close to limit (comfort)
agent_joint_rotation_cost = -0.02 # costs for joint rotation outside of preferred range (comfort)
agent_joint_force_cost = -0.02 # costs for forces applied to joints along their fixed digrees of freedom (comfort)
agent_joint_reward_scale = 0.0 # 1.0

# feet with body collision
agent_feet_collision_cost = -1.0
agent_feet_collision_reward_scale = 1.0

# non-feet with ground collision
agent_ground_contact_cost = -100

# body movement direction
agent_body_misalignment_cost = -1.0
agent_body_misalignment_reward_scale = 0.0

# movement distance
agent_move_distance_reward_scale = 0.0

# target distance
agent_target_distance_reward_scale = 0.0

# weight effort
agent_weight_effort_target_value = 0.0
agent_weight_effort_reward_scale = 0.0
agent_weight_effort_max_value = 200.0

# time effort
agent_time_effort_target_value = 0.0
agent_time_effort_reward_scale = 0.0
agent_time_effort_max_value = 300.0

# space effort
agent_space_effort_target_value = 0.0
agent_space_effort_reward_scale = 0.0
agent_space_effort_max_value = 20.0

# flow effort
agent_flow_effort_target_value = 0.0
agent_flow_effort_reward_scale = 0.0
agent_flow_effort_max_value = 20000.0

"""
configuration: model
"""

ppo_pi_learning_rate = 1e-4
ppo_vf_learning_rate = 1e-4
ppo_steps_per_epoch = int(1e6)
ppo_hidden_sizes=(256, 256, 256)
ppo_activation=nn.ReLU

"""
configuration: training
"""

epochs=500
batch_size=256
env_count = 4
steps_per_epoch=5000
target_kl = 0.02
start_steps=5000 # number of initial steps when actions are taken randomly rather than from sac model
update_after=1000 # update step after which training of the sac model starts 
update_every=50 # once training started, number of steps after which training of model is repeated
max_ep_len=800 # Maximum length of trajectory / episode / rollout.

"""
configuration: visualization
"""
render = False

"""
configuration: load/save model weights amd replay buffer
"""

load_epoch = 0
load_model_weights = False
save_epoch_interval = 100
save_model_weights = False

"""
Read configs
"""

# config_path
argCount = len(sys.argv)
if argCount > 1:
    config_path = sys.argv[1]
else:
    config_path = "{}/config.json".format(result_file_path)    

with open(config_path) as json_file: 
    config_data = json.load(json_file) 

    # data settings
    data_config = config_data["data"]
    result_file_path = data_config["result_file_path"]

    # agent settings 
    agent_config = config_data["agent"]
    agent_model_file_path = agent_config["agent_model_file_path"]
    agent_power = agent_config["agent_power"]
    agent_reset_position = agent_config["agent_reset_position"]
    agent_reset_orientation = agent_config["agent_reset_orientation"]
    agent_feet_names = agent_config["agent_feet_names"]
    agent_allow_self_collisions = agent_config["agent_allow_self_collisions"]
    
    # target settings 
    target_config = config_data["target"]
    target_min_center_dist = target_config["target_min_center_dist"]
    target_max_center_dist = target_config["target_max_center_dist"]
    target_reset_when_agent_close = target_config["target_reset_when_agent_close"]
    target_reset_agent_max_distance = target_config["target_reset_agent_max_distance"]

    # agent cost and rewards
    rewards_config = config_data["reward"]
    
    agent_alive_cost = rewards_config["agent_alive_cost"]
    agent_not_alive_cost = rewards_config["agent_not_alive_cost"]
    agent_alive_reward_scale = rewards_config["agent_alive_reward_scale"]
    
    agent_joint_comfort_rotation_range = rewards_config["agent_joint_comfort_rotation_range"]
    agent_joint_comfort_force_range = rewards_config["agent_joint_comfort_force_range"]
    agent_joint_max_force = rewards_config["agent_joint_max_force"]
    agent_joint_torque_cost = rewards_config["agent_joint_torque_cost"]
    agent_joint_limit_cost = rewards_config["agent_joint_limit_cost"]
    agent_joint_rotation_cost = rewards_config["agent_joint_rotation_cost"]
    agent_joint_force_cost = rewards_config["agent_joint_force_cost"]
    agent_joint_reward_scale = rewards_config["agent_joint_reward_scale"]
    
    agent_feet_collision_cost = rewards_config["agent_feet_collision_cost"]
    agent_feet_collision_reward_scale = rewards_config["agent_feet_collision_reward_scale"]
    
    agent_ground_contact_cost = rewards_config["agent_ground_contact_cost"]

    agent_move_distance_reward_scale = rewards_config["agent_move_distance_reward_scale"]
    
    agent_target_distance_reward_scale = rewards_config["agent_target_distance_reward_scale"]

    agent_weight_effort_target_value = rewards_config["agent_weight_effort_target_value"]
    agent_weight_effort_reward_scale = rewards_config["agent_weight_effort_reward_scale"]
    agent_weight_effort_max_value = rewards_config["agent_weight_effort_max_value"]
    
    agent_time_effort_target_value = rewards_config["agent_time_effort_target_value"]
    agent_time_effort_reward_scale = rewards_config["agent_time_effort_reward_scale"]
    agent_time_effort_max_value = rewards_config["agent_time_effort_max_value"]
    
    agent_space_effort_target_value = rewards_config["agent_space_effort_target_value"]
    agent_space_effort_reward_scale = rewards_config["agent_space_effort_reward_scale"]
    agent_space_effort_max_value = rewards_config["agent_space_effort_max_value"]
    
    agent_flow_effort_target_value = rewards_config["agent_flow_effort_target_value"]
    agent_flow_effort_reward_scale = rewards_config["agent_flow_effort_reward_scale"]
    agent_flow_effort_max_value = rewards_config["agent_flow_effort_max_value"]

    # model settings 
    model_config = config_data["model"]
    ppo_pi_learning_rate = model_config["ppo_pi_learning_rate"]
    ppo_vf_learning_rate = model_config["ppo_vf_learning_rate"]
    ppo_hidden_sizes= model_config["ppo_hidden_sizes"]

    # training settings
    training_config = config_data["training"]
    epochs = training_config["epochs"]
    batch_size = training_config["batch_size"]
    env_count = training_config["env_count"]
    target_kl = training_config["target_kl"]
    steps_per_epoch = training_config["steps_per_epoch"]
    start_steps = training_config["start_steps"]
    update_after = training_config["update_after"]
    update_every = training_config["update_every"]
    max_ep_len = training_config["max_ep_len"]

    # visualization settings
    visualization_config = config_data["visualization"]
    render = visualization_config["render"]
    
    # save config
    save_config = config_data["save"]
    load_epoch = save_config["load_epoch"]
    load_model_weights = save_config["load_model_weights"]
    save_epoch_interval = save_config["save_epoch_interval"]
    save_model_weights = save_config["save_model_weights"]

# initialize random number generators
seed = 0
torch.manual_seed(seed)
np.random.seed(seed)

# create environments

class GymCompatWrapper(gym.Wrapper):
    """
    Adapts old-style custom envs to the API expected by gym.vector.SyncVectorEnv.

    Old reset: obs
    New reset: (obs, info)

    Old step: (obs, reward, done, info)
    New step: (obs, reward, terminated, truncated, info)
    """

    def reset(self, **kwargs):
        result = self.env.reset()

        if isinstance(result, tuple) and len(result) == 2 and isinstance(result[1], dict):
            return result

        return result, {}

    def step(self, action):
        result = self.env.step(action)

        if len(result) == 4:
            obs, reward, done, info = result
            return obs, reward, done, False, info

        return result

def make_env(rank):
    def _thunk():
        env = gym.make(env_name)

        # Give this specific environment a unique random seed
        env_seed = 42 + rank
        env.seed(env_seed)
        env.action_space.seed(env_seed)
        
        # load agent and ground
        ground = Thing("plane", "3d_models/plane2/plane.urdf")
        target = Thing("target", "3d_models/pillar/pillar.urdf")
        agent = CustomAgent("agent", agent_model_file_path)
        agent.power = agent_power
        
        env.add_ground(ground)
        env.add_target(target)
        env.add_agent(agent)
        
        # Expose agent and target directly to env for easy access later
        env.agent_obj = agent 
        env.target_obj = target
        
        agent.set_reset_position(agent_reset_position)
        agent.set_reset_orientation(agent_reset_orientation)
        
        # Add states
        agent.add_state(JointRelState(), "joints")
        
        gc_state = GroundContactState()
        gc_state.part_names = agent_feet_names
        agent.add_state(gc_state, "groundContact")
        
        agent.add_state(BodyInitialHeightDiffState(), "heightDiff")
        
        bp_state = BodyPositionState()
        bp_state.normalise = True
        agent.add_state(bp_state, "bodyPos")
        agent.add_state(BodyRotationState(), "bodyRot")
        agent.add_state(BodyVelocityState(), "bodyVel")
        agent.add_state(BodyTargetState(), "bodyTarget")
        
        # Add alive states
        al_state = GroundContactAliveState()
        al_state.feet_names = agent_feet_names
        agent.add_alive_state(al_state, "alive")
        
        al2_state = MaxVelocityState()
        al2_state.max_linear_speed = 10.0
        al2_state.max_angular_speed = 100.0
        agent.add_alive_state(al2_state, "alive2")
        
        # Add Rewards (Simplified initialization for brevity, keep your exact reward values here)
        aliveReward = AliveReward()
        aliveReward.alive_value = agent_alive_cost
        aliveReward.not_alive_value = agent_not_alive_cost
        aliveReward.reward_scale = agent_alive_reward_scale

        jointReward = JointReward()
        jointReward.comfort_rotation_range = agent_joint_comfort_rotation_range
        jointReward.comfort_force_range = agent_joint_comfort_force_range
        jointReward.max_force = agent_joint_max_force
        jointReward.torque_cost = agent_joint_torque_cost
        jointReward.limit_cost = agent_joint_limit_cost
        jointReward.rotation_cost = agent_joint_rotation_cost
        jointReward.force_cost = agent_joint_force_cost
        jointReward.reward_scale = agent_joint_reward_scale

        feetCollisionReward = FeetCollisionReward()
        feetCollisionReward.feet_names = agent_feet_names
        feetCollisionReward.feet_collision_cost = agent_feet_collision_cost
        feetCollisionReward.reward_scale = agent_feet_collision_reward_scale

        groundContactReward = GroundContactReward()
        groundContactReward.feet_names = agent_feet_names
        groundContactReward.ground_collision_cost = agent_ground_contact_cost

        bodyVelocityAlignmentReward = BodyVelocityAlignmentReward()
        bodyVelocityAlignmentReward.misalignment_cost = agent_body_misalignment_cost
        bodyVelocityAlignmentReward.reward_scale = agent_body_misalignment_reward_scale

        moveDistanceReward = MoveDistanceReward()
        moveDistanceReward.reward_scale  = agent_move_distance_reward_scale

        targetDistanceReward = TargetDistanceReward()
        targetDistanceReward.reward_scale  = agent_target_distance_reward_scale

        weightEffortReward = WeightEffortReward()
        weightEffortReward.reward_scale = agent_weight_effort_reward_scale
        weightEffortReward.target_value = agent_weight_effort_target_value
        weightEffortReward.max_value = agent_weight_effort_max_value

        timeEffortReward = TimeEffortReward()
        timeEffortReward.reward_scale = agent_time_effort_reward_scale
        timeEffortReward.target_value = agent_time_effort_target_value
        timeEffortReward.max_value = agent_time_effort_max_value

        spaceEffortReward = SpaceEffortReward()
        spaceEffortReward.reward_scale = agent_space_effort_reward_scale
        spaceEffortReward.target_value = agent_space_effort_target_value
        spaceEffortReward.max_value = agent_space_effort_max_value

        flowEffortReward = FlowEffortReward()
        flowEffortReward.reward_scale = agent_flow_effort_reward_scale
        flowEffortReward.target_value = agent_flow_effort_target_value
        flowEffortReward.max_value = agent_flow_effort_max_value

        env.add_reward(aliveReward, "alive")
        env.add_reward(jointReward, "joint")
        env.add_reward(feetCollisionReward, "feet")
        env.add_reward(groundContactReward, "ground")
        env.add_reward(bodyVelocityAlignmentReward, "vel_align")
        env.add_reward(moveDistanceReward, "move_dist")
        env.add_reward(targetDistanceReward, "target_dist")
        env.add_reward(weightEffortReward, "weight_effort")
        env.add_reward(timeEffortReward, "time_effort")
        env.add_reward(spaceEffortReward, "space_effort")
        env.add_reward(flowEffortReward, "flow_effort")

        # reset environments which initialises environment information
        env.setDisplay(render)
        _ = env.reset()

        # agent self collisions
        if agent_allow_self_collisions == False:
            agent.body.deactivate_self_collisions()

        # add texture to ground
        textureId = env.physics.loadTexture("textures/ground_grid2.png")
        env.physics.changeVisualShape(env.ground.body.id, -1, -1, textureId)

        return GymCompatWrapper(env)

    return _thunk

# Setup Vectorized Environments
num_envs = env_count # Spawn 4 parallel physics simulations
envs = gym.vector.SyncVectorEnv([make_env(i) for i in range(num_envs)])

# Create a temporary environment just to extract observation/action limits
temp_env = make_env(0)()

env_observation_space = temp_env.observation_space
env_action_space = temp_env.action_space

env_observation_limits = np.stack( [env_observation_space.low, env_observation_space.high], axis=1)
env_action_limits = np.stack( [env_action_space.low, env_action_space.high], axis=1)

def randomise_target_pos(env_index):
    
    # generate random target distance and angle
    dist = target_min_center_dist + (target_max_center_dist - target_min_center_dist) * random.random()
    angle = random.random() * math.pi * 2.0
    t_pos = [dist * math.cos(angle), dist * math.sin(angle), 0.5]
    envs.envs[env_index].target_obj.body.set_position(t_pos)
    envs.envs[env_index].target_obj.set_reset_position(t_pos)

# output gym render frames as gif
def save_frames_as_gif(frames, path='./', filename='gym_animation.gif'):
    """
    Saves environment rgb_array frames directly to a GIF.
    This is magnitudes faster than matplotlib.animation.
    """
    print("save_frames_as_gif frames l ", len(frames))
    
    # Convert numpy arrays to Pillow Images
    images = [Image.fromarray(frame) for frame in frames]
    
    # Save the first image and append the rest (60 fps = ~16.6 ms per frame)
    images[0].save(
        path + filename, 
        save_all=True, 
        append_images=images[1:], 
        duration=16.6, 
        loop=0
    )

# output pillow images as gif
def save_images_as_gif(images, path='./', filename='gym_animation.gif'):
    """
    Saves a list of Pillow Images (from PlotUtils) directly to a GIF.
    """
    images[0].save(
        path + filename, 
        save_all=True, 
        append_images=images[1:], 
        duration=16.6, 
        loop=0
    )

def export_episode(env, sim_file, reward_file, value_file):

    print("export_episode sim_file ", sim_file, " reward_file ", reward_file, " value_file ", value_file)

    episode_rewards = {}
    episode_values = {}
    
    for reward_name in env.reward_names:
        episode_rewards[reward_name] = []
        episode_values[reward_name] = []
    
    sim_images = []

    randomise_target_pos()
    o, ep_ret, ep_len = env.reset(), 0, 0

    for t in range(max_ep_len):

        # Sample raw PPO action, value, and log-probability
        a_raw, v, logp = ppo.ac.step(torch.as_tensor(o, dtype=torch.float32))

        # Map raw action into the environment's action bounds
        a_env = ppo.ac.pi.raw_action_to_env_action(a_raw)

        # Step the env
        o2, r, d_env, _ = env.step(a_env)
        ep_ret += r
        ep_len += 1

        for reward, reward_name in zip(env.rewards, env.reward_names):
            
            #print("reward ", reward_name, " value ", reward.value)
            
            episode_rewards[reward_name].append(reward.reward)
            episode_values[reward_name].append(reward.value)
        
        env.camera.look_at(env.agent.body.get_position());
            
        sim_images.append(env.render(mode="rgb_array"))
        
        # Ignore the "done" signal if it comes from hitting the time
        # horizon (that is, when it's an artificial terminal signal
        # that isn't based on the agent's state)
        #d = False if ep_len==max_ep_len else d
    
        # Super critical, easy to overlook step: make sure to update 
        # most recent observation!
        o = o2
        
    
    save_frames_as_gif(sim_images, filename=sim_file + ".gif") 
    
    plot_labels = list(episode_rewards.keys())
    
    plot_x = np.arange(len(episode_values["alive"]))
    plot_rewards_y = np.array(list(episode_rewards.values()))
    plot_rewards_y = plot_rewards_y[:, :-1] # drop last reward
    plot_values_y = np.array(list(episode_values.values()))
    plot_values_y = plot_values_y[:, :-1] # drop last value
    
    reward_images = PlotUtils.create_plot_anim(plot_x, plot_rewards_y, plot_labels, 15, 5)
    save_images_as_gif(reward_images, filename=reward_file + ".gif") 
    #reward_images[0].save(reward_file + ".gif", save_all=True, append_images=reward_images[1:])
    PlotUtils.save_data_as_csv(plot_rewards_y, plot_labels, reward_file + ".csv")
    
    value_images = PlotUtils.create_plot_anim(plot_x, plot_values_y, plot_labels, 15, 5)
    save_images_as_gif(value_images, filename=value_file + ".gif") 
    #value_images[0].save(value_file + ".gif", save_all=True, append_images=value_images[1:])
    PlotUtils.save_data_as_csv(plot_values_y, plot_labels, value_file + ".csv")


# create PPO Model
ppo = PPO(env_observation_limits, env_action_limits, steps_per_epoch, target_kl=target_kl)

# Create one buffer per parallel environment
steps_per_env = steps_per_epoch // num_envs
ppo_buffers = [PPO_RolloutBuffer(len(env_observation_limits), len(env_action_limits), steps_per_env) for _ in range(num_envs)]

# load model weights
if load_model_weights:
    ppo.load_weights(result_file_path, load_epoch)


def train_agent_vectorized(epochs, steps_per_env):
    episode_counter = 0
    ep_reward_list = []
    
    # Get reward names from the first environment clone
    reward_names = envs.envs[0].reward_names
    num_rewards = len(reward_names)
    
    # Initialize history dictionary exactly like the non-vectorized version
    reward_history = {
        "length": [],
        "total": [],
        "avg": []
    }
    for name in reward_names:
        reward_history[name] = []
    
    # Initialize parallel environments trackers
    reset_result = envs.reset()
    if isinstance(reset_result, tuple) and len(reset_result) == 2:
        o, reset_info = reset_result
    else:
        o = reset_result

    ep_ret = np.zeros(num_envs)
    ep_len = np.zeros(num_envs)
    
    # Create a 2D array to track specific reward components for EACH environment 
    # Shape: (4 environments, N reward types)
    ep_reward_components = np.zeros((num_envs, num_rewards))

    for epoch in range(epochs):

        epoch_ep_rets = []
        epoch_ep_lens = []

        start = time.time()

        for t in range(steps_per_env):
            # 1. PPO Action Selection (Batched across all envs)
            a_raw, v, logp = ppo.ac.step(torch.as_tensor(o, dtype=torch.float32))
            
            # Map raw actions to environment bounds
            a_squashed = 1.0 / (1.0 + np.exp(-a_raw))
            act_limit_range = env_action_limits[:, 1] - env_action_limits[:, 0]
            act_limit_low = env_action_limits[:, 0]
            a_env = act_limit_low + act_limit_range * a_squashed
            
            # 2. Step all environments simultaneously
            step_result = envs.step(a_env)

            if len(step_result) == 5:
                o2, r, terminated, truncated, infos = step_result
                d_env = np.logical_or(terminated, truncated)
            else:
                o2, r, d_env, infos = step_result
                        
            ep_ret += r
            ep_len += 1

            # Accumulate individual reward components for each environment
            for i in range(num_envs):
                for rI, reward_obj in enumerate(envs.envs[i].rewards):
                    ep_reward_components[i, rI] += reward_obj.reward

            for i in range(num_envs):
                # Custom Target Logic for specific environment
                if target_reset_when_agent_close:
                    agent_pos = Utils.average_body_position(envs.envs[i].agent_obj)
                    target_pos = Utils.average_body_position(envs.envs[i].target_obj)
                    target_dist = np.linalg.norm([target_pos[1] - agent_pos[1], target_pos[0] - agent_pos[0]])
                    
                    if target_dist < target_reset_agent_max_distance:
                        randomise_target_pos(i)
                
                # Store experience in specific env's buffer
                ppo_buffers[i].store(o[i], a_raw[i], r[i], v[i], logp[i])
                
                timeout = (ep_len[i] == max_ep_len)
                terminal = d_env[i]
                
                if terminal or timeout:
                    if timeout and not terminal:
                        _, last_val, _ = ppo.ac.step(torch.as_tensor(o2[i], dtype=torch.float32))
                    else:
                        last_val = 0.0

                    ppo_buffers[i].finish_path(last_val)

                    episode_counter += 1
                    ep_reward_list.append(ep_ret[i])
                    avg_reward = np.mean(ep_reward_list[-40:])

                    reward_history["length"].append(ep_len[i])
                    reward_history["total"].append(ep_ret[i])
                    reward_history["avg"].append(avg_reward)
                    for rI, name in enumerate(reward_names):
                        reward_history[name].append(ep_reward_components[i, rI])

                    # IMPORTANT: explicitly reset this finished environment
                    randomise_target_pos(i)
                    reset_out = envs.envs[i].reset()
                    if isinstance(reset_out, tuple):
                        o2[i] = reset_out[0]
                    else:
                        o2[i] = reset_out

                    ep_ret[i] = 0.0
                    ep_len[i] = 0.0
                    ep_reward_components[i] = 0.0

            o = o2
            
        # 3. End of Epoch Handling
        # Bootstrap any trajectories cut off by the epoch ending
        for i in range(num_envs):
            _, last_val, _ = ppo.ac.step(torch.as_tensor(o[i], dtype=torch.float32))
            ppo_buffers[i].finish_path(last_val)
            
        # Merge all buffers into one large dictionary of tensors
        merged_data = {}
        for buf in ppo_buffers:
            data = buf.get() # .get() automatically resets the buffer pointers
            for k, val in data.items():
                if k not in merged_data: merged_data[k] = []
                merged_data[k].append(val)
                
        for k in merged_data:
            merged_data[k] = torch.cat(merged_data[k], dim=0)
            
        # Calculate and print averages for all environments
        avg_len = np.mean(epoch_ep_lens) if len(epoch_ep_lens) > 0 else 0.0
        avg_ret = np.mean(epoch_ep_rets) if len(epoch_ep_rets) > 0 else 0.0
        global_avg = np.mean(ep_reward_list[-40:]) if len(ep_reward_list) > 0 else 0.0
        
        print(f"--- Epoch {epoch} Summary ---")
        print(f"Total Episodes: {episode_counter} | Epoch Avg Len: {avg_len:.1f} | Epoch Avg Ret: {avg_ret:.2f} | Global Avg Ret: {global_avg:.2f} | Time: {(time.time()-start):01.2f}")
        # batching seems to prevent proper training, so I've taken it out for the moment
        #ppo.update(merged_data)
        ppo.update_batched(merged_data, batch_size=batch_size)
        
        # Save model weights based on user configs
        current_epoch = epoch + 1 + load_epoch
        if current_epoch % save_epoch_interval == 0:
            if save_model_weights:
                ppo.save_weights(result_file_path, current_epoch)

    return reward_history

# train agent
reward_history = train_agent_vectorized(epochs, steps_per_env)
PlotUtils.save_loss_as_csv(reward_history, result_file_path + "/reward_history_{}.csv".format(epochs))
ppo.save_weights(result_file_path, epoch=epochs)

"""
for export_index in range(10):
    export_episode(env, "{}/sim_{}_{}".format(result_file_path, epochs, export_index), "{}/reward_{}_{}".format(result_file_path, epochs, export_index), "{}/value_{}_{}".format(result_file_path, epochs, export_index))
"""

