"""
The __init__.py files specify that a directory is a Python package, 
and are run when the package is imported
"""

from gym.envs.registration import register

register(
    id='Custom_Environment',
    entry_point='custom.envs:CustomEnvironment'
)