# -*- coding: utf-8 -*-

from loguru import logger
import asyncio
import aiohttp
import typing

from .CommunicationBackend import CommunicationBackend
from .http import HTTPClient


class WebSocketClient(CommunicationBackend):
    """
    WebSocket Client backend
    """

    def __init__(self):
        self._http_base: HTTPClient = None
        self._http_base_managed: bool = None
        self._aws: aiohttp.client.ClientWebSocketResponse = None
        self._on_text_cb: typing.Callable[[str], None] = None
        self._on_bin_cb: typing.Callable[[bytes], None] = None

    @classmethod
    def from_http_client(cls, http_client: HTTPClient):
        ret = cls()
        ret._http_base = http_client
        ret._http_base_managed = False
        ret._aws = None
        logger.debug('ws client reuse existing http client')
        return ret

    @classmethod
    def from_parameters(cls, remote_addr: str, remote_port: int):
        ret = cls()
        ret._http_base = HTTPClient(remote_addr, remote_port)
        ret._http_base_managed = True
        ret._aws = None
        logger.debug('ws client use newly created http client')
        return ret

    async def setup(self) -> typing.Any:
        if self._http_base_managed:
            await self._http_base.setup()
        self._aws = await self._http_base.upgrade_ws()
        if self._aws is None:
            logger.critical('failed to create ws from http client')
            raise CommunicationBackend.SetupFailed()
        return WSClientAPI(self)

    async def cleanup(self):
        if self._aws is not None:
            await self._aws.close()
        if self._http_base_managed:
            await self._http_base.cleanup()

    async def run_daemon(self):
        while True:
            try:
                msg = await self._aws.receive()
                if msg.type == aiohttp.WSMsgType.error:
                    logger.error(msg)
                    # TODO: should we do something here?
                elif msg.type == aiohttp.WSMsgType.closed:
                    logger.error(self._aws.exception())
                    while True:
                        try:
                            logger.info('WebSocket disconnected. wait 10s before reconnect')
                            await asyncio.sleep(10)
                            self._aws = await self._http_base.upgrade_ws()
                            if self._aws is None:
                                logger.info('retrying...')
                            else:
                                logger.info('successfully reconnected')
                                break
                        except asyncio.CancelledError:
                            logger.info('reconnecting canceled')
                            return
                        except Exception as e:
                            logger.error(e)
                elif msg.type == aiohttp.WSMsgType.text:
                    if self._on_text_cb is not None:
                        self._on_text_cb(msg.data)
                elif msg.type == aiohttp.WSMsgType.binary:
                    if self._on_bin_cb is not None:
                        self._on_bin_cb(msg.data)
            except asyncio.CancelledError:
                logger.info('WebSocket client stopped')
                await self._aws.close()
                return


class WSClientAPI:
    def __init__(self, wsclient: WebSocketClient):
        self._ws: WebSocketClient = wsclient

    def register_text_message_callback(self, callback: typing.Callable[[str], None]):
        """
        Call this function to register a text message callback

        :param callback: callback function
        """
        self._ws._on_text_cb = callback

    def register_binary_message_callback(self, callback: typing.Callable[[bytes], None]):
        """
        Call this function to register a binary message callback

        :param callback: callback function
        """
        self._ws._on_bin_cb = callback

    async def send_text_message(self, data: str) -> typing.Any:
        try:
            await self._ws._aws.send_str(data)
            return True
        except Exception as e:
            logger.error(e)
            return False

    async def send_binary_message(self, data: bytes) -> typing.Any:
        try:
            await self._ws._aws.send_bytes(data)
            return True
        except Exception as e:
            logger.error(e)
            return False
