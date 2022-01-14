# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..ProtocolWare import ProtocolWare

import typing


class Protocol:
    _protocolware: ProtocolWare

    def __init__(self, protocolware: ProtocolWare):
        self._protocolware = protocolware

    @staticmethod
    def required_communication() -> typing.List[str]:
        """
        Override this function and return a list of required low level communication channel so that
        ProtocolWare will later assign to when creating instances

        Supported commus:

        - http_client
        - ws_client
        - http_server (TODO)
        - ws_server (TODO)
        - SocketIO (TODO)

        :return: a list of names
        """
        pass

    async def setup(self) -> bool:
        """
        Override this function to do some base setup right after communication channel is up

        :return:
        """
        pass

    async def cleanup(self):
        """
        Override this one to do cleanup right before communication closed

        :return:
        """
        pass

    async def probe(self) -> bool:
        """
        Override this one to do testing and detection if required by protocol design

        :return: True if probed successfully, otherwise false
        """
        pass

    def process_incoming_data(self, data: typing.Dict[str, typing.Any]):
        """
        Override this function to receive push messages from corresponding channel (if exist)

        May need to setup new tasks on each message

        :param data: a dict {channel_type: payload_data}
        :return:
        """
        pass

    async def send_outgoing_data(self, data: typing.Dict[str, typing.Any]):
        """
        Call this function to send requests to remote endpoint
        DO NOT OVERRIDE

        :param data: a dict {channel_type: payload_data}
        :return:
        """
        return await self._protocolware._deliver_data_to_backend(data)

    def create_task(self, coro: typing.Callable[[], typing.Awaitable], name: str):
        """
        Call this to start a new task with given co-routine

        :param name: task name
        :param coro: task coroutine
        """
        self._protocolware._bot._async_loop.create_task(coro, name=name)
