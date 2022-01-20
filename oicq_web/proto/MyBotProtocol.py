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
        commu['ws_client'].register_text_message_callback(self.process_incoming_data)
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

    def process_incoming_data(self, data: str):
        print(data)
        self.create_task(self.test(), 'test')

    async def test(self):
        await asyncio.sleep(5)

    # launched in separate tasks in parallel
    async def _deal_ws_packets(self, data):
        try:
            json_data = ujson.loads(data)
            if json_data['type'] == 'msg':
                msg_data = json_data['data']
                msg = ReceivedMessage._deserialize(msg_data)
                if msg_data['type'] == 'private':
                    if self._on_private_msg is not None:
                        await self._on_private_msg(msg)
                elif msg_data['type'] == 'group':
                    if self._on_group_msg is not None:
                        await self._on_group_msg(msg)
                else:
                    print('warning: unsupported sub-type: {base}.{sub}'.format(
                        base=json_data['type'],
                        sub=msg_data['type']
                    ))
            elif json_data['type'] == 'revoke':
                pass
            elif json_data['type'] == 'user':
                pass
            elif json_data['type'] == 'group':
                pass
            else:
                print('warning: unsupported type {type}'.format(type=json_data['type']))
        except Exception as e:
            print(e)
