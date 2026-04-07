"""
this trains an agent with constant values for dist and effort
dist in this case is not movement distance but distance between agent and a target
replaced te non-feet floor contact with a non-live ending negative reward
also, there is no conditional control for the agent
"""

import sys
import threading
import math
import random
import numpy as np
import torch
import torch.nn as nn
import pybullet
import gym
import time
from time import sleep
import json
import matplotlib
matplotlib.use('Agg') # Prevent flickering windows (Use the 'Agg' backend)
import matplotlib.pyplot as plt
from pythonosc import dispatcher
from pythonosc import osc_server
from pythonosc import udp_client

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

result_file_path = "results/biped_constant_ppo_run2"

"""
configuration frame rate
"""

frame_rate = 30.0

"""
configuration osc
"""

osc_rec_address = "127.0.0.1"
osc_rec_port = 9005

osc_send_address = "127.0.0.1"
osc_send_port = 9003

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
steps_per_epoch=5000
start_steps=5000 # number of initial steps when actions are taken randomly rather than from sac model
update_after=1000 # update step after which training of the sac model starts 
update_every=50 # once training started, number of steps after which training of model is repeated
max_ep_len=800 # Maximum length of trajectory / episode / rollout.

"""
configuration: visualization
"""
render = True

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

target_pos = np.array([0.0, 0.0, 0.0], dtype=np.float32)
target_pos_changed = True

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

# agent alive state
"""
# agent stops being alive when non feet in contact with ground
aliveState = GroundContactAliveState()
aliveState.feet_names = agent_feet_names
agent.add_alive_state(aliveState, "alive")
"""
# agent stops being alive when its root link moves too fast
aliveState2 = MaxVelocityState()
aliveState2.max_linear_speed = 10.0
aliveState2.max_angular_speed = 100.0
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

"""
osc setup
"""

# osc send

def create_osc_sender(osc_address, osc_port):
    # start osc client
    sender = udp_client.SimpleUDPClient(osc_address, osc_port)
    
    return sender

def send_joint_orientations(sender, frame):
    
    joint_orientations = []
    
    for joint in agent.body.ordered_joints:
        joint_orientations += [joint.get_orientation()]

    sender.send_message("/agent/joint/rot", joint_orientations)
    
def send_joint_positions(sender, frame):
    
    joint_positions = []
    
    for joint in agent.body.ordered_joints:
        joint_positions += [joint.get_position()]

    sender.send_message("/agent/joint/pos", joint_positions)

osc_sender = create_osc_sender(osc_send_address, osc_send_port)

# osc receive

def osc_set_target_position(address, pos_x, pos_y):
    
    global target_pos_changed

    #pos_x = args[0]
    #pos_y = args[1]
    pos_z = 0.0

    target_pos[0] = pos_x
    target_pos[1] = pos_y
    target_pos[2] = pos_z
    target_pos_changed = True
    

    #print("osc_set_target_position x ", pos_x, " y ", pos_y)

osc_handler = dispatcher.Dispatcher()
osc_handler.map("/target/position", osc_set_target_position)

osc_server = osc_server.ThreadingOSCUDPServer((osc_rec_address, osc_rec_port), osc_handler)

def osc_start_receive():
    osc_server.serve_forever()

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

env_observation_limits = np.stack( [env_observation_space.low, env_observation_space.high], axis=1)
env_action_limits = np.stack( [env_action_space.low, env_action_space.high], axis=1)

def randomise_target_pos():
    
    global target_pos
    global target_pos_changed
    
    rand_azim = random.uniform(0.0, math.pi * 2.0)
    rand_dist = random.uniform(target_min_center_dist, target_max_center_dist)
    
    rand_x = rand_dist * math.cos(rand_azim)
    rand_y = rand_dist * math.sin(rand_azim)
    rand_z = 0.0
    
    target_pos[0] = rand_x
    target_pos[1] = rand_y
    target_pos[2] = rand_z
    
    target_pos_changed = True
    
    #target.body.set_position([rand_x, rand_y, rand_z])
    #target.set_reset_position([rand_x, rand_y, rand_z])

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

def run_episode(env, osc_sender):
    
    global target_pos_changed
    
    o, ep_ret, ep_len = env.reset(), 0, 0
        
    while True: # never ending episode
    
        # osc communication
        send_joint_orientations(osc_sender, ep_len)
        send_joint_positions(osc_sender, ep_len)
    
        if target_pos_changed == True:
            
            target.body.set_position(target_pos)
            target.set_reset_position(target_pos)
            
            #print("target_pos ", target_pos)
            
            target_pos_changed = False
                                    

        # Sample raw PPO action, value, and log-probability
        a_raw, v, logp = ppo.ac.step(torch.as_tensor(o, dtype=torch.float32))

        # Map raw action into the environment's action bounds
        a_env = ppo.ac.pi.raw_action_to_env_action(a_raw)

        # Step the env
        o2, r, d_env, _ = env.step(a_env)
        ep_ret += r
        ep_len += 1
        
        env.camera.look_at(env.agent.body.get_position())
        env.render(mode="human")

        # Ignore the "done" signal if it comes from hitting the time
        # horizon (that is, when it's an artificial terminal signal
        # that isn't based on the agent's state)
        #d = False if ep_len==max_ep_len else d
    
        # Super critical, easy to overlook step: make sure to update 
        # most recent observation!
        o = o2
        
        sleep(1.0 / frame_rate)

# create PPO Model
ppo = PPO(env_observation_limits, env_action_limits, steps_per_epoch)
ppo_buffer = PPO_RolloutBuffer(len(env_observation_limits), len(env_action_limits), steps_per_epoch)

# load model weights
if load_model_weights:
    ppo.load_weights(result_file_path, load_epoch)

osc_thread = threading.Thread(target=osc_start_receive)
osc_thread.start()

while(True):
    run_episode(env, osc_sender)
    
osc_server.server_close()
