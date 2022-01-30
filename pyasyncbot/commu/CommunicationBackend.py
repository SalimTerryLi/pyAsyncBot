# -*- coding: utf-8 -*-
import typing
from abc import ABC, abstractmethod


class CommunicationBackend(ABC):
    class SetupFailed(Exception):
        pass
    
    @abstractmethod
    async def setup(self) -> typing.Any:
        """
        Get called when the underlie backend requires setup.

        Raise SetupFailed exception if something going wrong

        :return: backend handle
        """
        pass

    @abstractmethod
    async def cleanup(self):
        pass

    @abstractmethod
    async def run_daemon(self):
        """
        Get called when the underlie backend should poll and wait for remote push message

        Should not return until received exit signal (such as the canceled exception)

        :param ev_loop: event loop passed from upper call
        """
        pass
