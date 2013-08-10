""" Setup scrpt for Amber Editor

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

#======================================  External Libraries ========================================
import sys
from cx_Freeze import setup, Executable

#============================================== Code ===============================================

DATA = ['*.py', 'images/*.*', 'lib/*.py', 'amber/*.py']

"""
setup(name = "amber_editor",
      description = "Amber editor for development",
      long_description = "Amber editor for development",
      version = "0.0.1",
      packages = ['amber'],
      package_dir={'amber':'src'},
      package_data={'amber':DATA},
      maintainer="Lu, Ken",
      maintainer_email="bluewish.ken.lu@gmail.com",
      url = "http://ambereditor.sourceforge.net",
      license = "MOZILLA PUBLIC LICENSE")
"""

base = None
if sys.platform == "win32":
    base = "Win32GUI"

executables = [Executable("EDES2008.pyw",
                          base=base,
                          icon="app_icon_new.ICO"
                          )]

buildOptions = dict(compressed = True,
                    optimize   = 2)
        
setup(name = "pis",
      description = "Project Insight Studio",
      version = "0.0.1",
      author = "Lu, Ken",
      author_email = "Lu, Ken",
      options = dict(build_exe = buildOptions),
      executables = executables)

""" 
Setup Options:
    help_commands:
    name:
    version:
    fullname:
    author:
    author_email:
    maintainer:
    contact:
    contact_email:
    url:
    license:
    description:
    long_description:
    platforms:
    keywords:
    provides:
    obsoletes:

"""
