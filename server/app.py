
'''
Application logic for the server. So far only remote
module invocation is implemented.
'''

from aiohttp.web import Application, RouteTableDef, Response, normalize_path_middleware

from modules import run_module
from tufin.io import format_success_failure

def make_app(logger, secrets, args):
    '''
    Creates the Threefin API's routes and handlers.
    So far only routes remote module invocations.
    '''
    routes = RouteTableDef()
    @routes.post('/api/v0.1/module/{module}')
    async def handle_module(req): # pylint: disable=unused-variable
        '''
        The entry point to invoke a module remotely.
        The bodies of request and response are the same as
        in local invocation.
        '''
        module_name = req.match_info['module']
        instr = await req.text()
        result = await run_module(logger, secrets, args, instr, module_name)
        return Response(text=format_success_failure(result))
    app = Application(middlewares=[
        normalize_path_middleware(
            merge_slashes=True
            , remove_slash=True
            )
        ]
        )
    app.add_routes(routes)
    return app


