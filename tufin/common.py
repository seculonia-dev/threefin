
'''
This module provides the TufinConn class, abstracting over the communication
with the SecureTrack and SecureChange servers.
'''

from asyncio import gather
from json import dumps

from aiohttp import ClientSession, BasicAuth, ContentTypeError

TUFIN_HEADERS = {
    'accept': 'application/json'
    , 'content-type': 'application/json'
    }

def singleton_or_list(obj):
    '''
    A generator that turns lists into multi-item streams and other
    objects into single-item streams.

    Up until recently, the Tufin APIs returned single-member lists as
    plain objects in their JSON output. Newer versions have rectified
    this, but for the sake of compatibility we keep this generator.
    '''
    if not isinstance(obj, list):
        yield obj
        return
    for subobj in obj:
        yield subobj


class TufinConn():
    """
    A wrapper to grab authentication data and
    generate the right headers.
    """
    def __init__(self, secrets, logger=None, tls=None):
        self._logger = logger

        scbaseurl = secrets.get('SECURECHANGEURL')
        scusername = secrets.get('SECURECHANGEUSER')
        scpassword = secrets.get('SECURECHANGEPASSWORD')
        assert scbaseurl is not None
        assert scusername is not None
        assert scpassword is not None
        stbaseurl = secrets.get('SECURETRACKURL')
        stusername = secrets.get('SECURETRACKUSER')
        stpassword = secrets.get('SECURETRACKPASSWORD')
        assert stbaseurl is not None
        assert stusername is not None
        assert stpassword is not None

        self._scconn = ClientSession(
            auth=BasicAuth(scusername, password=scpassword)
            , headers=TUFIN_HEADERS
            )
        self._stconn = ClientSession(
            auth=BasicAuth(stusername, password=stpassword)
            , headers=TUFIN_HEADERS
            )
        self._scbaseurl = scbaseurl if scbaseurl[-1] == '/' else scbaseurl+'/'
        self._stbaseurl = stbaseurl if stbaseurl[-1] == '/' else stbaseurl+'/'
        self._tls = tls
        return None
    async def __aenter__(self):
        '''
        Infrastructure function.
        '''
        return self
    async def __aexit__(self, exc_type, exc, tb): # pylint: disable=invalid-name
        '''
        Infrastructure function. Closes the underlying connections.
        '''
        await gather(
            self._scconn.close()
            , self._stconn.close()
            )
        return None
    async def _call(self, conn, method, url, body, params=None): # pylint: disable=too-many-arguments
        '''
        A generic call to some endpoint.
        '''
        res = await conn.request(method, url, json=body, params=params, ssl=self._tls)
        try:
            resjson = await res.json()
        except ContentTypeError as e:
            restext = await res.text()
            if not restext:
                return res.status, res.headers, None
            raise ValueError('Server did not return valid JSON', url, res.status, restext) from e
        if self._logger:
            self._logger.debug('''
Method: %s
URL: %s
Params: %s
Body: %s
Status: %s
Result: %s
''', method, url, params, body, res.status, dumps(resjson))
        return res.status, res.headers, resjson

    async def stcall(self, method, endpoint, body, params=None):
        '''
        A generic call to the SecureTrack endpoint.
        '''
        url = self._stbaseurl + endpoint
        return await self._call(self._stconn, method, url, body, params=params)
    async def stget(self, endpoint, params=None):
        '''
        A GET call to the SecureTrack endpoint.
        '''
        return await self.stcall('GET', endpoint, None, params=params)
    async def stpost(self, endpoint, body, params=None):
        '''
        A POST call to the SecureTrack endpoint.
        '''
        return await self.stcall('POST', endpoint, body, params=params)
    async def stput(self, endpoint, body, params=None):
        '''
        A PUT call to the SecureTrack endpoint.
        '''
        return await self.stcall('PUT', endpoint, body, params=params)

    async def sccall(self, method, endpoint, body, params=None):
        '''
        A generic call to the SecureChange endpoint.
        '''
        url = self._scbaseurl + endpoint
        return await self._call(self._scconn, method, url, body, params=params)
    async def scget(self, endpoint, params=None):
        '''
        A GET call to the SecureChange endpoint.
        '''
        return await self.sccall('GET', endpoint, None, params=params)
    async def scpost(self, endpoint, body, params=None):
        '''
        A POST call to the SecureChange endpoint.
        '''
        return await self.sccall('POST', endpoint, body, params=params)
    async def scput(self, endpoint, body, params=None):
        '''
        A PUT call to the SecureChange endpoint.
        '''
        return await self.sccall('PUT', endpoint, body, params=params)

