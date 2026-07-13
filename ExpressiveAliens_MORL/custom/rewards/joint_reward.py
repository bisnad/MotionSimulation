from custom.rewards.custom_reward import CustomReward
from simulation.utils import Utils
from analysis.analysis import Analysis
from common.ringbuffer import RingBuffer
import numpy as np

# specify rewards
class JointReward(CustomReward):
    
    def __init__(self):
        super().__init__()
        
        self.value = 0.0
        
        self.comfort_rotation_range = 0.7
        self.comfort_force_range = 5000
        self.max_force = 10000.0
        
        self.torque_cost = -0.5 # costs for applying torque to joint (exhaustion)
        self.limit_cost = -0.2 # costs for joint rotation close to limit (comfort)
        self.rotation_cost = -0.02 # costs for joint rotation outside of preferred range (comfort)
        self.force_cost = -0.02 # costs for forces applied to joints along their fixed digrees of freedom (comfort)
        self.reward_scale = 1.0 # 1.0
        
        self.value = 0.0
        self.value_reward_scale = 1.0 
        self.reward = 0.0 
        self.reward_scale = 1.0
        
        self.joint_names = []
        self.joints = []

        self.history_length = 50 # only used for joint torque (as a measure of exhaustion)
        self.torque_history = None
        
    
    def init(self):
        
        self.joints = Utils.get_agent_joints(self.env.agent, self.joint_names)
        joint_count = len(self.joints)
        self.torque_history  = RingBuffer(self.history_length, np.zeros(shape=(joint_count, 1), dtype=np.float32))
        
        super().init()
        
    def _find_joints(self):
        agent = self.env.agent  
        if len(self.joint_names) > 0: # gather feet based on part names
            self.joints = [ agent.body.body_joints[joint_name] for joint_name in self.joint_names ] 
        else: # gather all parts
            self.joints = agent.body.ordered_joints
        
    def reset(self):
        if self.torque_history != None:
            joint_count = len(self.joints)
            self.torque_history.clear(np.zeros(shape=(joint_count, 1) ,dtype=np.float32))
            
        super().reset()

    def calc_value(self):
        #print("weight effort")
        
        agent = self.env.agent
        joint_count = len(self.joints)
        
        joint_torques = []
        joint_forces = []
        joints_limits = []
        joints_rotations = []


        for joint in self.joints:
            x, _ = joint.get_relative_state()
            _, _, rf, t  = joint.get_full_state()
            
            # normalise torque
            joint_max_torque = joint.power_coeff * agent.power 
            t /= joint_max_torque
            t = min(t, 1.0)
            joint_torques.append(t)
            
            # normalise forces
            rf = np.max(rf)
            
            if rf > self.comfort_force_range:
                rf = (rf - self.comfort_force_range) / (self.max_force - self.comfort_force_range)
                rf = min(rf, 1.0)
            else:
                rf = 0.0
            joint_forces.append(rf)

            # joint rotation limit
            joints_limits.append(abs(x) > 0.99)
            
            #print("joint ", joint.joint_name, " rot ", x)
            
            # joint rotation comfort
            if abs(x) > self.comfort_rotation_range:
                joint_rotation = max((abs(x) - self.comfort_rotation_range) / (1.0 - self.comfort_rotation_range), 1.0)
                joints_rotations.append(joint_rotation)
            else:
                joints_rotations.append(0.0)
            
        joint_torques = np.expand_dims(np.array(joint_torques, dtype=np.float32), axis=1)
        joint_forces = np.array(joint_forces, dtype=np.float32)
        joint_limits = np.array(joints_limits, dtype=np.float32)
        joint_rotations = np.array(joints_rotations, dtype=np.float32)
        
        """
        print("joint_torques s ", joint_torques.shape)
        print("joint_forces s ", joint_forces.shape)
        print("joint_limits s ", joint_limits.shape)
        print("joint_rotations s ", joint_rotations.shape)
    
        print("joint_torques ", joint_torques)
        print("joint_forces ", joint_forces)
        print("joint_limits ", joint_limits)
        print("joint_rotations ", joint_rotations)
        """
        
        self.torque_history.write(joint_torques)
        joint_torques = self.torque_history.read(self.history_length)

        #print("joint_torques2 s ", joint_torques.shape)
        
        torque_cost = np.mean(joint_torques) * self.torque_cost
        force_cost = np.max(joint_forces) * self.force_cost
        limit_cost = np.mean(joint_limits) * self.limit_cost
        rotation_cost = np.mean(joint_rotations) * self.rotation_cost

        """
        print("torque_cost ", torque_cost)
        print("force_cost ", force_cost)
        print("limit_cost ", limit_cost)
        print("rotation_cost ", rotation_cost)
        """
        
        self.value = torque_cost + force_cost + limit_cost + rotation_cost
        
        #print("value ", self.value)
