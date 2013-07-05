import os
from configobj import ConfigObj


configfile = os.path.join(os.path.dirname(__file__), 'server.cfg')
config = ConfigObj(configfile, interpolation=False, file_error=True)
