
from importlib import import_module

ALL_MODULES = {
    'hello'
    , 'dump'
    , 'faildump'
    , 'groupadd'
    }

def load_module(module_name):
    '''
    Checks module_name against the declared names and dynamically
    loads the corresponding module.
    '''
    if module_name not in ALL_MODULES:
        raise ValueError('Invalid module name', module_name)
    return import_module('modules.'+module_name)

