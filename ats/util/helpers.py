
import json
import ssl

import aiohttp
import aiohttp.web


async def authenticated_userid(request):
    try:
        userid = request.headers['X-Auth-UserId']
    except KeyError:
        await request.release()
        js = {'error': 'Missing authentication header'}
        raise aiohttp.web.HTTPUnauthorized(content_type='application/json',
                                           text=json.dumps(js))

    # Bind user name for structured logging
    if request.get('slog'):
        request['slog'] = request['slog'].bind(uid=userid)

    return userid


def get_os_session(*, os_cacert, insecure, log):
    """
    Returns a secure - or insecure - HTTP session depending
    on configuration settings.
    Works for both HTTP and HTTPS endpoints.
    """
    if os_cacert:
        ssl_context = ssl.create_default_context(cafile=os_cacert)
        return aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl_context=ssl_context))

    if insecure:
        log.warning('Insecure connection to OpenStack')
        return aiohttp.ClientSession(connector=aiohttp.TCPConnector(verify_ssl=False))

    log.error('No cacert provided and insecure parameter not specified')
