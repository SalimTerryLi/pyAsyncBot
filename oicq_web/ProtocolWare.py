# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .Bot import Bot


from typing import Dict, Any, Type

from .BotConfig import BotConfig
from .BotWare import BotWare
from .proto.Protocol import Protocol
from .commu.http import *
from .commu.websocket import *


class ProtocolWare:
    _bot: Bot
    _botware: BotWare
    _commus: Dict[str, CommunicationBackend]
    _protocol: Protocol
    _commu_tasks: typing.List[asyncio.Task]

    def __init__(self, bot_conf: BotConfig, bot: Bot):
        self._bot = bot
        self._botware = BotWare(bot, self)
        self._commu_tasks = []
        # create bot protocol obj from bot protocol string
        if bot_conf.bot_protocol == 'MyBotProtocol':
            from .proto.MyBotProtocol import MyBotProtocol as BotProtocol
        else:
            raise Exception('no supported bot protocol found')
        self._protocol = BotProtocol(self)
        # create required communication channels gained from bot protocol class
        self._commus = {}
        required_commus = self._protocol.required_communication()
        if 'http_client' in required_commus:
            self._commus['http_client'] = HTTPClient(bot_conf.http_setting.remote_addr,
                                                     bot_conf.http_setting.remote_port)
            required_commus.remove('http_client')
        if 'ws_client' in required_commus:
            # a simple 'break' point for convenience
            while True:
                # check if http client shares the same endpoint configuration as ws client
                if (bot_conf.http_setting.remote_addr == bot_conf.ws_setting.remote_addr
                        and bot_conf.http_setting.remote_port == bot_conf.ws_setting.remote_port):
                    # then make sure http client exists
                    if 'http_client' in self._commus:
                        # create ws on top of http
                        self._commus['ws_client'] = WebSocketClient.from_http_client(self._commus['http_client'])
                        required_commus.remove('ws_client')
                        break
                # create from parameter and let ws manage http base
                self._commus['ws_client'] = WebSocketClient.from_parameters(
                    bot_conf.ws_setting.remote_addr,
                    bot_conf.ws_setting.remote_port
                )
                required_commus.remove('ws_client')
                break
        # TODO: other communication backends
        if len(required_commus) != 0:
            raise Exception('required communication backends {backend} not supported, required by {proto}'.format(
                proto=str(required_commus),
                backend=bot_conf.bot_protocol,
            ))

    async def setup(self) -> bool:
        if 'http_client' in self._commus:
            if not await self._commus['http_client'].setup():
                print('failed to setup http_client')
                return False
        if 'ws_client' in self._commus:
            if not await self._commus['ws_client'].setup():
                print('failed to setup ws_client')
                return False
        return True

    async def cleanup(self):
        if 'ws_client' in self._commus:
            await self._commus['ws_client'].cleanup()
            del self._commus['ws_client']
        if 'http_client' in self._commus:
            await self._commus['http_client'].cleanup()
            del self._commus['http_client']

    async def run(self):
        for comm in self._commus:
            self._commu_tasks.append(self._bot._create_bot_task(
                self._commus[comm].run_daemon(),
                '{comm}_listen'.format(comm=comm)
            ))
        if not await self._protocol.setup(self._commus):
            self.request_stop()
            return
        if not await self._protocol.probe():
            self.request_stop()
            return
        await asyncio.gather(*self._commu_tasks)
        await self._protocol.cleanup()

    def request_stop(self):
        for task in self._commu_tasks:
            task.cancel()
