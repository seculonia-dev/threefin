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

from argparse import ArgumentParser
from logging import getLogger, Formatter as LogFormatter, StreamHandler

from asyncio import run
from json import load as jload

from modules import ALL_MODULES, load_module
from server import serve

### Defaults and constants ###

LOGFORMAT = '%(asctime)s %(name)s : %(funcName)s@%(module)s : %(message)s'

DEFAULT_SECRETS_FILE = '/opt/tufin/data/securechange/scripts/data/secrets.json'
DEFAULT_DUMP_DIRECTORY = '/opt/tufin/data/securechange/scripts/data/'

### End defaults and constants ###

ALL_LOG_LEVELS = {
    'ERROR'
    , 'WARNING'
    , 'INFO'
    , 'DEBUG'
    , 'NOTSET'
    }

def parse_arguments():
    '''
    Parses the arguments, keeping all the ArgParse configuration
    in one place. In the future it should also take care of loading
    defaults from a config file, but at that point perhaps a name
    change would be in order...
    '''
    #TODO: Defaults and/or choices from config file
    parser = ArgumentParser(description='Tufin script dispatcher')

    # Select module or give base URL
    arggroup = parser.add_mutually_exclusive_group(required=True)
    arggroup.add_argument(
        '-m', '--module'
        , choices=ALL_MODULES
        , default=None
        )
    arggroup.add_argument(
        '-b', '--base-path'
        , default='/threefin/v0.1/'
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
    if args.module is not None:
        logger.info('Loading module %s', args.module)
        module_logger = logger.getChild(args.module)
        module = load_module(args.module)
        logger.info('Running module %s', args.module)
        return await module.main(module_logger, secrets, args)
    logger.info('Running server at %s', args.base_path)
    await serve(logger, secrets, args)

if __name__ == "__main__":
    run(main())


