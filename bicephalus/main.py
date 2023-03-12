import asyncio
import logging

from bicephalus import gemini
from bicephalus import http
from bicephalus import otel


_LOG = logging.getLogger(__name__)


async def async_main(handler, ssl_context, http_port):
    loop = asyncio.get_running_loop()
    _LOG.info("Starting gemini server on 1965")
    gemini_server = await loop.create_server(
        gemini.create_server(handler), port=1965, ssl=ssl_context
    )
    _LOG.info(f"Starting http server on {http_port}")
    http_server = await loop.create_server(http.create_server(handler), port=http_port)
    await asyncio.gather(gemini_server.serve_forever(), http_server.serve_forever())


def main(handler, ssl_context, http_port):
    asyncio.run(async_main(handler, ssl_context, http_port))
