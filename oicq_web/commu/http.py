# -*- coding: utf-8 -*-
from __future__ import annotations

import asyncio
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

    _api: HTTPClientAPI

    def __init__(self, remote_addr: str, remote_port: int):
        self._addr = remote_addr
        self._port = remote_port
        self._ahttp = None
        self._api = None
        print('new http client created')

    async def setup(self) -> bool:
        self._ahttp = aiohttp.ClientSession(loop=asyncio.get_running_loop())
        self._api = HTTPClientAPI(self)
        return True

    async def cleanup(self):
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

    def get_http_client(self):
        """
        Call this function to get a reference of aiohttp client obj

        :return:
        """
        return self._api


class HTTPClientAPI:
    __base: HTTPClient

    def __init__(self, base: HTTPClient):
        self.__base = base

    async def get(self, path: str, allow_redirects: bool = True, **kwargs: typing.Any) -> aiohttp.ClientResponse:
        return await self.__base._ahttp.get('http://{addr}:{port}{path}'.format(
                addr=self.__base._addr,
                port=self.__base._port,
                path=path,
            ), allow_redirects=allow_redirects, **kwargs)
