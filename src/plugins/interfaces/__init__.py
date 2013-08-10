"""@package 
   
Lu, Ken (tech.ken.lu@gmail.com)
"""

import threading
import logging
from functools import update_wrapper
from types import *


"""Interface type/implementation class dictionary.
  
An interface type class is the class which inherited from Interface class directly.
An interface implement class is the class which inherited from interface type class.
For example: Interface -> IPlugin -> MyPlugin -> MyProjectPlugin
In above example, -> means inherit. IPlugin is interface type class.
And MyPlugin and MyProjectPlugin are all interface implement class.

Note: An interface object instance could only be created from an interface implementation class.
 
Key    : Interface type class
Value  : List of Interface implement class
"""
_ifclassdict   = {}
_classdictlock = threading.Lock()
 
"""The dictionary of object instance created from interface implement class.
  
Key    : Interface implement class
Value  : List of instance object which created from interface implement class.
"""
_ifobjdict = {}
_objdictlock = threading.Lock()


class InterfaceMeta(type):
    """IntefaceMeta class is the meta class for interface.
     
    This class hook the creation action to record all interface type class 
    and interface implementation class.
    """

    def __new__(cls, name, bases, dict):  
        # Allocate memory for class
        classtype = type.__new__(cls, name, bases, dict)
        
        # skip interface base class
        if name == "Interface":
            return classtype
        
        # if Interface is direct parent class, then this creating class is 
        # interface type class
        if Interface in bases: # if Inteface is direct parent class 
            _classdictlock.acquire()
            _ifclassdict[classtype] = []
            _classdictlock.release()
        else:
            # The Interface class is not direct parent, so the creating class
            # is implementation class
            for ifclass in _ifclassdict.keys():
                if issubclass(classtype, ifclass):
                    _classdictlock.acquire()
                    _ifclassdict[ifclass].append(classtype)
                    _classdictlock.release()
        return classtype
    
    def __init__(cls, name, bases, dict):
        # Initialize class
        super(InterfaceMeta, cls).__init__(name, bases, dict)

def getInterfaceTypeClass(cls):
    """Get interface type class according to interface implement class."""
    for ifclass in _ifclassdict.keys():
        if cls in _ifclassdict[ifclass]:
            return ifclass
    return None

def getInterfaceImplementClasses(ifclass):
    """Get interface implement class list according to given interface class"""
    if ifclass not in _ifclassdict.keys():
        return None
    return _ifclassdict[ifclass]

def interface(func):
    def _hookFunc(*args, **kwds):
        assert type(func) is FunctionType, "Invalid function type"
        assert len(args) > 0, "Invalid interface's method"
        
        ifobj = args[0]
        assert hasattr(ifobj, "__class__"), "Invalid interface object"
        
        impclass = ifobj.__class__
        typeclass = getInterfaceTypeClass(ifobj.__class__)
        assert typeclass is not None, "Invalid interface type class"
        
        raise InterfaceMissImplementError(impclass, typeclass, func)

    return update_wrapper(_hookFunc, func)
        
class Interface(object):
    __metaclass__ = InterfaceMeta
    _instances = {}
    def __new__(cls, *args, **kwds):
        typecls = getInterfaceTypeClass(cls)
        assert typecls != None, "Can not find interface type class for %s" % cls.__name__
        obj = object.__new__(cls)
        Interface._instances.setdefault(typecls, []).append(obj)
        return obj
    
    def __del__(self):
        typecls = getInterfaceTypeClass(self.__class__)
        assert typecls != None, "Can not find interface type class for %s" % self.__class__
        if self in Interface._instances[typecls]:
            Interface._instances[typecls].remove(self)

class InterfaceMissImplementError(Exception):
    def __init__(self, impclass, typeclass, func):
        self._message = "Interface implement class %s does not implement %s.%s" % \
                        (impclass, typeclass.__name__, func.__name__)
                        
    def __str__(self):
        return self._message
        
        
      
        