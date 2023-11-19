from aiohttp import web
from aiohttp import web_server

import bicephalus

from opentelemetry import trace


_STATUS = {
    bicephalus.Status.OK: 200,
    bicephalus.Status.NOT_FOUND: 404,
    bicephalus.Status.TEMPORARY_REDIRECTION: 307,
    bicephalus.Status.PERMANENT_REDIRECTION: 308,
    bicephalus.Status.ERROR: 500,
}


REDIRECTION_CLASSES = {
    307: web.HTTPTemporaryRedirect,
    308: web.HTTPPermanentRedirect,
}


def create_server(handler):
    tracer = trace.get_tracer("bicephalus")

    async def adapter(request: web.Request):
        with tracer.start_as_current_span("bicephalus.request", attributes={
                "url.path": request.path,
                "client.address": request.remote,
                "user_agent.original": request.headers.get("User-Agent"),
                "url.scheme": "http",
        }) as span:
            try:
                handler_response = handler(
                    bicephalus.Request(request.path, bicephalus.Proto.HTTP)
                )
                status = _STATUS[handler_response.status]
                span.set_attribute("http.response.status_code", status)

                redirection_class = REDIRECTION_CLASSES.get(status)
                if redirection_class:
                    raise redirection_class(handler_response.content)

                return web.Response(
                    text=handler_response.content.decode("utf8"),
                    content_type=handler_response.content_type,
                    status=status,
                )
            except web.HTTPPermanentRedirect:
                raise
            except web.HTTPTemporaryRedirect:
                raise
            except Exception as e:
                span.set_status(trace.StatusCode.ERROR)
                span.set_attribute("http.response.status_code", 500)
                span.record_exception(e)
                return web.Response(
                    text=str(e),
                    content_type="text/plain",
                    status=500,
                )

    return web_server.Server(adapter)
