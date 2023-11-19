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

from opentelemetry import trace

import bicephalus


_STATUS = {
    bicephalus.Status.OK: 20,
    bicephalus.Status.NOT_FOUND: 51,
    bicephalus.Status.ERROR: 42,
    bicephalus.Status.TEMPORARY_REDIRECTION: 30,
    bicephalus.Status.PERMANENT_REDIRECTION: 31,
}


REDIRECTION_STATUS = (30, 31)


TIMEOUT = 1


log = getLogger(__name__)


class GeminiProtocol(asyncio.Protocol):
    def __init__(self, handler, tracer):
        self.handler = handler
        self.tracer = tracer

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
        self.span = self.tracer.start_span("bicephalus.request", attributes={
            "client.address": transport.get_extra_info("peername")[0],
        })

    def error(self, code: int, msg: str) -> None:
        with trace.use_span(self.span):
            self.transport.write(f"{code} {msg}\r\n".encode("utf-8"))
            self.span.set_status(trace.StatusCode.ERROR)
            self.span.set_attribute("gemini.response.status_code", code)
            self.span.add_event(msg)
            self.transport.close()

    def send_file(self, path):
        with trace.use_span(self.span):
            try:
                response = self.handler(bicephalus.Request(path, bicephalus.Proto.GEMINI))
                status = _STATUS[response.status]
                if status in REDIRECTION_STATUS:
                    meta = response.content
                    content = None
                else:
                    meta = response.content_type
                    content = response.content
            except Exception as e:
                status = _STATUS[bicephalus.Status.ERROR]
                meta = "text/gemini"
                content = repr(e).encode("utf8")
                self.span.record_exception(e)
                self.span.set_status(trace.StatusCode.ERROR)
            self.span.set_attribute("gemini.response.status_code", status)
            self.transport.write(f"{status} {meta}\r\n".encode("utf-8"))
            if content:
                self.transport.write(content)
            self.transport.close()

    def data_received(self, data) -> None:
        with trace.use_span(self.span):
            self.timeout_handle.cancel()
            log.debug(f"{data}")
            if len(data) >= 7 and data[:7] != b"gemini:":
                self.error(59, "Only Gemini requests are supported")
                return
            self.span.set_attribute("url.scheme", "gemini")
            crlf_pos = data.find(b"\r\n")
            if crlf_pos >= 0:
                request = data[:crlf_pos].decode("utf-8")
                url = urlparse(request)
                self.span.set_attribute("url.path", url.path)
                self.send_file(url.path)
            else:
                self.error(59, "Bad Request")
            self.span.end()


def create_server(handler):
    tracer = trace.get_tracer("bicephalus")

    def _():
        return GeminiProtocol(handler, tracer)

    return _
