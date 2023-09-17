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

import asyncio
from urllib.parse import urlparse
from logging import getLogger

import bicephalus


_STATUS = {
    bicephalus.Status.OK: 20,
    bicephalus.Status.NOT_FOUND: 40,
}


TIMEOUT = 1


log = getLogger(__name__)


class GeminiProtocol(asyncio.Protocol):
    def __init__(self, handler):
        self.handler = handler
        # Enable flow control
        self._can_write = asyncio.Event()
        self._can_write.set()
        # Enable timeouts
        loop = asyncio.get_running_loop()
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
        try:
            response = self.handler(bicephalus.Request(path, bicephalus.Proto.GEMINI))
        except Exception as e:
            log.exception(e)
            raise e
        meta = response.content_type
        status = _STATUS[response.status]
        content = response.content
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


def create_server(handler):
    def _():
        return GeminiProtocol(handler)

    return _
