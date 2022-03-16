
'''
The main entry point for running a server. The
details are implemented in the server.* modules.
'''

from asyncio import sleep as a_sleep
from os import chmod
from server.site import make_site
from server.app import make_app

async def serve(logger, secrets, args, socket_permissions=0o770):
    '''
    Entrypoint for running the server. Note that the arguments are
    the same as with every module.
    '''
    print('Hello, world!')
    sockpath = args.socket
    if sockpath is None:
        raise ValueError('Missing server socket path', args)
    app = make_app(logger, secrets, args)
    sockpath, site = await make_site(app, sockpath, None)
    await site.start()
    if sockpath is not None:
        chmod(sockpath, socket_permissions)
    while True:
        await a_sleep(3600)
    return None

