""" This module invoke amber loader.

    Copyright (C) 2008 ~ 2012. All Rights Reserved.
    The contents of this file are subject to the Mozilla Public License
    Version 1.1 (the "License"); you may not use this file except in
    compliance with the License. You may obtain a copy of the License at
    http://www.mozilla.org/MPL/

    Software distributed under the License is distributed on an "AS IS"
    basis, WITHOUT WARRANTY OF ANY KIND, either express or implied. See the
    License for the specific language governing rights and limitations
    under the License.

    Initial Developer: Lu Ken <bluewish.ken.lu@gmail.com>
"""     

__author__   = "Lu Ken <bluewish.ken.lu@gmail.com>"
__revision__ = "$Revision: $"

import sys
import os

#
# Get application path. There is difference between freeze version and source version.
#
if hasattr(sys, "frozen"):
    appPath = os.path.abspath(os.path.dirname(sys.executable))
else:
    appPath = os.path.abspath(os.path.dirname(__file__))
    
if __name__ == '__main__':
    """
    Invoke amber loader.
    """
    import amber.app
    amber.app.loadAmber(appPath)