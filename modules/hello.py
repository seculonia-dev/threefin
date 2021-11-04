
'''
A Hello World module.
'''

from tufin.io import read_tid, write_success_failure

async def main(logger, secrets, args): # pylint: disable=unused-argument,missing-function-docstring
    tid = read_tid(logger=logger)
    logger.debug('Ticket id: %s', tid)
    greetstr = '' if tid is None else f', ticket {tid}'
    logger.info('Hello%s!', greetstr)
    write_success_failure(True)

