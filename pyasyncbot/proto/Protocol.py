# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass

import typing
from abc import ABC

from ..FrameworkWrapper import ProtocolWrapper, BotWrapper


class Protocol(ProtocolWrapper, ABC):
    """
    Bot framework protocol layer.

    Use self._bot_wrapper to interact with bot framework

    Implement those abstract functions from ProtocolWrapper to provide corresponding functionalities, in the flat manner
    """

    def __init__(self, bot_wrapper: BotWrapper):
        self._bot_wrapper: BotWrapper = bot_wrapper
        pass

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
