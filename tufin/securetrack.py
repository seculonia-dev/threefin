
'''
Convenience functions specific to SecureTrack.

Implemented so far:
    - Getting a device ID
    - Getting an object name given the id of the object's device
    - Zone lookups
'''

from ipaddress import ip_network, ip_address

async def grab_device_id(conn, target):
    '''
    Grabs a device's id.
    '''
    status, _, deviceres = await conn.stget('devices', params={'name': target})
    if status != 200:
        raise ValueError('Bad status', target, status, deviceres)
    candidates = deviceres.get('devices', {}).get('device', [])
    for candidate in candidates:
        if candidate['name'] == target:
            return candidate['id']
    raise ValueError('No such device', target)

async def grab_name(conn, device_id, obj):
    '''
    Grabs an object's name on a given device.
    '''
    if isinstance(obj, str):
        endpoint = f'devices/{device_id}/network_objects'
        params = {'name': obj}
    elif hasattr(obj, 'netmask'):
        endpoint = 'network_objects/search'
        params = {
            'device_id': device_id
            , 'filter': 'subnet'
            , 'contains': str(obj.network_address)
            , 'contained_in': str(obj.network_address)
            , 'exact_subnet': obj.netmask
            }
    else:
        endpoint = 'network_objects/search'
        params = {
            'device_id': device_id
            , 'ip': str(obj) # Is this sufficient?
            }
    status, _, res = await conn.stget(endpoint, params=params)
    if status != 200:
        raise ValueError(
            f'Bad result searching for network objects like {obj} on device {device_id}'
            , endpoint
            , params
            , status
            , res
            )
    netobjs = res['network_objects']['network_object']
    if not netobjs:
        return None
    return netobjs[0]['name']

async def zone_lookup(conn, objects):
    '''
    Looks up the zones relevant to the objects specified.
    Assumptions:
        - @xsi.type is either "object_network" or "ip_network"
        - Display names are unique
    '''
    display_name_cache = {}
    payload = {'network_objects': {'network_object': [
        (
            zone_payload_address(obj)
            if hasattr(obj, 'max_prefixlen')
            else zone_payload_object(obj, display_name_cache)
            )
        for obj in objects
        ]}}
    zonedata = await conn.stpost('security_zones', payload)
    res = {}
    for entry in zonedata['security_zones_result']['network_object_zones_map']['entry']:
        value_zones = [
            zone['zone']
            for zone in entry['value']['network_objects_zones']['network_objects_zone']
            ]
        key_full = entry['key']
        if (key_network := key_full.get('network')) is not None:
            key_mask = key_network['mask']
            key_ip = key_network['ip']
            res[ip_network(key_ip + '/' + key_mask)] = value_zones
            if key_mask == '255.255.255.255': #TODO: Recognize IPv6 hosts
                res[ip_address(key_ip)] = value_zones
        else:
            management_id = key_full['management_id']
            uid = key_full['uid']
            display_name = display_name_cache.get(
                (management_id, uid)
                , f'Tufin:/devices/{management_id}/network_objects/{uid}'
                )
            res[display_name] = value_zones
    return res


def zone_payload_object(obj, display_name_cache):
    '''
    Creates the payload for zone retrieval for an object.
    '''
    management_id = obj['management_id']
    uid = obj['object_UID']
    display_name = obj.get('display_name')
    if display_name is not None:
        display_name_cache[(management_id, uid)] = display_name
    return {
        '@xsi.type': 'object_network'
        , 'management_id': management_id
        , 'uid': uid
        }

def zone_payload_address(address):
    '''
    Creates the payload for zone retrieval for a network address.
    '''
    if address.version == 4:
        xsitype = 'raw_network_subnet'
        netmask_default = '255.255.255.255'
    else:
        xsitype = 'raw_network_ipv6'
        netmask_default = 'ffff:ffff:ffff:ffff' #Pure guesswork, there's no example at hand
    return {
        '@xsi.type': 'ip_network'
        , 'network': {
            '@xsi.type': xsitype
            , 'ip': str(getattr(address, 'network_address', address))
            , 'mask': str(getattr(address, 'netmask', netmask_default))
            }
        }



