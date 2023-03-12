import asyncio
import ssl

from bicephalus import gemini
from bicephalus import http


def create_ssl_context():
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
    context.load_cert_chain("cert.pem", "key.pem")
    return context


async def async_main(handler):
    ssl_context = create_ssl_context()
    loop = asyncio.get_running_loop()
    gemini_server = await loop.create_server(
        gemini.create_server(handler), port=1965, ssl=ssl_context
    )
    http_server = await loop.create_server(http.create_server(handler), port=8000)
    await asyncio.gather(gemini_server.serve_forever(), http_server.serve_forever())


def main(handler):
    asyncio.run(async_main(handler))
