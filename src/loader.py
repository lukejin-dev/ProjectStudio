""" Loader in debug version

    Lu, Ken (tech.ken.lu@gmail.com)
"""

import os, sys
import encodings.utf_8
    
#
# Get application path. There is difference between freeze version and source version.
#
if hasattr(sys, "frozen"):
    appPath = os.path.abspath(os.path.dirname(sys.executable))
else:
    appPath = os.path.abspath(os.path.dirname(__file__))

#
# Push plugin folder to sys.path
#
pluginPath = os.path.normpath(os.path.join(appPath, "plugins"))
if not os.path.exists(pluginPath):
    raise Exception, "plugins path does not exist under %s" % appPath
else:
    if pluginPath not in sys.path:
        sys.path.append(pluginPath)
        
#try:
#    import psyco
#    psyco.full
#except:
#    pass    
import ide.ps_app
ide.ps_app.startIDE(appPath)
