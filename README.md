# AI-Toolbox - Motion Simulation

The "Motion Simulation" category of the AI-Toolbox contains a collection of Python- and C++ based algorithms that simulate the behaviour of non-antropomorphic entities. Two tools employ a rigid-body dynamics physics engine to simulate the behaviour of articulated morphologies. One tool employs a flocking simulation to simulate the coordinated spatial motions of a collective of individuals. These tools have been specifically adapted for experimental applications in contemporary dance. One tool employs reinforcement learning to train the articulated morphologies on Laban Efforts. Another tool provides manually implemented behavioral algorithms for the articulated morphologies that mimic idiosyncratic movement qualities of Muriel Romero. The third tool combines two groups of flocks, one of which is directly associated with the joints of a motion captured performer while the other one responds to the first flock with varying degrees of autonomy. All tools generate motion data that is sent via OSC messages. Also all tools can be  controlled by receiving OSC messages. 

The following tools are available:

- [ArticulatedBodies](ArticulatedBodies)

  A C++ based rigid body dynamics simulation of non-antropomorphic articulated bodies that evoke in their behaviours idiosyncratic movement qualities of choreographer Muriel Romero. 

- [ExpressiveAliens](ExpressiveAliens)

  A Python-based combination of a rigid body dynamics simulation and a reinforcement learning algorithm to train non-antropomorphic articulated bodies on Laban Efforts.

- [Swarms](Swarms)

  A C++ based simulation for two flocks, one of which can be directly controlled by a motion captured performer while the other one exhibits varying degrees of autonomy
