# -*- coding: utf-8 -*-
import datetime

from ..ProtocolWare import ProtocolWare
from ..commu.http import HTTPClientAPI
from ..Message import MessageContent, RepliedMessage, TextSegment, ImageSegment, EmojiSegment, MentionSegment, GroupedSegment

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
        if msgdata['type'] == 'private':
            reply: typing.Union[RepliedMessage, None] = None
            if 'reply' in msgdata:
                reply = MyBotProtocol.parse_reply_content(msgdata['reply'])
            await self._botware.deliver_private_msg(
                time=datetime.datetime.fromtimestamp(msgdata['time']),
                sender_id=msgdata['sender'],
                msgid=msgdata['msgID'],
                msgcontent=MyBotProtocol.parse_msg_content(msgdata['msgContent']),
                is_friend=msgdata['known'],
                from_channel=msgdata['channel'],
                reply=reply
            )
        elif msgdata['type'] == 'group':
            reply: typing.Union[RepliedMessage, None] = None
            if 'reply' in msgdata:
                reply = MyBotProtocol.parse_reply_content(msgdata['reply'])
            await self._botware.deliver_group_msg(
                time=datetime.datetime.fromtimestamp(msgdata['time']),
                sender_id=msgdata['sender'],
                group_id=msgdata['channel'],
                msgid=msgdata['msgID'],
                msgcontent=MyBotProtocol.parse_msg_content(msgdata['msgContent']),
                is_anonymous=not msgdata['known'],
                reply=reply
            )
        else:
            print('unsupported msg.type: ' + msgdata['type'])

    @staticmethod
    def parse_msg_content(msg: list) -> MessageContent:
        ret = MessageContent()
        for seg in msg:
            if seg['type'] == 'text':
                ret.append_segment(TextSegment.from_text(seg['text']))
            elif seg['type'] == 'image':
                ret.append_segment(ImageSegment.from_url(seg['url']))
            elif seg['type'] == 'emoji':
                ret.append_segment(EmojiSegment.from_id(seg['id'], seg['replaceText']))
            elif seg['type'] == 'mention':
                ret.append_segment(MentionSegment.from_id(seg['target'], seg['displayText']))
            elif seg['type'] == 'forwarded':
                ret.append_segment(GroupedSegment.from_grouped_msg_id(seg['id']))
            else:
                print('unsupported msg segment: ' + seg['type'])
        return ret

    @staticmethod
    def parse_reply_content(reply_msg: dict) -> RepliedMessage:
        pass
