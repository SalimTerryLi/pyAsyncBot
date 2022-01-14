# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass

import typing
import asyncio

from .Message import ReceivedMessage
from .ProtocolWare import ProtocolWare
from .BotConfig import BotConfig


class Bot:
    """
    Async Bot client
    """

    _protoware: ProtocolWare
    _async_loop: asyncio.AbstractEventLoop

    # registered callbacks
    _on_private_msg: typing.Callable[[ReceivedMessage], typing.Awaitable[None]] = None
    _on_group_msg: typing.Callable[[ReceivedMessage], typing.Awaitable[None]] = None

    def __init__(self, conf: BotConfig):
        """
        Create a bot client object

        BorProtocol must be specified and the communication channel parameters should be filled
        according to the protocol in use

        :param conf: bot config
        """
        self._protoware = ProtocolWare(conf, self)
        self._async_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._async_loop)

    def __del__(self):
        self._async_loop.close()

    def run(self):
        """
        Block and run the bot client. Will return when bot exit
        """

        main_task = self._async_loop.create_task(self._run(), name='main task')
        print('main task emitted')
        ret = self._async_loop.run_until_complete(main_task)
        # find sub-tasks that are still running
        curr_tasks = asyncio.Task.all_tasks(loop=self._async_loop)
        curr_tasks = [x for x in curr_tasks if not x.done()]
        print('main task exited. wait for {d} of sub-tasks to complete'.format(d=len(curr_tasks)))
        self._async_loop.run_until_complete(asyncio.gather(*curr_tasks))
        print('all tasks exited')
        return ret

    def request_stop(self):
        """
        Notify the bot to exit, from outside async loop
        """
        # schedule stop
        self._async_loop.call_soon_threadsafe(self.__request_stop_cb)

    def __request_stop_cb(self):
        self._protoware.request_stop()

    async def _run(self):
        # run protocolware inside async loop to simplify its request stop logic (avoid call_soon_threadsafe())
        if await self._protoware.setup(self._async_loop):
            await self._protoware.run(self._async_loop)
        await self._protoware.cleanup(self._async_loop)

    def on_private_message(self, deco):
        """
        Register message callback for private channel
        """
        if self._on_private_msg is not None:
            print('warning: overwrite on_private_msg')
        self._on_private_msg = deco

    def on_group_message(self, deco):
        """
        Register message callback for group channel
        """
        if self._on_group_msg is not None:
            print('warning: overwrite on_group_msg')
        self._on_group_msg = deco
