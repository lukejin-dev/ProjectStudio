""" setup.py for window platform based on py2exe. 
    py2exe get better performance than cxfreeze under windows platform.
    
    Author : Lu, Ken (tech.ken.lu@gmail.com)
"""

from cx_Freeze import setup, Executable
import sys, glob
import os
base = None
if sys.platform == "win32":
    base = "Win32GUI"

def getDataFiles():
    files = []
    files.append(('img', glob.glob('img/*.*')))
    files.append(('locale', glob.glob('locale/*.*')))
    files.append(('plugins', glob.glob('plugins/*.*')))
    for item in getLocaleFiles():
        files.append(item)
    for item in getPluginFiles():
        files.append(item)
    return files
            
def getLocaleFiles():
    list = []
    for root, dirs, files in os.walk("locale"):
        for dir in dirs:
            if dir.lower() in [".svn", "_svn", "cvs"]:
                dirs.remove(dir)
                continue
        for dir in dirs:
            rpath = '%s/%s' % (root, dir)
            list.append((rpath, glob.glob('%s/*.mo' % rpath)))
    
    return list       
                
def getPluginFiles():
    list = []
    for root, dirs, files in os.walk("plugins"):
        for dir in dirs:
            if dir.lower() in [".svn", "_svn", "cvs"]:
                dirs.remove(dir)
                continue
        for dir in dirs:
            rpath = '%s/%s' % (root, dir)
            list.append((rpath, glob.glob('%s/*.py' % rpath)))
            list.append((rpath, glob.glob('%s/*.xml' % rpath)))
            list.append((rpath, glob.glob('%s/*.html' % rpath)))
            list.append((rpath, glob.glob('%s/*.ico' % rpath)))
    
    return list       

setup (name         = "ProjectEditor",
       version      = "0.2",
       description  = "Project Editor",
       data_files   = getDataFiles(),
       options      = {"build_exe": {"compressed" : True,
                                     "optimize"   : 2,
                                     "append_script_to_exe": True,
                                     "create_shared_zip": False}
                      },
       executables  = [Executable (script                = "loader.py", 
                                   base                  = base,
                                   appendScriptToLibrary = False,
                                   icon                  = 'img/app_32.ico',
                                   targetName            = "ProjectEditor.exe")])    