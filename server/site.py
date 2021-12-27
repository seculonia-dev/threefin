
'''
Server infrastructure, mostly related to choosing
the right socket.
'''

from urllib.parse import urlparse

from aiohttp.web import AppRunner, UnixSite, TCPSite

async def make_site(app, path, tls):
    '''
    Wrapper to prepare the application runner and
    set up the site.
    '''
    runner = AppRunner(app)
    await runner.setup()
    return _make_site_from_runner(runner, path, tls)

def _make_site_from_runner(runner, path, tls):
    '''
    Creates site from an app, choosing between TCPIP and
    UNIX domain sockets based on the socket path's prefix.
    '''
    components = urlparse(path)
    if components.scheme == 'tcp':
        if not components.netloc:
            raise ValueError('TCP socket needs binding IP and port')
        return TCPSite(
            runner
            , components.hostname
            , components.port
            , ssl_context=tls
            )
    if components.scheme == 'unix':
        if tls is not None:
            raise ValueError('TLS is not supported over UNIX domain socket', path, tls)
        if components.netloc:
            raise ValueError('UNIX domain socket URIs with authority section are not supported')
        return UnixSite(
            runner
            , components.path
            )
    raise ValueError('Bad spec for site runner socket, use tcp:// or unix: prefix', path)
