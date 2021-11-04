
from tufin.securetrack import grab_name

def group_change(mgmt_id, name, members, exists=True):
    return {
        '@xsi.type': 'multi_group_change'
        , 'group_change': [
            group_change_payload(mgmt_id, name, members, exists=exists)
            ]
        }

def group_change_multiple(data):
    '''
    data is a dict of form {(groupname, mgmt_id): (existing_or_new, members)}
    '''
    return {
        '@xsi.type': 'multi_group_change'
        , 'group_change': [
            group_change_payload(mgmt_id, name, members, exists=exists)
            for (name, mgmt_id), (exists, members) in data.items()
            ]
        }

def group_change_payload(mgmt_id, name, members, exists=True):
    return {
        'name': name
        , 'management_id': mgmt_id
        , 'members': {'member': members}
        , 'change_action': 'UPDATE' if exists else 'CREATE'
        }

async def make_member_data(conn, mgmt_id, obj, name=None, comment=''):
    existing_name = await grab_name(conn, mgmt_id, obj)
    if existing_name is not None:
        return existing_object(mgmt_id, existing_name)
    if hasattr(obj, 'netmask'):
        return new_network(mgmt_id, obj, name=name, comment=comment)
    return new_host(mgmt_id, obj, name=name, comment=comment)

def new_host(mgmt_id, ipobj, name=None, comment=''):
    objname = f'Host_{ipobj}' if name is None else name
    return {
        '@type': 'HOST'
        , 'name': objname
        , 'object_UID': objname
        , 'object_type': 'Host'
        , 'object_details': f'{ipobj}/255.255.255.255'
        , 'management_id': mgmt_id
        , 'status': 'ADDED'
        , 'comment': comment
        , 'object_updated_status': 'NEW'
        }

def new_network(mgmt_id, ipobj, name=None, comment=''):
    objname = f'Host_{ipobj.network_address}_{ipobj.prefixlen}' if name is None else name
    return {
        '@type': 'NETWORK'
        , 'name': objname
        , 'object_UID': objname
        , 'object_type': 'Network'
        , 'object_details': ipobj.with_netmask
        , 'management_id': mgmt_id
        , 'status': 'ADDED'
        , 'comment': comment
        , 'object_updated_status': 'NEW'
        }

def existing_object(mgmt_id, name, remove=False):
    status = 'DELETED' if remove else 'ADDED'
    return {
        '@type': 'Object'
        , 'name': name
        , 'management_id': mgmt_id
        , 'status': status
        , 'object_updated_status': 'EXISTING_NOT_EDITED'
        }

