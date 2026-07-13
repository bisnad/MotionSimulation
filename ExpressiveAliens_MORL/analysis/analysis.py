import numpy as np
from scipy.spatial import ConvexHull

class Analysis:
    
    # return average joint position for each time step
    # needs testing
    @staticmethod
    def average_body_position(joint_positions):
        # joint_positions: time_steps, joint_count, joint_dim
        return np.mean(joint_positions, axis=1, keepdims=True)
    
    # return joint velocities
    # needs testing
    @staticmethod
    def joint_velocities(joint_positions):
        # joint_positions: time_steps, joint_count, joint_dim
        time_steps = joint_positions.shape[0]
        joint_count = joint_positions.shape[1]
        joint_dim = joint_positions.shape[2]
        
        joint_vel = np.zeros( shape=(time_steps, joint_count, joint_dim), dtype=np.float32)
        joint_vel[1:] = joint_positions[1:] - joint_positions[:-1]
        
        return joint_vel
    
    # return joint speeds
    @staticmethod
    def joint_speeds(joint_velocities):
        # joint_positions: time_steps, joint_count, joint_dim
        time_steps = joint_velocities.shape[0]
        joint_count = joint_velocities.shape[1]
        joint_dim = joint_velocities.shape[2]
        
        _velocities = np.reshape(joint_velocities, (-1, joint_dim))
        _speeds = np.linalg.norm(_velocities, axis=1)
        _speeds = np.reshape(_speeds, (time_steps, joint_count, 1))
        
        return _speeds
    
    # return difference between start and end positions
    # needs testing
    @staticmethod
    def distance_travelled(joint_positions):
        # joint_positions: time_steps, joint_count, joint_dim
        joint_count = joint_positions.shape[1]
        pos_diff = joint_positions[-1] - joint_positions[0]
        pos_dist = np.linalg.norm(pos_diff, axis=1)
        return np.reshape(pos_dist, (1, joint_count, 1))

    # sum all position changes regardless of direction
    # needs testing
    @staticmethod
    def cumulative_distance_travelled(joint_positions):
        # joint_positions: time_steps, joint_count, joint_dim
        time_steps = joint_positions.shape[0]
        joint_count = joint_positions.shape[1]
        cum_dist = np.zeros(shape=(joint_count), dtype=np.float32)
        
        for tI in range(time_steps - 1):
            pos_diff = joint_positions[tI+1] - joint_positions[tI]
            pos_dist = np.linalg.norm(pos_diff, axis=1)
            cum_dist += pos_dist
        return np.reshape(cum_dist, (1, joint_count, 1))
    
    # tested
    @staticmethod
    def area_travelled(joint_positions, root_joint_index=-1):
        time_steps = joint_positions.shape[0]
        joint_count = joint_positions.shape[1]
        joint_dim = joint_positions.shape[2]
        
        if root_joint_index > -1:
            joint_count = 1
            joint_positions = joint_positions[:,joint_dim,:]
         
        joint_positions = np.reshape(joint_positions, (time_steps * joint_count, joint_dim))
        joint_positions = joint_positions[:, :2] # only orizontal coordinates
        
        #print("joint_positions ", joint_positions)
    
        hull = ConvexHull(joint_positions)
        area = np.array([hull.volume], dtype=np.float)
        
        return np.reshape(area, (1, 1, 1))
    
    # needs testing
    @staticmethod
    def volume_travelled(joint_positions, root_joint_index=-1):
        time_steps = joint_positions.shape[0]
        joint_count = joint_positions.shape[1]
        joint_dim = joint_positions.shape[2]
        
        if root_joint_index > -1:
            joint_count = 1
            joint_positions = joint_positions[:,joint_dim,:]
        
        joint_positions = np.reshape(joint_positions, (time_steps * joint_count, joint_dim))
        
        hull = ConvexHull(joint_positions)  
        volume = np.array([hull.volume], dtype=np.float)
        
        return np.reshape(volume, (1, 1, 1))

    
    # returns the velocities of the fastest moving joint with the velocities of all other joints set to zero
    # also returns any array containing only the joint with the fastest velocities
    # needs testing
    @staticmethod
    def isolated_movement(joint_velocities):
        time_steps = joint_velocities.shape[0]
        joint_count = joint_velocities.shape[1]
        joint_dim = joint_velocities.shape[2]
        
        joint_speeds = np.linalg.norm(joint_velocities, axis=2)
        
        maxSpeedJointIndex = np.argmax(joint_speeds, axis=1)
        
        fastest_velocities_all_joints = np.zeros(shape=joint_velocities.shape, dtype=np.float32)
        fastest_velocities_one_joint = np.zeros(shape=(time_steps, 1, joint_dim), dtype=np.float32)
        
        for tI in range(time_steps):
            fastest_velocities_all_joints[tI, maxSpeedJointIndex[tI]] = joint_velocities[tI, maxSpeedJointIndex[tI]]
            fastest_velocities_one_joint[tI,0] = joint_velocities[tI, maxSpeedJointIndex[tI]]

        return fastest_velocities_all_joints, fastest_velocities_one_joint
    
    @staticmethod
    def kinetic_energy(joint_velocities, joint_masses):
        energy = joint_velocities * joint_velocities * joint_masses
        return energy
    
    @staticmethod
    def weight_effort(kinetic_energy):
        return np.max(kinetic_energy)
    
    @staticmethod
    def time_effort(joint_accelerations, joint_masses):
        time_steps = joint_accelerations.shape[0]
        joint_count = joint_accelerations.shape[1]
        joint_dim = joint_accelerations.shape[2]      
        
        #print("acc s ", joint_accelerations.shape)
        #print("acc ", joint_accelerations)
        
        #print("mass s ", joint_masses.shape)
        #print("mass ", joint_masses)
        
        scalar_accelerations = np.linalg.norm(joint_accelerations,axis=2)
        
        #print("sacc s ", scalar_accelerations.shape)
        #print("sacc ", scalar_accelerations)       
        
        effort = np.sum(scalar_accelerations, axis=0) / time_steps
        
        #print("effort 1 s ", effort.shape)
        #print("effort 1 ", effort)

        effort = joint_masses * effort
        
        #print("effort 2 s ", effort.shape)
        #print("effort 2 ", effort)

        
        effort = np.sum(effort)

        #print("effort 3 s ", effort.shape)
        #print("effort 3 ", effort)

        return effort
    
    @staticmethod
    def space_effort(joint_positions, joint_masses):
        time_steps = joint_positions.shape[0]
        joint_count = joint_positions.shape[1]
        joint_dim = joint_positions.shape[2]
        
        #print("pos s ", joint_positions.shape)
        #print("pos ", joint_positions)
        
        #print("mass s ", joint_masses.shape)
        #print("mass ", joint_masses)
        
        pos_diff = joint_positions[1:] - joint_positions[:-1]
        
        #print("pos_diff s ", pos_diff.shape)
        #print("pos_diff ", pos_diff)
        
        sum_mov_length = np.linalg.norm(pos_diff, axis=2)
        
        #print("sum_mov_length 1 s ", sum_mov_length.shape)
        #print("sum_mov_length 1 ", sum_mov_length)
        
        sum_mov_length = np.sum(sum_mov_length, axis=0)
        
        #print("sum_mov_length 2 s ", sum_mov_length.shape)
        #print("sum_mov_length 2 ", sum_mov_length)
        
        total_mov_length = joint_positions[-1] - joint_positions[0]
        
        #print("total_mov_length s ", total_mov_length.shape)
        #print("total_mov_length ", total_mov_length)
        
        total_mov_length = np.linalg.norm(total_mov_length, axis=1) 
        
        #print("total_mov_length s ", total_mov_length.shape)
        #print("total_mov_length ", total_mov_length)
        
        effort = sum_mov_length / (total_mov_length + 0.000001)
        
        #print("effort 1 s ", effort.shape)
        #print("effort 1 ", effort)
        
        effort = joint_masses * effort
        
        #print("effort 2 s ", effort.shape)
        #print("effort 2 ", effort)
        
        effort = np.sum(effort)

        #print("effort 3 s ", effort.shape)
        #print("effort 3 ", effort)

        return effort
        
    @staticmethod
    def flow_effort(joint_jerks, joint_masses):
        time_steps = joint_jerks.shape[0]
        joint_count = joint_jerks.shape[1]
        joint_dim = joint_jerks.shape[2]      
        
        #print("jk s ", joint_jerks.shape)
        #print("jk ", joint_jerks)
        
        #print("mass s ", joint_masses.shape)
        #print("mass ", joint_masses)
        
        scalar_jerks = np.linalg.norm(joint_jerks,axis=2)
        
        #print("sjk s ", scalar_jerks.shape)
        #print("sjk ", scalar_jerks)       
        
        effort = np.sum(scalar_jerks, axis=0) / time_steps
        
        #print("effort 1 s ", effort.shape)
        #print("effort 1 ", effort)

        effort = joint_masses * effort
        
        #print("effort 2 s ", effort.shape)
        #print("effort 2 ", effort)

        
        effort = np.sum(effort)

        #print("effort 3 s ", effort.shape)
        #print("effort 3 ", effort)

        return effort    