# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

from loguru import logger
import ujson

from ..commu.http import HTTPClientAPI
from ..Message import *
from .Protocol import Protocol, BotWrapper


class MyBotProtocol(Protocol):
    _http_hdl: HTTPClientAPI

    def __init__(self, bot_wrapper: BotWrapper):
        super().__init__(bot_wrapper)
        self._http_hdl = None

    @staticmethod
    def required_communication() -> typing.List[str]:
        return [
            'http_client',
            'ws_client'
        ]

    async def setup(self, commu: typing.Dict[str, typing.Any]):
        self._http_hdl = commu['http_client']
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
                logger.info('remote version: {v}'.format(v=data['version']))
                return True
        return False

    def process_incoming_ws_data(self, data: str):
        try:
            msg_dict = ujson.loads(data)
            if msg_dict['type'] == 'msg':
                self._bot_wrapper.create_task(self.parse_msg(msg_dict['data']), 'push_event_worker')
            elif msg_dict['type'] == 'revoke':
                self._bot_wrapper.create_task(self.parse_revoke(msg_dict['data']), 'push_event_worker')
        except ValueError as e:
            logger.error(e)

    async def parse_msg(self, msgdata: dict):
        if msgdata['type'] == 'private':
            reply: typing.Union[RepliedMessageContent, None] = None
            if 'reply' in msgdata:
                reply = MyBotProtocol.parse_reply_content(msgdata['reply'])
            await self._bot_wrapper.deliver_private_msg(
                time=datetime.datetime.fromtimestamp(msgdata['time']),
                sender_id=msgdata['sender'],
                sender_nick=msgdata['sender_nick'],
                msgid=msgdata['msgID'],
                msgcontent=MyBotProtocol.parse_msg_content(msgdata['msgContent']),
                is_friend=msgdata['known'],
                from_channel=msgdata['channel'],
                from_channel_name=msgdata['channel_name'],
                reply=reply
            )
        elif msgdata['type'] == 'group':
            reply: typing.Union[RepliedMessageContent, None] = None
            if 'reply' in msgdata:
                reply = MyBotProtocol.parse_reply_content(msgdata['reply'])
            await self._bot_wrapper.deliver_group_msg(
                time=datetime.datetime.fromtimestamp(msgdata['time']),
                sender_id=msgdata['sender'],
                sender_nick=msgdata['sender_nick'],
                group_id=msgdata['channel'],
                group_name=msgdata['channel_name'],
                msgid=msgdata['msgID'],
                msgcontent=MyBotProtocol.parse_msg_content(msgdata['msgContent']),
                is_anonymous=not msgdata['known'],
                reply=reply
            )
        else:
            logger.error('unsupported msg.type: ' + msgdata['type'])

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
            elif seg['type'] == 'json':
                ret.append_segment(ApplicationSegment.from_data('qq', 'json', seg['data'], 'json消息'))
            elif seg['type'] == 'xml':
                ret.append_segment(ApplicationSegment.from_data('qq', 'xml', seg['data'], 'xml消息'))
            else:
                logger.error('unsupported msg segment: ' + seg['type'])
        return ret

    @staticmethod
    def parse_reply_content(reply_msg: dict) -> RepliedMessageContent:
        ret = RepliedMessageContent(
            to_uid=reply_msg['to'],
            time=datetime.datetime.fromtimestamp(reply_msg['time']),
            text=reply_msg['summary'],
            to_msgid=reply_msg['id']
        )
        return ret

    async def parse_revoke(self, data: dict):
        if data['type'] == 'private':
            await self._bot_wrapper.deliver_private_revoke(
                time=datetime.datetime.fromtimestamp(data['time']),
                revoker_id=data['revoker'],
                channel=data['channel'],
                msgid=data['msgID'],
                is_friend=data['known']
            )
        elif data['type'] == 'group':
            await self._bot_wrapper.deliver_group_revoke(
                time=datetime.datetime.fromtimestamp(data['time']),
                revoker_id=data['revoker'],
                group=data['channel'],
                msgid=data['msgID'],
                is_anonymous=not data['known']
            )
        else:
            logger.error('unsupported revoke.type: ' + data['type'])

    # below are abstract interfaces from protocol wrapper

    async def query_packed_msg(self, id: str) -> GroupedSegment.ContextFreeMessage:
        """
        Override this function to implement content querying of packed message

        :param id: packed msgid
        :return: context-free message obj
        """
        pass

    async def get_friend_list(self) -> typing.Dict[int, str]:
        """
        Override this function to provide friend list content. Normally not need to do cache here.

        :return: a list of user ids
        """
        resp = await self._http_hdl.get('/user/getFriendList')
        if 'application/json' in resp.content_type:
            data = ujson.loads(await resp.text())
            if data['status']['code'] == 0:
                ret = dict()
                for friend in data['list']:
                    ret[friend['id']] = friend['nickname']
                return ret
            else:
                raise Exception('remote returned status ' + data['status']['code'] + 'on /user/getFriendList')
        raise Exception('unexpected result from /user/getFriendList')

    async def get_group_list(self) -> typing.Dict[int, str]:
        """
        Override this function to provide group list content. Normally not need to do cache here.

        :return: a list of group ids
        """
        resp = await self._http_hdl.get('/user/getGroupList')
        if 'application/json' in resp.content_type:
            data = ujson.loads(await resp.text())
            if data['status']['code'] == 0:
                ret = dict()
                for group in data['list']:
                    ret[group['id']] = group['name']
                return ret
            else:
                raise Exception('remote returned status ' + data['status']['code'] + 'on /user/getGroupList')
        raise Exception('unexpected result from /user/getGroupList')

    async def get_group_members(self, id: int) -> typing.Dict[int, str]:
        """
        Get the group member list

        :param id: group id
        """
        resp = await self._http_hdl.get('/group/getMemberList', params={'group': id})
        if 'application/json' in resp.content_type:
            data = ujson.loads(await resp.text())
            if data['status']['code'] == 0:
                ret = dict()
                for member in data['list']:
                    if member['alias'] == '':
                        ret[member['id']] = member['nickname']
                    else:
                        ret[member['id']] = member['alias']
                return ret
            else:
                raise Exception('remote returned status ' + data['status']['code'] + 'on /user/getGroupList')
        raise Exception('unexpected result from /user/getGroupList')
