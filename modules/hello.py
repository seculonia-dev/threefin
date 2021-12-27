
'''
A Hello World module. Functions properly even
without credentials - good for simple tests.
'''

from tufin.io import read_tid

async def main(logger, secrets, args, instr): # pylint: disable=unused-argument,missing-function-docstring
    tid = read_tid(instr, logger=logger)
    logger.debug('Ticket id: %s', tid)
    greetstr = '' if tid is None else f', ticket {tid}'
    logger.info('Hello%s!', greetstr)
    return True

