# -*- coding: utf-8 -*-
import typing
from asyncio import AbstractEventLoop


class CommunicationBackend:
    async def setup(self, ev_loop: AbstractEventLoop) -> bool:
        """
        Get called when the underlie backend requires setup

        :return: whether succeed or not
        """
        return False

    async def cleanup(self, ev_loop: AbstractEventLoop):
        return

    async def run_daemon(self, ev_loop: AbstractEventLoop):
        """
        Get called when the underlie backend should poll and wait for remote push message

        Should not return until received exit signal (such as the canceled exception)

        :param ev_loop: event loop passed from upper call
        """
        return
