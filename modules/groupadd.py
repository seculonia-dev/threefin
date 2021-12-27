
'''
An example module that adds three fake addresses to a fixed group on a fixed
device and writes the changes to the "Modifications" field of the input ticket.
'''

from ipaddress import ip_address
from json import dumps

from tufin.common import TufinConn
from tufin.io import read_simple
from tufin.securetrack import grab_device_id
from tufin.securechange import make_member_data, group_change


FAKE_ADDRESSES = [
    ip_address('10.10.10.10')
    , ip_address('10.10.10.11')
    , ip_address('10.10.10.12')
    ]

TARGET_DEVICE = 'jk-CPMgmt'
TARGET_GROUP = 'Z_Intern'

async def main(logger, secrets, args, instr): # pylint: disable=unused-argument,missing-function-docstring
    async with TufinConn(secrets, logger=logger, tls=args.tls) as conn:
        ticket = await read_simple(conn, instr, logger=logger)
        mgmt_id = await grab_device_id(conn, TARGET_DEVICE)
        members = [
            await make_member_data(conn, mgmt_id, obj)
            for obj in FAKE_ADDRESSES
            ]
        logger.debug('Members: %s', dumps(members, indent=2, default=str))
        groupchange = group_change(mgmt_id, TARGET_GROUP, members)
        logger.debug('Groupchange: %s', dumps(groupchange, indent=2, default=str))
        status, headers, res = await ticket.set(conn, {'Modifications': groupchange})
        if status != 200:
            logger.error('Bad response: Status %s, headers %s, body %s', status, headers, res)
            return False
    return True
