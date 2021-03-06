
'''
Convenience functions specific to SecureChange.

Implemented so far:
    - Group changes retaining existing members
To be implemented:
    - Group changes not retaining existing members
    - Group changes specifying members to be removed
'''

#TODO: Properly subdivide the various types of group changes.

from tufin.securetrack import grab_name

def group_change(mgmt_id, name, members, exists=True):
    '''
    Generates a group change payload from member data as provided by
    make_member_data(...) . Caveat: This operation will only add members,
    existing members are retained.
    '''
    return {
        '@xsi.type': 'multi_group_change'
        , 'group_change': [
            group_change_payload(mgmt_id, name, members, exists=exists)
            ]
        }

def group_change_multiple(data):
    '''
    Like group_change(...), but for several groups at a time. The data
    argument is a dict of form
        {
            (groupname, mgmt_id): (existing_or_new, members)
            }
    '''
    return {
        '@xsi.type': 'multi_group_change'
        , 'group_change': [
            group_change_payload(mgmt_id, name, members, exists=exists)
            for (name, mgmt_id), (exists, members) in data.items()
            ]
        }

def group_change_payload(mgmt_id, name, members, exists=True):
    '''
    Creates a single group change payload. Used by group_change(...)
    and group_change_multiple(...) .
    '''
    return {
        'name': name
        , 'management_id': mgmt_id
        , 'members': {'member': members}
        , 'change_action': 'UPDATE' if exists else 'CREATE'
        }

async def make_member_data(conn, mgmt_id, obj, name=None, comment=''):
    '''
    Creates the payload for a single member, checking whether a suitable
    object already exists.
    '''
    existing_name = await grab_name(conn, mgmt_id, obj)
    if existing_name is not None:
        return existing_object(mgmt_id, existing_name)
    if hasattr(obj, 'netmask'):
        return new_network(mgmt_id, obj, name=name, comment=comment)
    return new_host(mgmt_id, obj, name=name, comment=comment)

def new_host(mgmt_id, ipobj, name=None, comment=''):
    '''
    Creates the payload for a single new host. A remove option
    is not necessary.
    '''
    if name is None:
        name = f'Host_{ipobj}'
    return {
        '@type': 'HOST'
        , 'name': name
        , 'object_UID': name
        , 'object_type': 'Host'
        , 'object_details': f'{ipobj}/255.255.255.255'
        , 'management_id': mgmt_id
        , 'status': 'ADDED'
        , 'comment': comment
        , 'object_updated_status': 'NEW'
        }

def new_network(mgmt_id, ipobj, name=None, comment=''):
    '''
    Creates the payload for a single new network. A remove option
    is not necessary.
    '''
    if name is None:
        name = f'Host_{ipobj.network_address}_{ipobj.prefixlen}'
    return {
        '@type': 'NETWORK'
        , 'name': name
        , 'object_UID': name
        , 'object_type': 'Network'
        , 'object_details': ipobj.with_netmask
        , 'management_id': mgmt_id
        , 'status': 'ADDED'
        , 'comment': comment
        , 'object_updated_status': 'NEW'
        }

def existing_object(mgmt_id, name, remove=False):
    '''
    Creates the payload for a single existing object.
    '''
    status = 'DELETED' if remove else 'ADDED'
    return {
        '@type': 'Object'
        , 'name': name
        , 'management_id': mgmt_id
        , 'status': status
        , 'object_updated_status': 'EXISTING_NOT_EDITED'
        }

