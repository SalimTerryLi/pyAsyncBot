# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..ProtocolWare import ProtocolWare
    from ..BotWare import BotWare
    from ..commu.CommunicationBackend import CommunicationBackend
    from ..Message import GroupedSegment

import typing


class Protocol:
    _protocolware: ProtocolWare
    _botware: BotWare

    def __init__(self, protocolware: ProtocolWare):
        self._protocolware = protocolware
        self._botware = protocolware._botware

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

    async def setup(self, commu: typing.Dict[str, typing.Any]) -> bool:
        """
        Override this function to do some base setup right after communication channel is up

        Also get communication handlers here so that event handlers can be bound here

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

    async def query_packed_msg(self, id: str) -> GroupedSegment.ContextFreeMessage:
        """
        Override this function to implement content querying of packed message

        :param id: packed msgid
        :return: context-free message obj
        """
        pass

    def create_task(self, coro: typing.Awaitable, name: str):
        """
        Call this to start a new task with given co-routine

        :param name: task name
        :param coro: task coroutine
        """
        self._protocolware._bot._async_loop.create_task(coro, name=name)
