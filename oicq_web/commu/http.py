# -*- coding: utf-8 -*-
from __future__ import annotations

import typing
from asyncio import AbstractEventLoop
import aiohttp

from .CommunicationBackend import CommunicationBackend


class HTTPClient(CommunicationBackend):
    """
    HTTP Client backend

    send_message type: {'method':, 'path':, 'content-type':, 'params': 'data'}

    return type: {'code':, 'content-type':, 'data':}
    """
    _ahttp: aiohttp.ClientSession

    def __init__(self, remote_addr: str, remote_port: int):
        self._addr = remote_addr
        self._port = remote_port
        self._ahttp = None
        print('new http client created')

    async def setup(self, ev_loop: AbstractEventLoop) -> bool:
        self._ahttp = aiohttp.ClientSession(loop=ev_loop)
        return True

    async def cleanup(self, ev_loop: AbstractEventLoop):
        await self._ahttp.close()

    async def upgrade_ws(self) -> aiohttp.client.ClientWebSocketResponse:
        try:
            return await self._ahttp.ws_connect('ws://{remote_addr}:{remote_port}'.format(
                remote_addr=self._addr,
                remote_port=self._port
            ))
        except Exception as e:
            print(e)
            return None

    async def send_message(self, data: typing.Any) -> typing.Any:
        res = None
        path = ''
        if 'path' in data:
            path = data['path']
        content_type = 'application/json'
        if 'content-type' in data:
            content_type = data['content-type']
        params = None
        if 'params' in data:
            params = data['params']
        body_data = None
        if 'data' in data:
            body_data = data['data']
        if data['method'] == 'GET':
            res = await self._ahttp.get('http://{addr}:{port}/{path}'.format(
                addr=self._addr,
                port=self._port,
                path=path,
            ), params=params, headers={'content-type': content_type}, data=body_data)
        elif data['method'] == 'POST':
            res = await self._ahttp.post('http://{addr}:{port}/{path}'.format(
                addr=self._addr,
                port=self._port,
                path=data['path'],
            ), params=params, headers={'content-type': content_type}, data=body_data)
        return {
            'code': res.status,
            'content-type': res.headers['content-type'],
            'data': await res.read()
        }
