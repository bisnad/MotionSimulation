"""
receive osc data from Expressive Aliens and convert them into message format resembling a single mocap skeleton
"""

import math
import numpy as np
import threading
import time

from pythonosc import dispatcher
from pythonosc import osc_server
from pythonosc.udp_client import SimpleUDPClient

alien_names = ["onshape", "onshape2", "onshape3", "onshape4"]
alien_joint_count = 6

osc_receive_ip = "127.0.0.1"
osc_receive_port = 9005

osc_send_ip = "127.0.0.1"
osc_send_port = 10000

osc_running = False

# combined alien joint positions array
alien_joint_positions = np.zeros([len(alien_names), alien_joint_count, 3], dtype=np.float32)

alien_joint_positions[0].shape

# combined alien joint rotations array
alien_joint_rotations = np.zeros([len(alien_names), alien_joint_count, 4], dtype=np.float32)

# update combined arrays
def update_combined_joint_positions( alien_name, joint_values ):
    
    alien_index = alien_names.index(alien_name)
    joint_positions = np.reshape(joint_values, (alien_joint_count, 3))

    # right to left handed coordinate system
    tmp = np.copy(joint_positions)
    joint_positions[:, 0] = tmp[:, 1]
    joint_positions[:, 1] = tmp[:, 0]
    joint_positions[:, 2] = tmp[:, 2]
    
    alien_joint_positions[alien_index] = joint_positions

def update_combined_joint_rotations( alien_name, joint_values ):
    
    alien_index = alien_names.index(alien_name)
    joint_rotations = np.reshape(joint_values, (alien_joint_count, 4))

    # right to left handed coordinate system and switch of w position in quaternion
    tmp = np.copy(joint_rotations)
    joint_rotations[:, 0] = tmp[:, 3]
    joint_rotations[:, 1] = tmp[:, 1]
    joint_rotations[:, 2] = tmp[:, 0]
    joint_rotations[:, 3] = tmp[:, 2]
    
    alien_joint_rotations[alien_index] = joint_rotations


"""
osc control
"""

def osc_start(addr):

    global osc_running

    if osc_running == False:
        
        print("osc_start")
        
        osc_running = True

def osc_stop(addr):
    
    global osc_running

    if osc_running == True:
        
        print("osc_stop")
        
        osc_running = False
        
def osc_quit(addr):

    osc_running = False
    server.server_close()

def alien_pos_osc_receive(addr, *args):
    
    if osc_running == False:
        return
    
    osc_address = addr
    osc_values = args
    
    alien_name = osc_values[0]
    alien_joint_values = np.asarray(osc_values[1:], dtype=np.float32)
    update_combined_joint_positions(alien_name, alien_joint_values)
  
def alien_rot_osc_receive(addr, *args):
    
    if osc_running == False:
        return
    
    osc_address = addr
    osc_values = args
    
    alien_name = osc_values[0]
    alien_joint_values = np.asarray(osc_values[1:], dtype=np.float32)
    update_combined_joint_rotations(alien_name, alien_joint_values)       
        
    # condition for sending combined joint positions and rotations
    if alien_name == alien_names[-1]:
        
        mocap_osc_send()
    
def mocap_osc_send():
    
    osc_pos_world = np.reshape(alien_joint_positions, (-1)).tolist()
    osc_rot_world = np.reshape(alien_joint_rotations, (-1)).tolist()
    
    osc_sender.send_message("/mocap/joint/pos_world", osc_pos_world) 
    osc_sender.send_message("/mocap/joint/rot_world", osc_rot_world) 


# osc send
osc_sender = SimpleUDPClient(osc_send_ip, osc_send_port)


# osc receive
osc_dispatcher = dispatcher.Dispatcher()
osc_dispatcher.map("/start", osc_start)
osc_dispatcher.map("/stop", osc_stop)
osc_dispatcher.map("/quit", osc_quit)
osc_dispatcher.map("/physics/joint/pos", alien_pos_osc_receive)
osc_dispatcher.map("/physics/joint/rot", alien_rot_osc_receive)

server = osc_server.ThreadingOSCUDPServer((osc_receive_ip, osc_receive_port), osc_dispatcher)

def start_server():
    server.serve_forever()

# Create a Thread with a function without any arguments
th = threading.Thread(target=start_server)
th.start()
