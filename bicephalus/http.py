from aiohttp import web
from aiohttp import web_server

import bicephalus


def create_server(handler):
    async def adapter(request: web.Request):
        handler_response = handler(
            bicephalus.Request(request.path, bicephalus.Proto.HTTP)
        )
        status = {bicephalus.Status.OK: 200}[handler_response.status]
        return web.Response(
            text=handler_response.content.decode("utf8"),
            content_type=handler_response.content_type,
            status=status,
        )

    return web_server.Server(adapter)
