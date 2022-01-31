# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .Bot import Bot

from loguru import logger
import typing

from .BotConfig import BotConfig
from .commu.http import *
from .commu.websocket import *


class CommunicationWare:
    _commus: typing.Dict[str, CommunicationBackend]
    _commu_tasks: typing.Set[asyncio.Task]

    def __init__(self):
        self._commus = dict()
        self._commu_tasks = set()

    async def setup(self, reqs: typing.List[str], bot_conf: BotConfig) -> typing.Dict[str, typing.Any]:
        if 'http_client' in reqs:
            # create http client
            self._commus['http_client'] = HTTPClient(bot_conf.http_setting.remote_addr,
                                                     bot_conf.http_setting.remote_port)
            reqs.remove('http_client')
        if 'ws_client' in reqs:
            # a simple 'break' point for convenience
            while True:
                # check if http client shares the same endpoint configuration as ws client
                if (bot_conf.http_setting.remote_addr == bot_conf.ws_setting.remote_addr
                        and bot_conf.http_setting.remote_port == bot_conf.ws_setting.remote_port):
                    # then make sure http client exists
                    if 'http_client' in self._commus:
                        # create ws on top of http
                        self._commus['ws_client'] = WebSocketClient.from_http_client(self._commus['http_client'])
                        reqs.remove('ws_client')
                        break
                # create from parameter and let ws manage http base
                self._commus['ws_client'] = WebSocketClient.from_parameters(
                    bot_conf.ws_setting.remote_addr,
                    bot_conf.ws_setting.remote_port
                )
                reqs.remove('ws_client')
                break
        # TODO: other communication backends
        if len(reqs) != 0:
            raise Exception('required communication backends {backend} not supported, required by {proto}'.format(
                proto=str(reqs),
                backend=bot_conf.bot_protocol,
            ))

        ret: typing.Dict[str, typing.Any] = dict()
        if 'http_client' in self._commus:
            try:
                ret['http_client'] = await self._commus['http_client'].setup()
            except CommunicationBackend.SetupFailed as e:
                logger.error('failed to setup http_client')
                await self.cleanup()
                raise e
        if 'ws_client' in self._commus:
            try:
                ret['ws_client'] = await self._commus['ws_client'].setup()
            except CommunicationBackend.SetupFailed as e:
                logger.error('failed to setup ws_client')
                await self.cleanup()
                raise e
        return ret

    async def cleanup(self):
        if 'ws_client' in self._commus:
            await self._commus['ws_client'].cleanup()
            del self._commus['ws_client']
        if 'http_client' in self._commus:
            await self._commus['http_client'].cleanup()
            del self._commus['http_client']

    async def run(self):
        for comm in self._commus:
            # Those tasks doesn't need to be monitored by bot, as they will always block the main task
            self._commu_tasks.add(asyncio.get_running_loop().create_task(
                self._commus[comm].run_daemon(),
                name='{comm}_daemon'.format(comm=comm)
            ))
        await asyncio.gather(*self._commu_tasks)

    def request_stop(self):
        for task in self._commu_tasks:
            task.cancel()
