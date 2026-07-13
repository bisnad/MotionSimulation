
import numpy as np
import gym
from environments import quadruped_v1
env_name = "Quadruped-v1"

env = gym.make(env_name)
env.display = True
_ = env.reset()

#_ = env.render(mode="human")
_ = env.render(mode="rgb_array")

env_observation_space = env.observation_space
env_action_space = env.action_space

obs_dim = env_observation_space.shape[0]
act_dim = env_action_space.shape[0]

# Action limit for clamping: critically, assumes all dimensions share the same bound!

action_limit_high = env.action_space.high[0]
action_limit_low = env.action_space.low[0]

# debug
agent_joints = env.agent.body.active_joints
agent_joint_names = [ joint.joint_name  for joint in agent_joints ]
#action_joint_name = "RotZ_LArm2LHand"
action_joint_name = "shoulder3"
action_joint_index = agent_joint_names.index(action_joint_name)

action_joint = agent_joints[action_joint_index]
env.agent.power
action_joint.power_coeff

"""
while(True):
    action_joint.set_torque(np.random.uniform(action_limit_low, action_limit_high))
    env.physics.stepSimulation()
"""

"""
while(True):
    for joint in env.agent.body.active_joints:
        #joint.set_position(np.random.uniform(-1.0, 1.0))
        joint.set_torque(np.random.uniform(-2000.0, 2000.0))
    env.physics.stepSimulation()
"""


while(True):
    #test_action = np.zeros(shape=(act_dim), dtype=np.float32)
    #test_action[action_joint_index] = np.random.uniform(action_limit_low, action_limit_high)
    
    test_action = np.random.uniform(action_limit_low, action_limit_high, len(agent_joints))
    _, _, done, _ = env.step(test_action)
    
    if done:
        env.reset()


env.close()


"""
import numpy as np
import matplotlib.pyplot as plt
from simulation.environment import Environment
from simulation.walker_environment import WalkerEnvironment
from simulation.body_loader import BodyLoader
from simulation.thing import Thing
from simulation.agent import Agent
from simulation.walker_agent import WalkerAgent

env = WalkerEnvironment(display=True)

plane = Thing("plane", "models/plane/plane.urdf")
pillar = Thing("pillar", "models/pillar/pillar.urdf")
humanoid = WalkerAgent("humanoid", "models/humanoid/humanoid.urdf")
humanoid.set_feet_names(["RFoot1", "RFoot2", "LFoot1", "LFoot2"])


env.add_ground(plane)
env.add_target(pillar)
env.add_agent(humanoid)

_ = env.reset()

humanoid.body.deactivate_joint_collisions()
humanoid.body.reset_position([0.0, 0.0, 0.75])
humanoid.set_power(1.0)
pillar.body.reset_position([0.0, 8.0, 0.5])


env.camera.distance = 2.0
env.camera_adjust()
rgb = env.render(mode="rgb_array")

# plt.imshow(rgb)
# plt.axis("off")

action_space = humanoid.get_action_space()
state, reward, done, _ = env.step(np.random.uniform(action_space.low, action_space.high))

while(True):
    state, reward, done, _ = env.step(np.random.uniform(action_space.low * 0.1, action_space.high * 0.1))
    env.camera_adjust()
    rgb = env.render(mode="rgb_array")
    
    if done:
        env.reset()

env.close()
"""
