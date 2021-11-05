# pylint: disable=unused-import

'''
A generic wrapper:
    - Parses arguments
    - Loads libraries
    - Loads secrets
    - Hands over execution to module indicated by the arguments.
This file also serves as the entry point for PyInstaller compilation.

TODO:
    - Logging
    - Better secrets management
'''

from importlib import import_module

from argparse import ArgumentParser
from logging import getLogger, Formatter as LogFormatter, StreamHandler

from asyncio import run
from json import load as jload

### Fake imports ###

# These are listed here for PyInstaller to pick up.
# Ideally we'd tell it just to grab all of modules/ ,
# but for the moment this is easier.
# To add a new module, add it here as well as in the
# ALL_MODULES dict.

if False: # pylint: disable=using-constant-test
    import modules.hello
    import modules.dump
    import modules.faildump
    import modules.groupadd

### End fake imports ###

### Defaults and constants ###

LOGFORMAT = '%(asctime)s %(name)s : %(funcName)s@%(module)s : %(message)s'

DEFAULT_SECRETS_FILE = '/opt/tufin/data/securechange/scripts/data/secrets.json'
DEFAULT_DUMP_DIRECTORY = '/opt/tufin/data/securechange/scripts/data/'

ALL_MODULES = {
    'hello'
    , 'dump'
    , 'faildump'
    , 'groupadd'
    }

ALL_LOG_LEVELS = {
    'ERROR'
    , 'WARNING'
    , 'INFO'
    , 'DEBUG'
    , 'NOTSET'
    }

### End defaults and constants ###

def load_module(module_name):
    '''
    Checks module_name against the declared names and dynamically
    loads the corresponding module.
    '''
    if module_name not in ALL_MODULES:
        raise ValueError('Invalid module name', module_name)
    return import_module('modules.'+module_name)

def parse_arguments():
    '''
    Parses the arguments, keeping all the ArgParse configuration
    in one place. In the future it should also take care of loading
    defaults from a config file, but at that point perhaps a name
    change would be in order...
    '''
    #TODO: Defaults and/or choices from config file
    parser = ArgumentParser(description='Tufin script dispatcher')
    parser.add_argument(
        '-m', '--module'
        , required=True
        , choices=ALL_MODULES
        )
    parser.add_argument(
        '--no-tls'
        , dest='tls'
        , default=None
        , action='store_false'
        )
    parser.add_argument(
        '-L', '--log-level'
        , default='INFO'
        , choices=ALL_LOG_LEVELS
        )
    parser.add_argument(
        '-S', '--secrets-file'
        , default=DEFAULT_SECRETS_FILE
        )
    parser.add_argument(
        '-D', '--dump-directory'
        , default=DEFAULT_DUMP_DIRECTORY
        )
    return parser.parse_args()

def load_secrets(logger, path):
    '''
    Loads secrets from the secrets file, which isn't all that
    secret. In the future it should handle secrets loading from
    different sources - suggestions are welcome!
    '''
    #TODO: Secret secrets.
    try:
        with open(path, 'r') as handle:
            secrets = jload(handle)
        logger.info('Loaded secrets from %s', path)
        return secrets
    except FileNotFoundError:
        return None

def make_logger(log_level):
    '''
    A proper logger for all modules. No more print(exception) !
    '''
    fmt = LogFormatter(
        fmt=LOGFORMAT
        )
    logger = getLogger('main')
    logger.setLevel(log_level)
    stream_handler = StreamHandler()
    stream_handler.setFormatter(fmt)
    stream_handler.setLevel(log_level)
    logger.addHandler(stream_handler)
    return logger

async def main():
    '''
    The core dispatcher function.
    Steps:
        - Parses arguments
        - Provides a logger
        - Loads secrets
        - Imports module
        - Runs that module
    '''
    args = parse_arguments()
    logger = make_logger(args.log_level)
    secrets = load_secrets(logger, args.secrets_file)
    if secrets is None:
        logger.critical('Secrets file %s not found', args.secrets_file)
        return None
    logger.info('Loading module %s', args.module)
    module_logger = logger.getChild(args.module)
    module = load_module(args.module)
    logger.info('Running module %s', args.module)
    await module.main(module_logger, secrets, args)

if __name__ == "__main__":
    run(main())


