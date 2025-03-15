"""
Scene 1: Painting

Basic Target Position Tracking
Using Cartesion to Spherical Coordinate Conversion
based on: https://en.wikipedia.org/wiki/Spherical_coordinate_system

Lights point to agent positions
Light control data is not sent via DMX directly to the lights but via osc to Pablo
"""

"""
Maxi Lights 

Pan Range: 540
Tilt Range: 240

DMX Channels
Total Channels per Light: 20

1: Pan
3: Tilt
10: White Light
12: Shutter
13: Intensity
"""

import numpy as np
from DMXEnttecPro import Controller
from pythonosc import dispatcher
from pythonosc import osc_server
from pythonosc import udp_client
import threading
import asyncio
import time
from scipy.spatial.transform import Rotation


tilt_angle_min = -180
tilt_angle_max = 180

pan_angle_min = -270
pan_angle_max = 270


channel_count = 20
pan_channel = 1
tilt_channel = 3
white_channel = 10
shutter_channel = 12
intensity_channel = 13

flock_to_light_pos_scale = 100.0
flock_height_offset = 800.0

#debug_print = True
debug_print = False

#dmx_light_control = True
dmx_light_control = False

# osc setup
#osc_rec_address = "127.0.0.1"
#osc_rec_port = 9005

"""
# data from mocap analysis 
osc_rec_address = "127.0.0.1" 
osc_rec_port = 9004
"""

# data from flock
osc_rec_address = "127.0.0.1" 
osc_rec_port = 7500

#light control data to Pablo
#osc_light_send_address = "127.0.0.1"
#osc_light_send_port = 9014
osc_light_send_address = "2.0.0.31"
osc_light_send_port = 9005


def create_osc_sender(osc_address, osc_port):
    # start osc client
    sender = udp_client.SimpleUDPClient(osc_address, osc_port)
    
    return sender
  
osc_light_sender = create_osc_sender(osc_light_send_address, osc_light_send_port)

debug_print = False
#debug_print = True

# test dmx update interval with live mocap, mabe slower update intervals are better?
#min_dmx_update_interval = 0.02 #in seconds
min_dmx_update_interval = 0.04 #in seconds
#min_dmx_update_interval = 0.01 #in seconds
prev_time = time.time()

agent_speed_range = [0.0, 100.0]

"""
Light Settings
"""


grid_height = 500
grid_row_length= 180
grid_col_length = 180
grid_row_light_count = 4
grid_col_light_count = 4
light_base_tilt = 0.0
light_base_pan = 0.0

light_count = grid_row_light_count * grid_col_light_count

light_base_positions = []
light_base_orientations = []


light_nr = 0

for row in range(grid_row_light_count):
    for col in range(grid_col_light_count):
        
        #print("row ", row, " col ", col)

        posX = -grid_row_length / 2.0 + grid_row_length / (grid_row_light_count - 1) * col
        posY = -grid_col_length / 2.0 + grid_col_length / (grid_col_light_count - 1) * row
        posZ = grid_height

        rotPan = light_base_tilt
        rotTilt = light_base_pan

        light_base_positions.append(np.array([posX, posY, posZ]))
        light_base_orientations.append(np.array([rotPan, rotTilt]))

        print("light nr ", light_nr, " p ", light_base_positions[light_nr], " o ", light_base_orientations[light_nr])
        
        light_nr += 1

"""
>> OSC setup <<
"""

def create_osc_sender(osc_address, osc_port):
    # start osc client
    sender = udp_client.SimpleUDPClient(osc_address, osc_port)
    
    return sender

osc_light_sender = create_osc_sender(osc_light_send_address, osc_light_send_port)

"""
>> Light setup <<
"""

# Direct DMX Light Controls
dmx = None

if dmx_light_control == True:
    dmx = Controller('COM3', auto_submit=False)

# Cartesion to Polar Coordinates Conversion
def cart2spherical(vector):
    # normalize direction
    vector_norm = vector / np.linalg.norm(vector)
    
    # inclination
    elevation = np.arccos( vector_norm[2] )

    # azimuth
    azimuth = np.arctan2(vector_norm[1],vector_norm[0])
    
    return np.array([azimuth, elevation])


vector = np.array([1.0, 0.0, 0.])
print("dir ", vector, "angle ", cart2spherical(vector))

# Direct DMX Light Controls
def set_shutter(lightnr, value):
    dmx.set_channel(lightnr * channel_count + shutter_channel, int(value * 255))
    
def set_white(lightnr, value):
    dmx.set_channel(lightnr * channel_count + white_channel, int(value * 255))
    
def set_intensity(lightnr, value):
    dmx.set_channel(lightnr * channel_count + intensity_channel, int(value * 255))

def set_pan_angle(lightnr, value):
    dmx_value = int((value + pan_angle_max / 2) / pan_angle_max * 255)
    dmx_value = max(min(255, dmx_value), 0)
    
    if debug_print == True:
        print("lr ", lightnr, " pan v ", value, " d ", dmx_value)
    
    dmx.set_channel(lightnr * channel_count + pan_channel, dmx_value, submit_after=False)

def set_tilt_angle(lightnr, value):
    
    dmx_value = int((value + tilt_angle_max / 2) / tilt_angle_max * 255)
    dmx_value = max(min(255, dmx_value), 0)
    
    if debug_print == True:
        print("lr ", lightnr, " tilt v ", value, " d ", dmx_value)
    
    dmx.set_channel(lightnr * channel_count + tilt_channel, dmx_value, submit_after=False)
    
# Light Controls by send OSC to Pablo
def set_shutter_osc(light_nr, value):
    osc_value = value
    osc_light_sender.send_message("/light/" + str(light_nr)  + "/shutter", osc_value)

def set_shutters_osc(start_light_nr, end_light_nr, values):
    
    osc_values = []
    
    for light_nr in range(start_light_nr, end_light_nr+1):
        osc_values.append(values[light_nr])
    
    osc_light_sender.send_message("/light/" + str(start_light_nr) + "/" + str(end_light_nr) + "/shutter", osc_values)
   
def set_white_osc(light_nr, value):
    osc_value = value
    osc_light_sender.send_message("/light/" + str(light_nr)  + "/white", osc_value) 
   
def set_whites_osc(start_light_nr, end_light_nr, values):
    
    osc_values = []
    
    for light_nr in range(start_light_nr, end_light_nr+1):
        osc_values.append(values[light_nr])
    
    osc_light_sender.send_message("/light/" + str(start_light_nr) + "/" + str(end_light_nr) + "/white", osc_values)
    
def set_intensity_osc(light_nr, value):
    osc_value = value
    osc_light_sender.send_message("/light/" + str(light_nr) + "/intensity", osc_value)
    
def set_intensities_osc(start_light_nr, end_light_nr, values):
    
    osc_values = []
    
    for light_nr in range(start_light_nr, end_light_nr+1):
        osc_values.append(values[light_nr])
    
    osc_light_sender.send_message("/light/" + str(start_light_nr) + "/" + str(end_light_nr) + "/intensity", osc_values)
    
def set_pan_angle_osc(light_nr, value):
    dmx_value = int((value + pan_angle_max / 2) / pan_angle_max * 255)
    dmx_value = max(min(255, dmx_value), 0)
    osc_value = dmx_value/255
    
    osc_light_sender.send_message("/light/" + str(light_nr) + "/pan", osc_value)
    
def set_pan_angles_osc(start_light_nr, end_light_nr, values):
    
    osc_values = []
    
    for light_nr in range(start_light_nr, end_light_nr+1):
        dmx_value = int((values[light_nr] + pan_angle_max / 2) / pan_angle_max * 255)
        dmx_value = max(min(255, dmx_value), 0)
        osc_values.append(dmx_value/255)
    
    #print("set_pan_angle_osc")
    
    osc_light_sender.send_message("/light/" + str(start_light_nr) + "/" + str(end_light_nr) + "/pan", osc_values)

def set_pan_angles_norm_osc(start_light_nr, end_light_nr, values):
    
    osc_values = []
    
    for light_nr in range(start_light_nr, end_light_nr+1):
        osc_values.append(values[light_nr])
    
    #print("set_pan_angle_osc")
    
    osc_light_sender.send_message("/light/" + str(start_light_nr) + "/" + str(end_light_nr) + "/pan", osc_values)

def set_tilt_angle_osc(light_nr, value):
    dmx_value = int((value + tilt_angle_max / 2) / tilt_angle_max * 255)
    dmx_value = max(min(255, dmx_value), 0)
    osc_value = dmx_value/255

    osc_light_sender.send_message("/light/" + str(light_nr) + "/tilt", osc_value)
    
def set_tilt_angles_osc(start_light_nr, end_light_nr, values):
    
    osc_values = []
    
    for light_nr in range(start_light_nr, end_light_nr+1):
        dmx_value = int((values[light_nr] + tilt_angle_max / 2) / tilt_angle_max * 255)
        dmx_value = max(min(255, dmx_value), 0)
        osc_values.append(dmx_value/255)
        
    #print("set_tilt_angle_osc")
    
    osc_light_sender.send_message("/light/" + str(start_light_nr) + "/" + str(end_light_nr) + "/tilt", osc_values)
    
def set_tilt_angles_norm_osc(start_light_nr, end_light_nr, values):
    
    osc_values = []
    
    for light_nr in range(start_light_nr, end_light_nr+1):
        osc_values.append(values[light_nr])
        
    #print("set_tilt_angle_osc")
    
    osc_light_sender.send_message("/light/" + str(start_light_nr) + "/" + str(end_light_nr) + "/tilt", osc_values)
    
# open all shutters
if dmx_light_control == True:
    for light_nr in range(light_count):
        set_shutter(light_nr, 1.0)
        set_white(light_nr, 1.0)
        set_intensity(light_nr, 0.1)
    dmx.submit()
else:
    for light_nr in range(light_count):
        set_shutter_osc(light_nr, 1.0)
        set_white_osc(light_nr, 1.0)
        set_intensity_osc(light_nr, 0.1)
        

flock_pos_scale_x = 1.0
flock_pos_scale_y = 1.0
flock_pos_scale_z = -1.0

# this is in degrees
light_tilt_offset = 0.0
light_pan_offset = 0.0
light_tilt_flip = -1.0
light_pan_flip = 1.0

flip_block_active = True
#flip_block_active = False

debug_print = True
debug_print = False
debug_light_index = 7

"""
coordinates in light setup:
    left and right is x-coord: left: x decreases right: x increases
    front and back is y-coord:  back: y increaes front: y decreases
    up and down is z-coord: up: z increases, down: z decreases
    
coordinates swarm simulation: 
    left and right is y-coord: left: y incraeses right: y decreases
    front and back is x-coord:  back: x increases front: x decreases
    up and down is z-coord: up: z increases, down: z decreases
"""

prev_quat_w = [1.0] * light_count
    
# translate swarm positions into light orientations and send result via OSC to Pablo
def osc_swarm_target_response(address, *args):
    
    global prev_pan_angles

    global prev_time
    current_time = time.time()
    
    #print("ct ", current_time, " diff ", (current_time - prev_time), " inter ", min_dmx_update_interval)
    
    if (current_time - prev_time) < min_dmx_update_interval:
        return
    else:
        prev_time = current_time
        
    #print("send dmx")
    
    agent_count = len(args) // 3
    
    light_pans = []
    light_tilts = []
    
    # bottom light calculations
    for light_nr in range(light_count):
        
        if light_nr >= agent_count:
            break
        
        arg_index = light_nr * 3

        """
        get flock agent position
        """
        
        agent_pos = np.array( [args[arg_index], args[arg_index+1],args[arg_index + 2]])
        
        """
        get light position
        """
        
        light_pos = np.copy(light_base_positions[light_nr])
        
        """
        convert agent_pos to target position
        involves swapping x and y, and mirroring x
        """
        
        # scale agent pos to target pos
        target_pos = np.array([ agent_pos[1] * -1.0, agent_pos[0], agent_pos[2]])
        #target_pos = np.array([ agent_pos[0], agent_pos[1], agent_pos[2] ])
        target_pos[0] = target_pos[0] * flock_pos_scale_x * flock_to_light_pos_scale
        target_pos[1] = target_pos[1] * flock_pos_scale_y * flock_to_light_pos_scale
        target_pos[2] = target_pos[2] * flock_pos_scale_z * flock_to_light_pos_scale
        
        target_pos[2] += flock_height_offset
        
        if debug_print == True and light_nr == debug_light_index:
            print("1. target_pos ", target_pos, " light_pos ", light_pos)
        
        """
        # convert upside down setting with light at the top and dancer at the bottom
        # into setting with light at the bottom and dancer at the top
        """
            
        # flip horizontal
        target_pos[0] *= -1.0
        light_pos[0] *= -1.0
        
        # flip vertical
        #target_pos[2] = grid_height - target_pos[2]
        light_pos[2] = grid_height - light_pos[2]
        
        if debug_print == True and light_nr == debug_light_index:
            print("2. target_pos ", target_pos, " light_pos ", light_pos)
        
       # target_pos = np.array( [-args[arg_index  + 1] * flock_to_light_pos_scale, -args[arg_index] * flock_to_light_pos_scale, -args[arg_index + 2] * flock_to_light_pos_scale])
        
        # direction from light to target
        target_dir = target_pos - light_base_positions[light_nr]
        
        if debug_print == True and light_nr == debug_light_index:
            print("1. target_dir ", target_dir)

        # normalize direction
        target_dir = target_dir / np.linalg.norm(target_dir)
        
        if debug_print == True and light_nr == debug_light_index:
            print("2. target_dir ", target_dir)
        
        # calculate spherical coordinates in radians
        light_rot_radian = cart2spherical(target_dir)
        
        if debug_print == True and light_nr == debug_light_index:
            print("light_rot_radian ", light_rot_radian)
        
        # convert radians to degrees
        light_rot_degrees = np.array([ light_rot_radian[0] * 180 / np.pi, light_rot_radian[1] * 180 / np.pi ])
        
        if debug_print == True and light_nr == debug_light_index:
            print("1. light_rot_degrees ", light_rot_degrees)
        
        # convert form anticlockwise to clockwise rotation
        light_rot_degrees[0] *= light_pan_flip
        light_rot_degrees[1] *= light_tilt_flip
        
        if debug_print == True and light_nr == debug_light_index:
            print("2. light_rot_degrees ", light_rot_degrees)
        
        # apply angle offsets (probably unnecessary)
        light_rot_degrees[0] += light_pan_offset 
        light_rot_degrees[1] += light_tilt_offset
        
        if debug_print == True and light_nr == debug_light_index:
            print("3. light_rot_degrees ", light_rot_degrees)
            
 
        """ 
        avoid pan euler anglr discontinuities by converting pan rotation to quaternion
        check if the W-component of the current quaternion has a flipped sign with regards to the previous quaternion
        of the sign is flipped, unflip it
        then convert quaternion back to euler angle
        """
        
        rot_euler1 = light_rot_degrees[0]
        rot_quat = Rotation.from_euler("x", rot_euler1, degrees=True).as_quat()
        
        if prev_quat_w[light_nr] < 0.0 and rot_quat[0] > 0.0:
            rot_quat[0] *= -1.0
        elif prev_quat_w[light_nr] > 0.0 and rot_quat[0] < 0.0:
            rot_quat[0] *= -1.0
            
        prev_quat_w[light_nr] = rot_quat[0]
        
        rot_euler2 = Rotation.from_quat(rot_quat).as_euler("xyz", degrees=True)  
            
        if flip_block_active == True:
            light_rot_degrees[0] = rot_euler2[0]
            
            if debug_print == True and light_nr == debug_light_index:
                print("rot_euler1 ", rot_euler1, " rot_quat ", rot_quat, " rot_euler2 ", rot_euler2)
 

        if debug_print == True and light_nr == debug_light_index:
            print("3. light_rot_degrees ", light_rot_degrees, " prev_pan_angles[light_nr] ", prev_pan_angles[light_nr])

        
        if debug_print == True and light_nr == debug_light_index:
            print("4. light_rot_degrees ", light_rot_degrees)
        
        # convert degrees to norm
        light_rot_norm = np.array([(light_rot_degrees[0] - pan_angle_min) / (pan_angle_max - pan_angle_min), (light_rot_degrees[1] - tilt_angle_min) / (tilt_angle_max - tilt_angle_min)])
        
        if debug_print == True and light_nr == debug_light_index:
            print("light_rot_norm ", light_rot_norm)

        
        # add light base orientation

        #print("bottom ln ", light_nr, " p ", light_rot_degrees[0], " t ", light_rot_degrees[1])

        light_pans.append(light_rot_norm[0])
        light_tilts.append(light_rot_norm[1])
        
    set_pan_angles_norm_osc(0, light_count-1, light_pans)
    set_tilt_angles_norm_osc(0, light_count-1, light_tilts)


osc_handler = dispatcher.Dispatcher()

#osc_handler.map("/target/pos", osc_target_response)

# data from mocap analysis
#osc_handler.map("/mocap/joint/pos", osc_target_response)

# data from flock
osc_handler.map("/swarm/0/15/position", osc_swarm_target_response)

server = osc_server.ThreadingOSCUDPServer((osc_rec_address, osc_rec_port), osc_handler)

def start_osc_receive():
    server.serve_forever()
    
osc_thread = threading.Thread(target=start_osc_receive)

osc_thread.start()

