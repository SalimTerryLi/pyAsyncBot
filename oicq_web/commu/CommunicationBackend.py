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

    async def await_message(self, ev_loop: AbstractEventLoop, callback: typing.Callable[[typing.Any],None], tag: str):
        """
        Get called when the underlie backend should poll and wait for remote push message

        Should not return until received exit signal (such as the canceled exception)

        :param ev_loop: event loop passed from upper call
        :param callback: deliver the received message to bot protocol using callback
        :param tag: mark the message source in multi-communication case
        """
        return

    async def send_message(self, data: typing.Any) -> typing.Any:
        """
        Get called when bot try to send something though this backend

        :param data: data
        :return: depends
        """
