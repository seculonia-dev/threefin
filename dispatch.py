
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

if False:
    import modules.hello
    import modules.dump
    import modules.faildump
    import modules.groupadd

### End fake imports ###

DEFAULT_SECRETS_FILE = '/opt/tufin/data/securechange/scripts/data/secrets.json'

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

def load_module(module_name):
    if module_name not in ALL_MODULES:
        raise ValueError('Invalid module name', module_name)
    return import_module('modules.'+module_name)

def parse_arguments():
    parser = ArgumentParser(description='Tufin script dispatcher')
    parser.add_argument('-m', '--module', required=True, choices=ALL_MODULES)
    parser.add_argument('--no-tls', dest='tls', action='store_false', default=None)
    parser.add_argument('-L', '--log-level', choices=ALL_LOG_LEVELS, default='INFO')
    parser.add_argument('-S', '--secrets-file', default=DEFAULT_SECRETS_FILE)
    parser.add_argument('-D', '--dump-directory', default='/opt/tufin/data/securechange/scripts/data/')
    return parser.parse_args()

def load_secrets(logger, path):
    try:
        with open(path, 'r') as handle:
            secrets = jload(handle)
        logger.info('Loaded secrets from %s', path)
        return secrets
    except FileNotFoundError:
        return None

def make_logger(log_level):
    fmt = LogFormatter(fmt='%(asctime)s %(name)s : %(funcName)s@%(module)s : %(message)s')
    logger = getLogger('main')
    logger.setLevel(log_level)
    stream_handler = StreamHandler()
    stream_handler.setFormatter(fmt)
    stream_handler.setLevel(log_level)
    logger.addHandler(stream_handler)
    return logger

async def main():
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


