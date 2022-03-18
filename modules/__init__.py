
'''
Common infrastructure for dynamic module execution. All
interaction with the module system takes place inside
the load_module function, which is currently only used
here. All interaction so far happens via run_module,
which loads and runs modules both for one-shot and
server invocations. The instr argument is used by
the server to pass along request data; when instr is
None, the modules will typically try to read from stdin.
'''

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
    return import_module('.' + module_name, 'modules')

async def run_module(logger, secrets, args, instr, module_name):
    '''
    Dynamically loads and runs the specified module. If the
    instr parameter is not given, the module's main function
    will typically attempt to read stdin instead.
    '''
    mlogger = logger.getChild(module_name)
    mlogger.info('Loading module')
    module = load_module(module_name)
    mlogger.info('Loading successful, running module')
    return await module.main(mlogger, secrets, args, instr)


