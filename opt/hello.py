
'''
A Hello, World module that deals directly with Request objects.
'''

from aiohttp.web import Response

async def handler_opt(logger, secrets, args, req): # pylint: disable=unused-argument
    '''
    The /opt/ case.
    '''
    return Response(text=f'Hello, {req.host}!')

async def handler_varopt(logger, secrets, args, req): # pylint: disable=unused-argument
    '''
    The /var/opt/ case.
    '''
    return Response(text=f'Hello, {req.host}!')
