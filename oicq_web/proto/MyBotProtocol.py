# -*- coding: utf-8 -*-
import asyncio
import typing
import ujson

from .Protocol import Protocol


class MyBotProtocol(Protocol):
    @staticmethod
    def required_communication() -> typing.List[str]:
        return [
            'http_client',
            'ws_client'
        ]

    async def setup(self):
        return True

    async def cleanup(self):
        pass

    async def probe(self) -> bool:
        res = await self.send_outgoing_data({
            'http_client': {
                'method': 'GET',
            }
        })
        if 'application/json' in res['content-type']:
            data = ujson.loads(res['data'].decode('utf8'))
            if data['name'] == 'oicq-webapi':
                print('remote version: {v}'.format(v=data['version']))
                return True
        return False

    def process_incoming_data(self, data: typing.Dict[str, typing.Any]):
        if 'ws_client' in data and data['ws_client']['type'] == 'text':
            print(data['ws_client']['data'])
            self.create_task(self.test(), 'test')
        else:
            print('unsupported: ' + str(data))

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
