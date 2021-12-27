
'''
A wrapper around the Dump module - the difference is only the exit status.
'''

from modules.dump import dump

async def main(logger, secrets, args, instr): # pylint: disable=unused-argument,missing-function-docstring
    return await dump(logger, secrets, args, instr, False)

