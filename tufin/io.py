
'''
This module provides two key functions:
    - read_simple(...) provides the ticket indicated by stdin in a
        suitable form for further work.
    - write_success_failure(...) indicates script success or failure
        in the form required by SecureChange.
'''

from sys import stdin, stdout
from xml.etree.ElementTree import fromstring, ParseError, XMLParser

from tufin.ticket import SimpleTicket

TUFINPARSER = XMLParser(encoding='utf-8')

async def read_simple(conn, logger=None):
    '''
    Fetches the ticket indicated by stdin and returns it in mangled form.
    '''
    tid, status, ticket = await read_ticket(conn, logger=logger)
    if status != 200:
        logger.error('Failed to retrieve ticket', tid, status, ticket)
        raise ValueError
    try:
        formatted_ticket = SimpleTicket(ticket)
    except ValueError:
        if logger is not None:
            logger.error('Error mangling ticket %s : %s', tid, ticket)
        raise
    return formatted_ticket

async def read_ticket(conn, logger=None):
    '''
    Fetches the ticket indicated by stdin.
    '''
    tid = read_tid(logger=logger)
    if tid is None:
        return None, None, None
    status, _, ticket = await conn.scget(f'/tickets/{tid}')
    if status == 200:
        ticket = ticket['ticket']
    return tid, status, ticket

def read_tid(logger=None):
    '''
    Fetches the ticket ID from stdin.
    '''
    instr = read_stdin(default='')
    if logger:
        logger.debug('stdin: %s', instr)
    if not instr:
        return None
    try:
        root = fromstring(instr)
    except ParseError:
        return None
    id_element = root.find('id')
    if id_element is None:
        return None
    try:
        ticket_id = int(id_element.text)
        return ticket_id
    except ValueError:
        return None

def read_stdin(default=None):
    '''
    Performs a check for interactive use, substituting a
    default when appropriate.
    '''
    if stdin.isatty():
        if default is not None:
            return default
        raise ValueError('Script needs ticket ID via stdin')
    return stdin.read() #No streaming

def write_success_failure(success):
    '''
    Indicates script success or failure in the form required
    by SecureChange.
    '''
    success_status = 'true' if success else 'false'
    stdout.write(
        '<response><condition_result>'
        + str(success_status)
        + '</condition_result></response>\n'
        )



