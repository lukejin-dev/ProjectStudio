"""
This module is the main entry of Project Insight Studio.

Project Insignt Studio is designed for managing project source code
and help developer to navigator source.

@summary: Main Entry of Project Insight Studio

"""

__author__ = "Lu, Ken <bluewish.ken.lu@gmail.com>"
__svnid__ = "$Id: $"
__revision__ = "$Revision: $"

import wx
import encodings
import encodings.ascii
import encodings.aliases
import encodings.cp437
import encodings.gbk
import encodings.utf_16
import encodings.utf_8
if wx.Platform == '__WXMSW__':
    import encodings.mbcs
    
import profile, pstats
import core.appmain

from version import *
from optparse import OptionParser
from core.debug import *

def StartPIS():
    """ Prepare and enter project insight studio.
    1) First thing is to process the command line  as following.
    Usage: PIS.py [options]
    
    Options:
      --version             show program's version number and exit
      -h, --help            show this help message and exit
      -p PROFILE_NAME, --profile=PROFILE_NAME
                            Specific profile file name for getting profiling
                            information
      -d VERBOSE, --debug=VERBOSE
                            Turn on debug message and specific debug level:
                            [DEBUG|INFO|WARNING|ERROR|CRITICAL]
      -l LOGFILE, --logfile=LOGFILE
                            Specific log file or server address to hold log
                            information under specific debug level.
      -s LOGSERVER, --logserver=LOGSERVER
                            Specific log server address to hold log information
                            under specific debug level.  
                            
    2) Initialize logging system as early as possible.
    3) Launch the PIS's core.  
    """
    #
    # Process command line firstly.
    #
    parser = OptionParser(version="%s - Version %s" % (PROJECT_NAME, VERSION))
    parser.add_option('-p', '--profile', action='store', 
                      type='string', dest='profile_name',
                      help='Specific profile file name for getting profiling information')
    parser.add_option('-d', '--debug', action='store', dest='verbose', default='DEBUG',
                      help='Turn on debug message and specific debug level: [DEBUG|INFO|WARNING|ERROR|CRITICAL]')
    parser.add_option('-l', '--logfile', action='store', dest='logfile',
                      help='Specific log file or server address to hold log information under specific debug level.')
    parser.add_option('-s', '--logserver', action='store', dest='logserver',
                      help='Specific log server address to hold log information under specific debug level.')
    
    (options, args) = parser.parse_args()
    
    if options.verbose not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
        parser.error("invalid value for -d options")
        sys.exist(0)

    # must specific the log file event no log file is given
    if options.logfile == None:
        logfile = os.path.join(os.path.dirname(sys.argv[0]), 'log.txt')
    else:
        logfile = options.logfile
        
    #
    # Enable the logging system.
    #
    core.debug.IniLogging(options.verbose, logfile, options.logserver)
    
    #
    # Start main entry, if want profiling, then profile the main entry.
    #
    if options.profile_name != None:
        # profiling PIS and display the result after finishing run()
        profile.run('core.appmain.main()', options.profile_name)
        stats = pstats.Stats(options.profile_name)
        stats.strip_dirs().sort_stats("time").print_stats(10)
    else:
        core.appmain.main()

if __name__ == '__main__':
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass
        
    StartPIS()
