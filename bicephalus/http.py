from asyncio import get_running_loop, run
from logging import getLogger

from aiohttp import web
from aiohttp import web_server


log = getLogger(__name__)


async def handler(request):
    return web.Response(text="OK")


async def main(host, port) -> None:
    """
    Usage:

    $ poetry run python -m bicephalus.http
    """
    loop = get_running_loop()
    server = await loop.create_server(web_server.Server(handler), host, port)
    log.info(f"('{host}', {port})")
    await server.serve_forever()


if __name__ == "__main__":
    run(main("127.0.0.1", 8000))
