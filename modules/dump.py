
'''
Mangles the input ticket and dumps both the raw and the mangled version to disk.
'''

from json import dump as jdump, dumps as jdumps

from tufin.common import TufinConn
from tufin.io import read_ticket, write_success_failure
from tufin.ticket import SimpleTicket

def raw_path(dumpdir, ticketid, instatus):
    '''
    Creates the dumping path for the raw ticket.
    '''
    return f'{dumpdir}/ticket_raw_{ticketid}_{instatus}.json'

def mangled_path(dumpdir, ticketid):
    '''
    Creates the dumping path for the mangled ticket.
    '''
    return f'{dumpdir}/ticket_mangled_{ticketid}.json'

async def dump(logger, secrets, args, action):
    '''
    The core function of the module - main(...) only supplies the exit code.
    This function is reused in the faildump module, which motivates the split.
    '''
    dumpdir = args.dump_directory
    async with TufinConn(secrets, tls=args.tls) as conn:
        ticketid, instatus, inticket = await read_ticket(conn, logger=logger)
    with open(raw_path(dumpdir, ticketid, instatus), 'w+') as handle:
        jdump(inticket, handle)
    if not instatus < 400:
        if logger is not None:
            logger.error(f'Error retrieving ticket #{ticketid}')
            logger.info('Status: %s', instatus)
            logger.info('Raw data:\n%s', inticket)
        return None
    try:
        formatted_ticket = SimpleTicket(inticket)
    except ValueError:
        if logger is not None:
            logger.error(f'Error mangling ticket #{ticketid}')
            logger.info('Status: %s', instatus)
            logger.info('Raw data:\n%s', inticket)
        write_success_failure(False)
        return None
    with open(mangled_path(dumpdir, ticketid), 'w+') as handle:
        jdump(formatted_ticket.show(), handle)
    if logger is not None:
        logger.info('All done!')
        logger.info('Status: %s', instatus)
        logger.info('Raw data:\n%s', jdumps(inticket, indent=2))
        logger.info('Mangled data:\n%s', jdumps(formatted_ticket.show(), indent=2))
    write_success_failure(action)

async def main(logger, secrets, args): # pylint: disable=unused-argument,missing-function-docstring
    return await dump(logger, secrets, args, True)
