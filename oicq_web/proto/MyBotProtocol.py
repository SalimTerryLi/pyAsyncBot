# -*- coding: utf-8 -*-
from typing import TYPE_CHECKING

from ..ProtocolWare import ProtocolWare
from ..commu.http import HTTPClientAPI

import asyncio
import typing
import ujson
import aiohttp

from .Protocol import Protocol


class MyBotProtocol(Protocol):
    _http_hdl: HTTPClientAPI

    def __init__(self, protocolware: ProtocolWare):
        super().__init__(protocolware)
        self._http_hdl = None

    @staticmethod
    def required_communication() -> typing.List[str]:
        return [
            'http_client',
            'ws_client'
        ]

    async def setup(self, commu: typing.Dict[str, typing.Any]):
        self._http_hdl = commu['http_client'].get_http_client()
        commu['ws_client'].register_text_message_callback(self.process_incoming_ws_data)
        return True

    async def cleanup(self):
        self._http_hdl = None
        pass

    async def probe(self) -> bool:
        res = await self._http_hdl.get('')
        if 'application/json' in res.content_type:
            data = ujson.loads(await res.text())
            if data['name'] == 'oicq-webapi':
                print('remote version: {v}'.format(v=data['version']))
                return True
        return False

    def process_incoming_ws_data(self, data: str):
        try:
            msg_dict = ujson.loads(data)
            if msg_dict['type'] == 'msg':
                self.create_task(self.parse_msg(msg_dict['data']), 'msg_worker')
        except ValueError as e:
            print(e)

    async def parse_msg(self, msgdata: dict):
        pass
