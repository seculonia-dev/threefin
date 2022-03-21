
'''
Modules that understand HTTP requests.
'''

from importlib import import_module

ALL_MODULES = {
    'hello'
    , 'feed'
    }

def load_opt(module_name):
    '''
    Checks module_name against the declared names and dynamically
    loads the corresponding module.
    '''
    if module_name not in ALL_MODULES:
        raise ValueError('Invalid module name', module_name)
    return import_module('.' + module_name, 'opt')

async def run_opt(logger, secrets, args, req, var=False):
    '''
    Dynamically loads and runs the module specified in req.
    '''
    module_name = req.match_info['module']
    submodule = tuple(
        field
        for field in req.match_info.get('submodule', '').split('/')
        if field
        )
    mlogger = logger.getChild(module_name)
    mlogger.info('Loading module')
    module = load_opt(module_name)
    mlogger.info('Loading successful, running module')
    if var:
        return await module.handler_varopt(mlogger, secrets, args, submodule, req)
    return await module.handler_opt(mlogger, secrets, args, submodule, req)

