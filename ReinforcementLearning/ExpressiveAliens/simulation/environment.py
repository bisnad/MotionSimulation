import numpy as np
import pybullet
from pybullet_utils import bullet_client
import gym, gym.spaces, gym.utils, gym.utils.seeding
from simulation.camera import Camera
from simulation.body_loader import BodyLoader

class Environment(gym.Env):
    
    metadata = {'render.modes': ['human', 'rgb_array']}
    
    def __init__(self, display=False):        
        self.display = display
        self.things = []
        #self.agents = [] # multi agents to do later once the single agent version fully works
        self.agent = None
        self.physics = None
        self.physics_state_id = None
        self.isRender = False
        self.sim_gravity = -9.8
        self.sim_has_drag = False
        
        self.sim_sub_steps = 20
        self.sim_time_step = 1.0 / (self.sim_sub_steps * 60)
        self.sim_solver_iterations = 50
        
        self.episode_done = False
        self.episode_reward = 0
        
        #self.action_space = None
        #self.observation_space = None
        
        #set action space and observation space to something arbitrary so the automated initiale env checking by gym doesn't fail
        self.action_space = gym.spaces.Box(-np.ones([1]), np.ones([1]))
        self.observation_space = gym.spaces.Box(-np.ones([1]), np.ones([1]))

    def add_thing(self, thing):
        self.things.append(thing)
    
    """
    def add_agent(self, agent):
        self.agents.append(agent)
    """
    
    def add_agent(self, agent):
        self.agent = agent
    
    def setGravity(self, gravity):
        self.gravity = gravity
        
    def setDisplay(self, display):
        self.display = display

    def reset(self):
        
        # create physics client and initialze camera if required
        if self.physics == None:
            if self.display:
                #self.physics = bullet_client.BulletClient(connection_mode=pybullet.GUI, options="--background_color_red=1.0 --background_color_green=1.0 --background_color_blue=1.0")
                self.physics = bullet_client.BulletClient(connection_mode=pybullet.GUI)
                self.camera = Camera(self.physics)
            else:
                self.physics = bullet_client.BulletClient()
            
            self.physics.resetSimulation()
            self.physics.setGravity(0, 0, -9.81)
            self.physics.setPhysicsEngineParameter(fixedTimeStep=self.sim_time_step * self.sim_sub_steps, numSolverIterations=self.sim_solver_iterations, numSubSteps=self.sim_sub_steps)
            
        # restore physics state
        # TODO: check if this is really necessary, after all, I'm reseting all things and agents afterwards
        if self.physics_state_id != None:
            self.physics.restoreState(self.physics_state_id)
            
        # reset things and agents
        for thing in self.things:
            if thing.physics == None:
                thing.physics = self.physics
            thing.reset()

        if self.agent.physics == None:
            self.agent.physics = self.physics
        self.agent.reset()
        
        self.action_space = self.agent.get_action_space()
        self.observation_space = self.agent.get_observation_space()

        # restart episode
        self.episode_done = False
        self.episode_reward = 0
    
        # collect agent state
        agent_state = self.agent.calc_state()
            
        # save physics state
        if self.physics_state_id == None:
            self.physics_state_id=self.physics.saveState()
        
        #return agent_state
        return agent_state
    
    def seed(self, seed=None):
        self.np_random, seed = gym.utils.seeding.np_random(seed)
        return [seed]

    def _get_observation(self):
        ob = np.array([0.0, 0.0])
        return ob
    
    def step(self, action):
        # if multiplayer, action first applied to all robots
        # then global stepSimulation()
        # then agent_state() for all robots with the same actions
        
        self.agent.apply_action(action)
        self.physics.stepSimulation()
        
        agent_state = self.agent.calc_state()
        
        ob = agent_state
        reward = 0.0
        done = False
        return ob, reward, done, dict()
    
    def render(self, mode):
        
        if mode == "human":
            self.isRender = True
        if mode != "rgb_array" or self.camera == None:
            return np.array([])
        
        return self.camera.render()
    
    def close(self):
        self.physics.disconnect()