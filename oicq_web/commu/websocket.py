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

    def __init__(self):
        self._http_base = None
        self._http_base_managed = None
        self._aws = None

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

    async def await_message(self, ev_loop: asyncio.AbstractEventLoop, callback: typing.Callable[[typing.Any],None], tag: str):
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
                    callback({tag: {'type': 'text', 'data': msg.data}})
                elif msg.type == aiohttp.WSMsgType.binary:
                    callback({tag: {'type': 'binary', 'data': msg.data}})
            except asyncio.CancelledError:
                print('WebSocket client stopped')
                await self._aws.close()
                return

    async def send_message(self, data: typing.Any) -> typing.Any:
        try:
            if data['type'] == 'binary':
                await self._aws.send_bytes(data['data'])
            elif data['type'] == 'text':
                await self._aws.send_str(data['data'])
            else:
                print('ws client unsupported data format: ' + data['type'])
                return False
            return True
        except Exception as e:
            print(e)
            return False
