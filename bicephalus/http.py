from aiohttp import web
from aiohttp import web_server

import bicephalus


_STATUS = {
    bicephalus.Status.OK: 200,
    bicephalus.Status.NOT_FOUND: 404,
    bicephalus.Status.TEMPORARY_REDIRECTION: 307,
    bicephalus.Status.PERMANENT_REDIRECTION: 308,
}


REDIRECTION_CLASSES = {
    307: web.HTTPTemporaryRedirect,
    308: web.HTTPPermanentRedirect,
}

def create_server(handler):
    async def adapter(request: web.Request):
        handler_response = handler(
            bicephalus.Request(request.path, bicephalus.Proto.HTTP)
        )
        status = _STATUS[handler_response.status]

        redirection_class = REDIRECTION_CLASSES.get(status)
        if redirection_class:
            raise redirection_class(handler_response.content)

        return web.Response(
            text=handler_response.content.decode("utf8"),
            content_type=handler_response.content_type,
            status=status,
        )

    return web_server.Server(adapter)
