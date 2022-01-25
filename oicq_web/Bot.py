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
    __task_set: typing.Set[asyncio.Task]

    # registered callbacks
    _on_private_msg: typing.Callable[[ReceivedMessage], typing.Awaitable[None]] = None
    _on_group_msg: typing.Callable[[ReceivedMessage], typing.Awaitable[None]] = None

    def __init__(self, conf: BotConfig):
        """
        Create a bot client object

        BotProtocol must be specified and the communication channel parameters should be filled
        according to the protocol in use

        :param conf: bot config
        """
        self._protoware = ProtocolWare(conf, self)
        self._async_loop = None
        self.__task_set = set()

    def __del__(self):
        pass

    def get_event_loop(self) -> asyncio.AbstractEventLoop:
        """
        Get the asyncio event loop that the bot is running on

        :return: event loop obj
        """
        return self._async_loop

    def _create_bot_task(self, coro: typing.Awaitable, name: str):
        """
        Create a task which is monitored by the bot. Bot will exit only if those tasks are exited.

        :param coro: co-routine
        :param name: task name
        """
        return self._async_loop.create_task(self.__create_bot_task_coro(coro), name=name)

    async def __create_bot_task_coro(self, coro: typing.Awaitable):
        self.__task_set.add(asyncio.current_task(self._async_loop))
        ret = await coro
        self.__task_set.remove(asyncio.current_task(self._async_loop))
        return ret

    def run_as_daemon(self):
        """
        Block and run the bot client. Will return when bot exit.

        This is an all-in-one function which will also take control of the event loop.
        Suitable for simple application which do not require a foreign event loop.
        Also suitable for multi-threaded condition, but it is not recommended.
        """
        self._async_loop = asyncio.get_event_loop()
        return self._async_loop.run_until_complete(self.run_as_task())

    async def run_as_task(self):
        """
        Block and run the bot client in the task context. Will return when bot exit.

        You'd probably want to setup a new task for this coro and monitor its lifecycle to determine whether
        bot exited or not.
        """
        self._async_loop = asyncio.get_running_loop()
        main_task = self._async_loop.create_task(self._run(), name='main task')
        print('main task emitted')
        ret = await main_task
        print('main task exited. wait for {d} of sub-tasks to complete'.format(d=len(self.__task_set)))
        await asyncio.gather(*self.__task_set)
        print('all tasks exited')
        return ret

    def request_stop(self):
        """
        Notify the bot to exit

        Will only stop the daemon, but not touching any sub-tasks launched by daemon.
        Assume those tasks will exit properly by themself
        """
        self._async_loop.call_soon_threadsafe(self._protoware.request_stop)

    async def _run(self):
        if await self._protoware.setup():
            await self._protoware.run()
        await self._protoware.cleanup()

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
