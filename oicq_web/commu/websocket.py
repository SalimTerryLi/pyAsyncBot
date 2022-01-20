# -*- coding: utf-8 -*-
import asyncio
import aiohttp
import typing

from .CommunicationBackend import CommunicationBackend
from .http import HTTPClient


class WebSocketClient(CommunicationBackend):
    """
    WebSocket Client backend

    callback format: dict {'type': 'binary|text', 'data': data}

    send_message format: dict {'type': 'binary|text', 'data': msg.data} return True as success
    """
    _aws: aiohttp.client.ClientWebSocketResponse
    _http_base: HTTPClient
    _http_base_managed: bool

    _on_text_cb: typing.Callable[[str], None]
    _on_bin_cb: typing.Callable[[bytes], None]

    def __init__(self):
        self._http_base = None
        self._http_base_managed = None
        self._aws = None
        self._on_text_cb = None

    @classmethod
    def from_http_client(cls, http_client: HTTPClient):
        ret = cls()
        ret._http_base = http_client
        ret._http_base_managed = False
        ret._aws = None
        print('ws client reuse existing http client')
        return ret

    @classmethod
    def from_parameters(cls, remote_addr: str, remote_port: int):
        ret = cls()
        ret._http_base = HTTPClient(remote_addr, remote_port)
        ret._http_base_managed = True
        ret._aws = None
        print('ws client use newly created http client')
        return ret

    async def setup(self, ev_loop: asyncio.AbstractEventLoop) -> bool:
        if self._http_base_managed:
            await self._http_base.setup(ev_loop)
        self._aws = await self._http_base.upgrade_ws()
        if self._aws is None:
            print('failed to create ws from http client')
            return False
        return True

    async def cleanup(self, ev_loop: asyncio.AbstractEventLoop):
        if self._aws is not None:
            await self._aws.close()
        if self._http_base_managed:
            await self._http_base.cleanup(ev_loop)

    async def run_daemon(self, ev_loop: asyncio.AbstractEventLoop):
        while True:
            try:
                msg = await self._aws.receive()
                if msg.type == aiohttp.WSMsgType.error:
                    print(msg)
                    # TODO: should we do something here?
                elif msg.type == aiohttp.WSMsgType.closed:
                    print(self._aws.exception())
                    while True:
                        try:
                            print('WebSocket disconnected. wait 10s before reconnect')
                            await asyncio.sleep(10)
                            self._aws = await self._http_base.upgrade_ws()
                            # no more exception means successfully connected
                            print('successfully reconnected')
                            break
                        except asyncio.CancelledError:
                            print('reconnecting canceled')
                            return
                        except Exception as e:
                            print(e)
                elif msg.type == aiohttp.WSMsgType.text:
                    if self._on_text_cb is not None:
                        self._on_text_cb(msg.data)
                elif msg.type == aiohttp.WSMsgType.binary:
                    if self._on_bin_cb is not None:
                        self._on_bin_cb(msg.data)
            except asyncio.CancelledError:
                print('WebSocket client stopped')
                await self._aws.close()
                return

    def register_text_message_callback(self, callback: typing.Callable[[str], None]):
        """
        Call this function to register a text message callback

        :param callback: callback function
        :return:
        """
        self._on_text_cb = callback

    def register_binary_message_callback(self, callback: typing.Callable[[bytes], None]):
        """
        Call this function to register a binary message callback

        :param callback: callback function
        :return:
        """
        self._on_bin_cb = callback

    async def send_text_message(self, data: typing.Any) -> typing.Any:
        try:
            await self._aws.send_str(data['data'])
            return True
        except Exception as e:
            print(e)
            return False

    async def send_binary_message(self, data: typing.Any) -> typing.Any:
        try:
            await self._aws.send_bytes(data['data'])
            return True
        except Exception as e:
            print(e)
            return False
