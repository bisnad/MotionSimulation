"""
Classical walker environment with a target (fixed or moving) that a walker has to reach.
"""

import numpy as np
from simulation.environment import Environment

class WalkerEnvironment(Environment):
    def __init__(self, display=False):    
        super(WalkerEnvironment, self).__init__(display)

        self.ground = None
        self.target = None
        self.agent_potential = 0.0

        # costs for reward function
        self.alive_reward = 1.0 # reward for each step where the agent is alife 
        self.not_alive_cost = -10.0 # cost or agent no longer being alive 
        self.electricity_cost = -2.0	 # cost for using motors -- this parameter should be carefully tuned against reward for making progress, other values less improtant
        self.stall_torque_cost = -0.1  # cost for running electric current through a motor even at zero rotational speed, small
        self.foot_collision_cost = -1.0	# touches another leg, or other objects, that cost makes robot avoid smashing feet into itself
        self.joints_at_limit_cost = -0.1	 # discourage stuck joints
    
    def add_ground(self, ground):
        self.ground = ground
        self.add_thing(ground)
        
    def add_target(self, target):
        self.target = target
        self.add_thing(target)
        
    def reset(self):
        _ = super(WalkerEnvironment, self).reset()
        agent_state = self.agent.calc_state(self.ground, self.target)
        self.agent_potential = self.agent.walk_target_dist / (self.sim_time_step * self.sim_sub_steps)
        
        return agent_state

    def step(self, action):
        self.agent.apply_action(action)
        
        if self.sim_has_drag == True:
            self.apply_drag()
        
        self.physics.stepSimulation()
        
        agent_state = self.agent.calc_state(self.ground, self.target)
        
        # alive based on robot 
        agent_alive = self.agent.get_alive(self.ground)
        
        # episode ends if agent is not alive or some states values are infinite
        if agent_alive < 0:
            self.episode_done = True
            agent_alive = self.not_alive_cost
        else:
            self.episode_done = False
            agent_alive = self.alive_reward
    
        if not np.isfinite(agent_state).all():
            print("~INF~", agent_state)
            self.episode_done = True
        
        # potential
        potential_old = self.agent_potential
        self.agent_potential = self.agent.walk_target_dist / (self.sim_time_step * self.sim_sub_steps)
        #progress = float(self.agent_potential - potential_old)
        progress = float(potential_old - self.agent_potential)
        #progress *= 10.0

        # calculate feet collision costs (of the feet touch something else than the ground)
        collision_cost = 0.0
        ground_body_id = self.ground.body.id
        for foot in self.agent.feet:
            for contact in foot.get_contacts():
                contact_body_id = contact[2]
                if contact_body_id != ground_body_id:
                    collision_cost += self.foot_collision_cost
        
        # calculate electricity costs
        electricity_cost = self.electricity_cost * float(np.abs(action*self.agent.joint_speeds).mean())  # let's assume we have DC motor with controller, and reverse current braking
        electricity_cost += self.stall_torque_cost * float(np.square(action).mean())
        
        # calculate joint limit costs
        joints_at_limit_cost = float(self.joints_at_limit_cost * self.agent.joints_at_limit)
        
        #print("agent_alive", agent_alive)
        
        debugmode = 0
        if debugmode:
            print("alive=")
            print(agent_alive)
            print("progress")
            print(progress)
            print("electricity_cost")
            print(electricity_cost)
            print("joints_at_limit_cost")
            print(joints_at_limit_cost)
            print("feet_collision_cost")
            print(collision_cost)

        self.rewards = [
            agent_alive,
            progress,
            electricity_cost,
            joints_at_limit_cost,
            collision_cost
        ]
        
        if debugmode:
            print("rewards=")
            print(self.rewards)
            print("sum rewards")
            print(sum(self.rewards))
            
        self.episode_reward += sum(self.rewards)
        
        return agent_state, sum(self.rewards), bool(self.episode_done), {}
    
    def camera_adjust(self):
        agent_position = self.agent.body.get_position()
        self.camera.look_at(agent_position)
