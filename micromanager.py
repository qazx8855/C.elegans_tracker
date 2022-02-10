
from pycromanager import Bridge

bridge = Bridge()
core = bridge.get_core()

print(core.get_version_info())