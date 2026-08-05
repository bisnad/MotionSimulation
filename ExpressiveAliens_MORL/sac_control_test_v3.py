"""
this goes along with sac_control_train_v3.py
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
import matplotlib.pyplot as plt
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
from custom.rewards.move_to_target_reward import MoveToTargetReward
from custom.rewards.impulse_reward import ImpulseReward
from custom.rewards.weight_effort_reward import WeightEffortReward
from custom.rewards.time_effort_reward import TimeEffortReward
from custom.rewards.space_effort_reward import SpaceEffortReward
from custom.rewards.flow_effort_reward import FlowEffortReward
from custom.rewards.target_distance_reward import TargetDistanceReward
from custom.rewards.ground_contact_reward import GroundContactReward

# custom environment
from custom.envs.custom_environment import CustomEnvironment
env_name = "Custom_Environment"

"""
configuration
"""

result_file_path = "results/biped_control_sac_v2_run17_v3"

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

target_move_reward_threshold = 200
target_speed_increment = 0.0001
target_max_speed = 0.05

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
agent_joint_torque_cost = -0.5 
agent_joint_limit_cost = -0.2 
agent_joint_rotation_cost = -0.02 
agent_joint_force_cost = -0.02 
agent_joint_reward_scale = 0.0 

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

# move to target
agent_move_to_target_reward_scale = 1.0
agent_stay_at_target_reward_scale = 1.0

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

sac_pi_learning_rate = 1e-4
sac_q_learning_rate = 1e-4
sac_replay_size = int(1e6)
sac_hidden_sizes=(256, 256, 256)
sac_activation=nn.ReLU

"""
configuration: training/testing shared
"""

max_ep_len=800 
render = True

"""
configuration: load/save model weights amd replay buffer
"""

load_epoch = 0
load_model_weights = True
load_replay_buffer = True
save_epoch_interval = 100
save_model_weights = False
save_replay_buffer = False

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
    target_move_reward_threshold = target_config["target_move_reward_threshold"]
    target_speed_increment = target_config["target_speed_increment"]
    target_max_speed = target_config["target_max_speed"]

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
    
    agent_body_misalignment_cost = rewards_config["agent_body_misalignment_cost"]
    agent_body_misalignment_reward_scale = rewards_config["agent_body_misalignment_reward_scale"]
    
    agent_move_distance_reward_scale = rewards_config["agent_move_distance_reward_scale"]
    
    agent_move_to_target_reward_scale = rewards_config["agent_move_to_target_reward_scale"]
    agent_stay_at_target_reward_scale = rewards_config["agent_stay_at_target_reward_scale"]
    
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
    sac_pi_learning_rate = model_config["sac_pi_learning_rate"]
    sac_q_learning_rate = model_config["sac_q_learning_rate"]
    sac_replay_size = int(model_config["sac_replay_size"])
    sac_hidden_sizes= model_config["sac_hidden_sizes"]
    
    # training settings
    training_config = config_data["training"]
    max_ep_len = training_config["max_ep_len"]
    
    # testing settings 
    testing_config = config_data["testing"]
    test_epoch = testing_config["test_epoch"]
    test_episode_count = testing_config["test_episode_count"]
    load_epoch = test_epoch
    epochs = load_epoch


# initialize random number generators
seed = 0
torch.manual_seed(seed)
np.random.seed(seed)


# create environments
env = gym.make(env_name)

# load agent and ground
ground = Thing("plane", "3d_models/plane2/plane.urdf")
target = Thing("target", "3d_models/pillar/pillar.urdf")
agent = CustomAgent("agent", agent_model_file_path)
agent.power = agent_power

# add agent and ground to environment
env.add_ground(ground)
env.add_target(target)
env.add_agent(agent)

# specify start position and orientation for agent
agent.set_reset_position(agent_reset_position)
agent.set_reset_orientation(agent_reset_orientation)

def randomise_target_pos():
    
    rand_azim = random.uniform(0.0, math.pi * 2.0)
    rand_dist = random.uniform(target_min_center_dist, target_max_center_dist)
    
    rand_x = rand_dist * math.cos(rand_azim)
    rand_y = rand_dist * math.sin(rand_azim)
    rand_z = 0.0
    
    target.body.set_position([rand_x, rand_y, rand_z])
    target.set_reset_position([rand_x, rand_y, rand_z])
    

# agent states
# relative orientations of joints
jointState = JointRelState()
agent.add_state(jointState, "joints")

# contact between feet and ground
groundContactState = GroundContactState()
groundContactState.part_names = agent_feet_names
agent.add_state(groundContactState, "groundContact")

# different in body height between episode start and end
heightDiffState = BodyInitialHeightDiffState()
agent.add_state(heightDiffState, "heightDiff")

# normalised body positions
bodyPosState = BodyPositionState()
bodyPosState.normalise = True
agent.add_state(bodyPosState, "bodyPos")

# body rotation
bodyRotState = BodyRotationState()
agent.add_state(bodyRotState, "bodyRot")

# body velocity
bodyVelState = BodyVelocityState()
agent.add_state(bodyVelState, "bodyVel")

# body target state (agent body angle to target state)
bodyTargetState = BodyTargetState()
agent.add_state(bodyTargetState, "bodyTarget")

# external control state - UPDATED TO 6 TO MATCH TRAINING
# 0: move_dist weight scale toggle
# 1: move_to_target weight scale toggle
# 2 - 5: effort target values (weight, time, space, flow)
controlState = CustomState()
controlState.state = np.array([0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=np.float32)
agent.add_state(controlState, "control")

# agent alive state
"""
# agent stops being alive when non feet in contact with ground
aliveState = GroundContactAliveState()
aliveState.feet_names = agent_feet_names
agent.add_alive_state(aliveState, "alive")
"""

# agent stops being alive when its root link moves too fast - RESTORED TO MATCH TRAINING
aliveState2 = MaxVelocityState()
aliveState2.max_linear_speed = 50.0  # Increased for stability
aliveState2.max_angular_speed = 200.0 # Increased for stability
agent.add_alive_state(aliveState2, "alive2")

# specify rewards

# rewards for training environment
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

moveToTargetReward = MoveToTargetReward()
moveToTargetReward.approach_scale = agent_move_to_target_reward_scale # FIXED TYPO HERE
moveToTargetReward.stillness_scale = agent_stay_at_target_reward_scale # FIXED TYPO HERE

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
env.add_reward(moveToTargetReward, "move_to_target")
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

# setup reinforcement learning model
env_observation_space = env.observation_space
env_action_space = env.action_space

env_observation_limits = np.stack([env_observation_space.low, env_observation_space.high], axis=1)
env_action_limits = np.stack([env_action_space.low, env_action_space.high], axis=1)

# reinforcement learning model
from learning.sac import SAC

num_objectives = len(env.rewards)

# create SAC Model with num_objectives
sac = SAC(env_observation_limits, env_action_limits, num_objectives, sac_replay_size, sac_hidden_sizes, sac_activation, sac_pi_learning_rate, sac_q_learning_rate)

# load model weights
if load_model_weights:
    sac.load_weights(result_file_path, load_epoch)

if load_replay_buffer:
    sac.load_replay_buffer(result_file_path, load_epoch)
    
def randomise_rewards():
    # 1. Handle Control State Values exactly as they are in train script
    moveDistanceReward.reward_scale = random.choice([0.0, 1.0])
    controlState.state[0] = moveDistanceReward.reward_scale

    moveToTargetReward.approach_scale = random.choice([0.0, 1.0])
    controlState.state[1] = moveToTargetReward.approach_scale

    weight_t = random.choice([0.0, 1.0])
    time_t = random.choice([0.0, 1.0])
    space_t = random.choice([0.0, 1.0])
    flow_t = random.choice([0.0, 1.0])

    weightEffortReward.target_value = weight_t
    timeEffortReward.target_value = time_t
    spaceEffortReward.target_value = space_t
    flowEffortReward.target_value = flow_t

    # Write targets directly to aligned controlState indices
    controlState.state[2] = weight_t
    controlState.state[3] = time_t
    controlState.state[4] = space_t
    controlState.state[5] = flow_t

    # 2. Sample continuous preference weights for the objectives (Dirichlet distribution)
    # Testing can use purely random Dirichlet, or you can hardcode this if you want to test specific efforts
    num_objectives = len(env.rewards)
    w = np.random.dirichlet(np.ones(num_objectives)).astype(np.float32)

    return w

# output gym render frames as gif
def save_frames_as_gif(frames, path='./', filename='gym_animation.gif'):

    plt.figure(figsize=(frames[0].shape[1] / 72.0, frames[0].shape[0] / 72.0), dpi=72)
    patch = plt.imshow(frames[0])
    plt.axis('off')

    def animate(i):
        patch.set_data(frames[i])

    anim = animation.FuncAnimation(plt.gcf(), animate, frames = len(frames), interval=50)
    anim.save(path + filename, writer='pillow', fps=60)

# output pillow images as gif
def save_images_as_gif(images, path='./', filename='gym_animation.gif'):

    plt.figure(figsize=(images[0].width / 72.0, images[0].height / 72.0), dpi=72)
    patch = plt.imshow(images[0])
    plt.axis('off')

    def animate(i):
        patch.set_data(images[i])

    anim = animation.FuncAnimation(plt.gcf(), animate, frames = len(images), interval=50)
    anim.save(path + filename, writer='pillow', fps=60)

def export_episode(env, sim_file, reward_file, value_file):
    
    episode_rewards = {}
    episode_values = {}
    episode_values_orig = {}

    for reward_name in env.reward_names:
        episode_rewards[reward_name] = []
        episode_values[reward_name] = []
        episode_values_orig[reward_name] = []

    sim_images = []
    randomise_target_pos()
    
    # Initialize preference weights w
    w = randomise_rewards()
    o, d, ep_ret, ep_len = env.reset(), False, 0, 0

    target_velocity = np.array([0.0, 0.0])
    base_target_speed = target_max_speed 

    while not(d or (ep_len == max_ep_len)):

        # Use the learned policy deterministically for evaluation. Pass w to get_action!
        a = sac.get_action(np.expand_dims(o, 0), np.expand_dims(w, 0), deterministic=True)
        a = np.squeeze(a, 0)

        # Step the env (r_vec is now an array)
        o2, r_vec, d, _ = env.step(a)
        
        # Calculate scalarized reward for printing/logging
        r_scalar = np.dot(r_vec, w)
        ep_ret += r_scalar
        ep_len += 1

        for reward, reward_name in zip(env.rewards, env.reward_names):
            episode_rewards[reward_name].append(reward.reward)
            episode_values[reward_name].append(reward.value)
            # Make sure all reward scripts actually have orig_value initialized for this to work
            if hasattr(reward, 'orig_value'):
                episode_values_orig[reward_name].append(reward.orig_value)
            else:
                episode_values_orig[reward_name].append(reward.value)

        # Update target position continuously
        if base_target_speed > 0:
            if random.random() < 0.02 or np.linalg.norm(target_velocity) == 0:
                rand_angle = random.uniform(0, 2 * math.pi)
                target_velocity = np.array([math.cos(rand_angle), math.sin(rand_angle)]) * base_target_speed

            current_target_pos = target.body.get_position()
            new_x = current_target_pos[0] + target_velocity[0]
            new_y = current_target_pos[1] + target_velocity[1]

            if np.linalg.norm([new_x, new_y]) > target_max_center_dist:
                target_velocity = -target_velocity 
                new_x = current_target_pos[0] + target_velocity[0]
                new_y = current_target_pos[1] + target_velocity[1]

            target.body.set_position([new_x, new_y, current_target_pos[2]])

        env.camera.look_at(env.agent.body.get_position())
        sim_images.append(env.render(mode="rgb_array"))
        
        o = o2

    save_frames_as_gif(sim_images, filename=sim_file + ".gif") 

    plot_labels = list(episode_rewards.keys())

    # Ensure plotting matches the lengths correctly
    plot_x = np.arange(len(episode_values["move_dist"]))
    plot_rewards_y = np.array(list(episode_rewards.values()))
    plot_rewards_y = plot_rewards_y[:, :-1]
    plot_values_y = np.array(list(episode_values.values()))
    plot_values_y = plot_values_y[:, :-1]
    plot_values_orig_y = np.array(list(episode_values_orig.values()))
    plot_values_orig_y = plot_values_orig_y[:, :-1]

    PlotUtils.save_data_as_csv(plot_rewards_y, plot_labels, reward_file + ".csv")
    PlotUtils.save_data_as_csv(plot_values_y, plot_labels, value_file + ".csv")
    PlotUtils.save_data_as_csv(plot_values_orig_y, plot_labels, value_file + "_orig.csv")

# Run export
for export_index in range(test_episode_count):
    export_episode(env, "{}/sim_{}_{}".format(result_file_path, epochs, export_index), "{}/reward_{}_{}".format(result_file_path, epochs, export_index), "{}/value_{}_{}".format(result_file_path, epochs, export_index))