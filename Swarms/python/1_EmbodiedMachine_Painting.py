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

pan_angle_max = 540
tilt_angle_max = 240
channel_count = 20
pan_channel = 1
tilt_channel = 3
white_channel = 10
shutter_channel = 12
intensity_channel = 13

flock_to_light_pos_scale = 100.0

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
light_base_positions = [np.array([0.0, -240, 30.0])]
#light_base_positions = [np.array([0.0, 0.0, 0.0])]
light_base_orientations = [np.array([0.0, 0.0])]
"""


bottom_light_count = 8
top_light_count = 8
light_count = bottom_light_count + top_light_count

bottom_ring_radius = 240.0 # in cm (for the small lights)
top_ring_radius = 140.0

bottom_light_tilt_offset = 0.0
bottom_light_pan_offset = 0.0

top_light_tilt_offset = 0.0
top_light_pan_offset = 0.0

bottom_light_pan_flip = -1.0
bottom_light_tilt_flip = -1.0

top_light_pan_flip = 0.0
top_light_tilt_flip = 0.0

bottom_ring_angle_increment = (np.pi * 2.0) / bottom_light_count
top_ring_angle_increment = (np.pi * 2.0) / top_light_count

bottom_ring_angle_start = -np.pi/2.0
top_ring_angle_start = -np.pi/2.0 - np.pi/8.0


# ring_angle_start = -np.pi/2.0 # same but with first light exactly at minus 90 degrees
#light_height = -10.0 # for the big light, 

bottom_light_height = -10
top_light_height = 500

bottom_light_base_tilt_angle = 0.0
top_light_base_tilt_angle = np.pi # totally untested

light_base_positions = []
light_base_orientations = []

# bottom ring
for light_nr in range(bottom_light_count):
    
  ringAngle = bottom_ring_angle_start + light_nr * bottom_ring_angle_increment
  
  #print("bottom lnr ", light_nr, " a ", ringAngle)

  posX = bottom_ring_radius * np.cos(ringAngle)
  posY = bottom_ring_radius * np.sin(ringAngle)
  posZ = bottom_light_height
  
  light_base_positions.append(np.array([posX, posY, posZ]))
  
  light_base_pan_angle = ringAngle + np.pi/2.0
  
  light_base_pan_angle = light_base_pan_angle * 180 / np.pi
  
  #print("nr ", light_nr, " a ", light_base_pan_angle)
  
  light_base_orientations.append(np.array([light_base_pan_angle, bottom_light_base_tilt_angle]))
  #light_base_orientations.append(np.array([0.0, 0.0]))
  
  #speakerOrientations[sI] = -posAngle;
  
  print("bottom lnr ", light_nr, " p ", light_base_positions[light_nr], " o ", light_base_orientations[light_nr])
  
# top ring
for light_nr in range(top_light_count):
    
  ringAngle = top_ring_angle_start + light_nr * top_ring_angle_increment
  
  #print("top lnr ", light_nr, " a ", ringAngle)

  posX = top_ring_radius * np.cos(ringAngle)
  posY = top_ring_radius * np.sin(ringAngle)
  posZ = top_light_height
  
  light_base_positions.append(np.array([posX, posY, posZ]))
  
  light_base_pan_angle = ringAngle + np.pi/2.0
  
  light_base_pan_angle = light_base_pan_angle * 180 / np.pi
  
  #print("nr ", light_nr, " a ", light_base_pan_angle)
  
  light_base_orientations.append(np.array([light_base_pan_angle, top_light_base_tilt_angle]))
  #light_base_orientations.append(np.array([0.0, 0.0]))
  
  #speakerOrientations[sI] = -posAngle;
  
  print("top lnr ", light_nr, " p ", light_base_positions[light_nr], " o ", light_base_orientations[light_nr])

# hacky offset for the big light at the position of light 2
#light_base_positions[2][0] += 20

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
        
        
x_pos_scale = 1.0
y_pos_scale = 1.0
z_pos_scale = -1.0
    
# translate swarm positions into light orientations and send result via OSC to Pablo
def osc_swarm_target_response(address, *args):

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
    for light_nr in range(bottom_light_count):
        
        if light_nr >= agent_count:
            break
        
        arg_index = light_nr * 3
        
        #target_pos = np.array([ args[arg_index], args[arg_index+1], args[arg_index+2] ])
        #target_pos = np.array([ -args[1], args[0], args[2] ])
        #target_pos = np.array([ args[1], args[0], -args[2] ])
        
        #target_pos = np.array([ args[arg_index + 1] * flock_to_light_pos_scale, -args[arg_index] * flock_to_light_pos_scale, -args[arg_index + 2] * flock_to_light_pos_scale ])
        target_pos = np.array( [x_pos_scale * args[arg_index  + 1] * flock_to_light_pos_scale, y_pos_scale * args[arg_index] * flock_to_light_pos_scale, z_pos_scale * args[arg_index + 2] * flock_to_light_pos_scale])
        
       # target_pos = np.array( [-args[arg_index  + 1] * flock_to_light_pos_scale, -args[arg_index] * flock_to_light_pos_scale, -args[arg_index + 2] * flock_to_light_pos_scale])
        
        # direction from light to target
        target_dir = target_pos - light_base_positions[light_nr]

        # normalize direction
        target_dir = target_dir / np.linalg.norm(target_dir)
        
        # calculate spherical coordinates in radians
        light_rot_radian = cart2spherical(target_dir)
        
        # convert radians to degrees
        light_rot_degrees = np.array([ light_rot_radian[0] * 180 / np.pi, light_rot_radian[1] * 180 / np.pi ])

        # convert form anticlockwise to clockwise rotation
        light_rot_degrees[0] *= bottom_light_pan_flip
        light_rot_degrees[1] *= bottom_light_tilt_flip
        
        # add light base orientation
        
        #print("lr ", light_nr, " bo ", light_base_orientations[light_nr])
        
        #print("lr ", light_nr, " r1 ", light_rot_degrees[0])
        
        light_rot_degrees += light_base_orientations[light_nr]
        
        #print("lr ", light_nr, " r2 ", light_rot_degrees[0])
        
        # apply angle offsets (probably unnecessary)
        light_rot_degrees[0] += bottom_light_pan_offset 
        light_rot_degrees[1] += bottom_light_tilt_offset
        
        #print("bottom ln ", light_nr, " p ", light_rot_degrees[0], " t ", light_rot_degrees[1])
        
        if light_rot_degrees[0] < 0.0:
            light_rot_degrees[0] += 180.0
        elif light_rot_degrees[0] > 180.0:
            light_rot_degrees[0] -= 180.0
            
        if light_rot_degrees[1] < 0.0:
            light_rot_degrees[1] += 180.0
        elif light_rot_degrees[1] > 180.0:
            light_rot_degrees[1] -= 180.0
            
        
        if dmx_light_control == True:
            set_pan_angle(light_nr, light_rot_degrees[0])
            set_tilt_angle(light_nr, light_rot_degrees[1])
        else:
            light_pans.append(light_rot_degrees[0])
            light_tilts.append(light_rot_degrees[1])
            
    """
    # dummy top light calculation
    light_rot_degrees = np.array([ 0.0, 0.0, 0.0 ])
    for light_nr in range(bottom_light_count, light_count):
        
        if dmx_light_control == True:
            set_pan_angle(light_nr, light_rot_degrees[0])
            set_tilt_angle(light_nr, light_rot_degrees[1])
        else:
            light_pans.append(light_rot_degrees[0])
            light_tilts.append(light_rot_degrees[1])
    """
    
    # top light calculations   
    for light_nr in range(bottom_light_count, light_count):
        
        if light_nr >= agent_count:
            break

        arg_index = light_nr * 3
        
        #target_pos = np.array([ args[arg_index], args[arg_index+1], args[arg_index+2] ])
        #target_pos = np.array([ -args[1], args[0], args[2] ])
        #target_pos = np.array([ args[1], args[0], -args[2] ])
        
        #target_pos = np.array([ args[arg_index + 1] * flock_to_light_pos_scale, -args[arg_index] * flock_to_light_pos_scale, -args[arg_index + 2] * flock_to_light_pos_scale ])
        
        target_pos = np.array( [-args[arg_index  + 1] * flock_to_light_pos_scale, -args[arg_index] * flock_to_light_pos_scale, -args[arg_index + 2] * flock_to_light_pos_scale])
        
        #print("ln ", light_nr, " tp ", target_pos)
        
        # direction from light to target
        target_dir = target_pos - light_base_positions[light_nr]

        # normalize direction
        target_dir = target_dir / np.linalg.norm(target_dir)
        
        # calculate spherical coordinates in radians
        light_rot_radian = cart2spherical(target_dir)
        
        # convert radians to degrees
        light_rot_degrees = np.array([ light_rot_radian[0] * 180 / np.pi, light_rot_radian[1] * 180 / np.pi ])

        # convert form anticlockwise to clockwise rotation
        light_rot_degrees[0] *= top_light_pan_flip
        light_rot_degrees[1] *= top_light_tilt_flip
        
        # add light base orientation
        
        #print("lr ", light_nr, " bo ", light_base_orientations[light_nr])
        
        #print("lr ", light_nr, " r1 ", light_rot_degrees[0])
        
        light_rot_degrees += light_base_orientations[light_nr]
        
        #print("lr ", light_nr, " r2 ", light_rot_degrees[0])
        
        # apply angle offsets (probably unnecessary)
        light_rot_degrees[0] += top_light_pan_offset 
        light_rot_degrees[1] += top_light_tilt_offset
        
        
        #print("top ln ", light_nr, " p ", light_rot_degrees[0], " t ", light_rot_degrees[1])
        
        if light_rot_degrees[0] < 0.0:
            light_rot_degrees[0] += 180.0
        elif light_rot_degrees[0] > 180.0:
            light_rot_degrees[0] -= 180.0
            
        if light_rot_degrees[1] < 0.0:
            light_rot_degrees[1] += 180.0
        elif light_rot_degrees[1] > 180.0:
            light_rot_degrees[1] -= 180.0
            
        
        #light_rot_degrees[0] = light_rot_degrees[0] % 360
        #light_rot_degrees[1] = light_rot_degrees[1] % 360
        
        if dmx_light_control == True:
            set_pan_angle(light_nr, light_rot_degrees[0])
            set_tilt_angle(light_nr, light_rot_degrees[1])
        else:
            light_pans.append(light_rot_degrees[0])
            light_tilts.append(light_rot_degrees[1])

    if dmx_light_control == True:
        dmx.submit()
    else:
        set_pan_angles_osc(0, light_count-1, light_pans)
        set_tilt_angles_osc(0, light_count-1, light_tilts)
    
# translate swarm velocities into light brightness and send result via DMX directly to lights
def osc_swarm_velocity_response(address, *args):

    global prev_time
    current_time = time.time()
    
    #print("ct ", current_time, " diff ", (current_time - prev_time), " inter ", min_dmx_update_interval)
    
    if (current_time - prev_time) < min_dmx_update_interval:
        return
    else:
        prev_time = current_time
        
    #print("send dmx")
    
    agent_count = len(args) // 3
    light_count = len(light_base_positions)
    
    for light_nr in range(light_count):
        
        if light_nr >= agent_count:
            break
        
        arg_index = light_nr * 3
        
        agent_velocity = np.array( [-args[arg_index  + 1] * flock_to_light_pos_scale, -args[arg_index] * flock_to_light_pos_scale, -args[arg_index + 2] * flock_to_light_pos_scale])
        agent_speed = np.linalg.norm(agent_velocity)
        
        #print("aI ", light_nr, " speed ", agent_speed)
        
        agent_norm_speed = (agent_speed - agent_speed_range[0]) / (agent_speed_range[1] - agent_speed_range[0])
        agent_norm_speed = max(min(agent_norm_speed, 1.0), 0.0)
        
        #set_intensity(light_nr, 1.0 - agent_norm_speed)
        set_intensity(light_nr, agent_norm_speed)

    dmx.submit()

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




"""
server.server_close()
"""

"""
light_base_orientations = np.array([90.0, 0.0])


target_dir = np.array([1.0, 0.0, 0.0])
        
# calculate spherical coordinates in radians
light_rot_radian = cart2spherical(target_dir)
        
# convert radians to degrees
light_rot_degrees = np.array([ light_rot_radian[0] * 180 / np.pi, light_rot_radian[1] * 180 / np.pi ])

# convert form anticlockwise to clockwise rotation
light_rot_degrees[0] *= -1.0
light_rot_degrees[1] *= -1.0

# TODO: compensate for light base orientation
light_rot_degrees[0] += light_base_orientations[0]
light_rot_degrees[1] += light_base_orientations[1]

# apply angle offsets
light_rot_degrees[0] += light_pan_offset 
light_rot_degrees[1] += light_tilt_offset
        
# send pan and tilt controls to light
set_pan_angle(light_nr, light_rot_degrees[0])
set_tilt_angle(light_nr, light_rot_degrees[1])
        

print("pan ", light_rot_degrees[0], " tilt ", light_rot_degrees[1])

"""





"""
brightness = 0.2
for light_nr in range(len(light_base_positions)):
    set_white(light_nr, brightness)
dmx.submit()
"""