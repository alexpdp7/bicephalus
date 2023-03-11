"""
This module is heavily based on:

https://github.com/rcarmo/aiogemini/blob/main/server.py

, which is licensed using the MIT License

MIT License

Copyright (c) 2022 Rui Carmo

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""


from asyncio import Protocol, Event, get_running_loop, run
from ssl import create_default_context, Purpose
from urllib.parse import urlparse
from logging import getLogger


TIMEOUT = 1


log = getLogger(__name__)


class GeminiProtocol(Protocol):
    def __init__(self):
        # Enable flow control
        self._can_write = Event()
        self._can_write.set()
        # Enable timeouts
        loop = get_running_loop()
        self.timeout_handle = loop.call_later(TIMEOUT, self._timeout)
        log.debug(f"Timeout: {TIMEOUT}s")

    def pause_writing(self) -> None:
        log.debug("Pausing data transfer")
        self._can_write.clear()

    def resume_writing(self) -> None:
        log.debug("Resuming data transfer")
        self._can_write.set()

    async def drain(self) -> None:
        log.debug("Checking transfer")
        await self._can_write.wait()

    def _timeout(self) -> None:
        """Close connections upon timeout"""
        log.warning("Connection timeout, closing")
        self.transport.close()

    def connection_made(self, transport) -> None:
        self.transport = transport
        log.info(transport.get_extra_info("peername"))

    def error(self, code: int, msg: str) -> None:
        self.transport.write(f"{code} {msg}\r\n".encode("utf-8"))
        log.error(f"{code} {msg}")
        self.transport.close()

    def send_file(self, path):
        log.debug(path)
        meta, status, content = self.handler(path)
        self.transport.write(f"{status} {meta}\r\n".encode("utf-8"))
        self.transport.write(content)
        log.info(f"{status} {meta} {len(content)}")
        self.transport.close()
        return

    def data_received(self, data) -> None:
        self.timeout_handle.cancel()
        log.debug(f"{data}")
        if len(data) >= 7 and data[:7] != b"gemini:":
            self.error(59, "Only Gemini requests are supported")
            return
        crlf_pos = data.find(b"\r\n")
        if crlf_pos >= 0:
            request = data[:crlf_pos].decode("utf-8")
            url = urlparse(request)
            self.send_file(url.path)
        else:
            self.error(59, "Bad Request")

    def handler(self, path):
        return (
            "text/gemini",
            20,
            f"# Hello world at {path}".encode("utf8"),
        )


async def main(host, port) -> None:
    """
    Usage:

    $ openssl req -x509 -newkey rsa:4096 -keyout key.pem -out cert.pem \
              -days 365 -nodes
    # specify localhost as the common name
    $ poetry run python -m bicephalus.gemini
    """
    loop = get_running_loop()
    context = create_default_context(Purpose.CLIENT_AUTH)
    context.load_cert_chain("cert.pem", "key.pem")
    server = await loop.create_server(GeminiProtocol, host, port, ssl=context)
    log.info(f"('{host}', {port})")
    await server.serve_forever()


if __name__ == "__main__":
    run(main("127.0.0.1", 1965))
