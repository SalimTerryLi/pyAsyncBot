# -*- coding: utf-8 -*-

from loguru import logger
import asyncio
import typing
import aiohttp
import sys

from .CommunicationBackend import CommunicationBackend


class HTTPClient(CommunicationBackend):
    """
    HTTP Client backend
    """
    _ahttp: aiohttp.ClientSession

    def __init__(self, remote_addr: str, remote_port: int):
        self._addr = remote_addr
        self._port = remote_port
        self._ahttp = None

    async def setup(self) -> typing.Any:
        self._ahttp = aiohttp.ClientSession(loop=asyncio.get_running_loop())
        return HTTPClientAPI(self)

    async def cleanup(self):
        await self._ahttp.close()

    async def run_daemon(self):
        # HTTP client has no daemon
        pass

    async def upgrade_ws(self) -> aiohttp.client.ClientWebSocketResponse:
        try:
            return await self._ahttp.ws_connect('ws://{remote_addr}:{remote_port}'.format(
                remote_addr=self._addr,
                remote_port=self._port
            ))
        except Exception as e:
            logger.error(e)
            return None


class HTTPClientAPI:
    __base: HTTPClient

    def __init__(self, base: HTTPClient):
        self.__base = base

    async def get(self, path: str, allow_redirects: bool = True, **kwargs: typing.Any) -> aiohttp.ClientResponse:
        retry_count = 0
        while True:
            try:
                return await self.__base._ahttp.get('http://{addr}:{port}{path}'.format(
                    addr=self.__base._addr,
                    port=self.__base._port,
                    path=path,
                ), allow_redirects=allow_redirects, **kwargs)
            except aiohttp.ClientConnectorError as e:
                # remote service down
                raise e
            except aiohttp.ClientOSError as e:
                print('aiohttp GET failed, retrying...', file=sys.stderr)
                retry_count += 1
                if retry_count > 3:
                    raise e
                continue

    async def post(self, path: str, data: typing.Any = None, **kwargs: typing.Any) -> aiohttp.ClientResponse:
        retry_count = 0
        while True:
            try:
                return await self.__base._ahttp.post('http://{addr}:{port}{path}'.format(
                    addr=self.__base._addr,
                    port=self.__base._port,
                    path=path,
                ), data=data, **kwargs)
            except aiohttp.ClientConnectorError as e:
                # remote service down
                raise e
            except aiohttp.ClientOSError as e:
                print('aiohttp POST failed, retrying...', file=sys.stderr)
                retry_count += 1
                if retry_count > 3:
                    raise e
                continue
