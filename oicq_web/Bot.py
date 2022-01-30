# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass

import typing
import asyncio
import traceback
import sys

from .Message import ReceivedMessage
from .CommunicationWare import CommunicationWare
from .commu.CommunicationBackend import CommunicationBackend
from .FrameworkWrapper import BotWrapper
from .BotConfig import BotConfig
from .Contacts import Contacts
from .proto.Protocol import Protocol


class Bot:
    """
    Async Chat Bot Client for Python3
    """

    def __init__(self, conf: BotConfig):
        """
        Create a bot client object

        BotProtocol must be specified and the communication channel parameters should be filled
        according to the protocol in use

        :param conf: bot config
        """
        self._config: BotConfig = conf
        self._commuware: CommunicationWare = CommunicationWare()
        self._async_loop: asyncio.AbstractEventLoop = None      # Get filled run-timely
        self.__task_set: typing.Set[asyncio.Task] = set()
        self._contacts = None                                   # Get filled run-timely

        # registered callbacks
        self._on_private_msg_cb: typing.Callable[[ReceivedMessage], typing.Awaitable[None]] = None
        self._on_group_msg_cb: typing.Callable[[ReceivedMessage], typing.Awaitable[None]] = None

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
        # add some wrapper to monitor the state of those sub tasks
        self.__task_set.add(asyncio.current_task(self._async_loop))
        ret = 0
        try:
            ret = await coro
        except Exception:
            print('Exception from bot tasks:', file=sys.stderr)
            traceback.print_exc()
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
        print('main task started')
        ret = await self._run()
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
        self._async_loop.call_soon_threadsafe(self._commuware.request_stop)

    async def _run(self):
        bot_protocol: Protocol = None
        # get bot_protocol instance based on configuration
        if self._config.bot_protocol == 'MyBotProtocol':
            from .proto.MyBotProtocol import MyBotProtocol
            bot_protocol = MyBotProtocol(BotWrapper(self))
        else:
            print('unsupported bot protocol: ' + self._config.bot_protocol)
            return -1

        # initializing commuware with requested backends
        commus = dict()
        try:
            commus = await self._commuware.setup(bot_protocol.required_communication(), self._config)
        except CommunicationBackend.SetupFailed:
            print('failed to setup communication backend')
            return -2

        # doing bot protocol initialization that doesn't require run-time interaction
        if not await bot_protocol.setup(commus):
            print(self._config.bot_protocol + ' setup failed')
            await self._commuware.cleanup()
            return -3

        # bring up communication daemons
        commu_task = self._async_loop.create_task(self._commuware.run(), name='bot daemon')

        retval = 0
        # now commu backend is fully working, do protocol probe
        if not await bot_protocol.probe():
            print(self._config.bot_protocol + ' probe failed')
            # at this point we can do cleanup in normal routine
            self._commuware.request_stop()
            # but set retval
            retval = -4

        # bot protocol is ready, create protocol wrapper and initialize contacts
        self._contacts = Contacts(bot_protocol)

        # wait until the daemon task finished
        await commu_task

        # do cleanups
        await bot_protocol.cleanup()
        await self._commuware.cleanup()

        return retval

    def get_contacts(self) -> Contacts:
        """
        Get the contacts obj of this bot
        """
        return self._contacts

    def on_private_message(self, deco):
        """
        Register message callback for private channel
        """
        if self._on_private_msg_cb is not None:
            print('warning: overwrite _on_private_msg_cb')
        self._on_private_msg_cb = deco

    def on_group_message(self, deco):
        """
        Register message callback for private channel
        """
        if self._on_group_msg_cb is not None:
            print('warning: overwrite _on_group_msg_cb')
        self._on_group_msg_cb = deco
