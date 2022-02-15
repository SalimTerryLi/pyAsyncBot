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
from ..Event import *
from ..FrameworkWrapper import PrivateMessageContext, GroupMessageContext, Channel


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
            if data['name'] == 'oicq2-webapid':
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
            elif msg_dict['type'] == 'user':
                self._bot_wrapper.create_task(self.parse_user_event(msg_dict['data']), 'push_event_worker')
            elif msg_dict['type'] == 'group':
                self._bot_wrapper.create_task(self.parse_group_event(msg_dict['data']), 'push_event_worker')
            else:
                logger.warning('Unsupported packet type: ' + msg_dict['type'])
        except ValueError as e:
            logger.error(e)

    async def parse_msg(self, msgdata: dict):
        reply: typing.Union[RepliedMessageContent, None] = None
        if 'reply' in msgdata:
            reply = MyBotProtocol.parse_reply_content(msgdata['reply'])
        if msgdata['type'] == 'private':
            await self._bot_wrapper.deliver_private_msg(PrivateMessageContext(
                time=datetime.datetime.fromtimestamp(msgdata['time']),
                sender_id=msgdata['sender'],
                sender_nick=msgdata['sender_nick'],
                channel_id=msgdata['channel'],
                channel_nick=msgdata['channel_name'],
                msgid=msgdata['msgID'],
                msgcontent=MyBotProtocol.parse_msg_content(msgdata['msgContent']),
                summary=msgdata['msgString'],
                is_friend=msgdata['known'],
                from_channel=msgdata['ref_channel'],
                from_channel_name=msgdata['ref_channel_name'],
                reply=reply
            ))
        elif msgdata['type'] == 'group':
            await self._bot_wrapper.deliver_group_msg(GroupMessageContext(
                time=datetime.datetime.fromtimestamp(msgdata['time']),
                sender_id=msgdata['sender'],
                sender_nick=msgdata['sender_nick'],
                group_id=msgdata['channel'],
                group_name=msgdata['channel_name'],
                msgid=msgdata['msgID'],
                msgcontent=MyBotProtocol.parse_msg_content(msgdata['msgContent']),
                summary=msgdata['msgString'],
                is_anonymous=not msgdata['known'],
                reply=reply
            ))
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

    @staticmethod
    def generate_message_content(msg_content: MessageContent) -> list:
        ret = []
        for msg in msg_content._msgs:
            if isinstance(msg, TextSegment):
                ret.append({
                    'type': 'text',
                    'text': msg._text
                })
            elif isinstance(msg, ImageSegment):
                seg = {'type': 'image'}
                if msg._url != '':
                    seg['url'] = msg._url
                else:
                    seg['base64'] = msg._base64
                ret.append(seg)
            elif isinstance(msg, EmojiSegment):
                ret.append({
                    'type': 'emoji',
                    'id': msg._id
                })
            elif isinstance(msg, MentionSegment):
                ret.append({
                    'type': 'mention',
                    'target': msg._target
                })
            elif isinstance(msg, GroupedSegment):
                ret.append({
                    'type': 'forwarded',
                    'id': msg._grouped_msg_id
                })
            elif isinstance(msg, ApplicationSegment):
                ret.append({
                    'type': msg._type,
                    'data': msg._data
                })
            else:
                logger.error('unsupported msg segment: ' + str(type(msg)))
        return ret

    @staticmethod
    def generate_reply_content(replied_content: RepliedMessageContent) -> dict:
        if replied_content is None:
            return None
        return {
            'to': replied_content.to_uid,
            'time': replied_content.time.timestamp(),
            'id': replied_content.to_msgid,
            'summary': replied_content.text
        }

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

    async def parse_user_event(self, data: dict):
        if data['type'] == 'online':
            await self._bot_wrapper.process_bot_online_event()
        elif data['type'] == 'offline':
            await self._bot_wrapper.process_bot_offline_event()
        elif data['type'] == 'newFriendRequest':
            refsrc = None
            if data['source'] != 0:
                refsrc = data['source']
            await self._bot_wrapper.process_new_friend_request_event(data['who'], data['nick'], data['comment'], data['eventID'], refsrc)
        elif data['type'] == 'groupInvite':
            await self._bot_wrapper.process_group_invitation_event(data['group'], data['groupName'], data['inviter'], data['eventID'])
        elif data['type'] == 'friendAdded':
            await self._bot_wrapper.process_friend_added_event(data['who'], data['nick'])
        elif data['type'] == 'friendRemoved':
            await self._bot_wrapper.process_friend_removed_event(data['who'], data['nick'])
        elif data['type'] == 'groupJoined':
            await self._bot_wrapper.process_group_added_event(data['which'], data['name'])
        elif data['type'] == 'groupLeft':
            kicker = None
            if data['operator'] != 0:
                kicker = data['operator']
            await self._bot_wrapper.process_group_removed_event(data['which'], data['name'], kicker)
        else:
            logger.warning('unsupported user event type: ' + data['type'])

    async def parse_group_event(self, data: dict):
        if data['type'] == 'joinRequest':
            inviter = None
            if 'inviter' in data:
                inviter = data['inviter']
            await self._bot_wrapper.process_group_member_join_request_event(data['who'], data['group'], data['comment'], data['eventID'], inviter)
        elif data['type'] == 'mute':
            await self._bot_wrapper.process_group_mute_event(data['group'], data['who'], data['duration'])
        elif data['type'] == 'admin':
            await self._bot_wrapper.process_group_admin_change_event(data['group'], data['who'], data['status'])
        elif data['type'] == 'memberJoined':
            await self._bot_wrapper.process_group_member_added_event(data['who'], data['nick'], data['group'], data['group_name'])
        elif data['type'] == 'memberLeft':
            await self._bot_wrapper.process_group_member_removed_event(data['who'], data['group'], data['group_name'])
        else:
            logger.warning('unsupported group event type: ' + data['type'])

    # below are abstract interfaces from protocol wrapper

    async def get_bot_basic_info(self) -> typing.Tuple[int, str]:
        resp = await self._http_hdl.get('/user/basicInfo')
        if 'application/json' in resp.content_type:
            data = ujson.loads(await resp.text())
            if data['status']['code'] == 0:
                return data['basic']['id'], data['basic']['nick']
            else:
                raise Exception('remote returned status ' + data['status']['code'] + ' on /user/basicInfo')
        raise Exception('unexpected result from /user/basicInfo')

    async def query_packed_msg(self, id: str) -> typing.List[GroupedSegment.ContextFreeMessage]:
        resp = await self._http_hdl.get('/mesg/parseForwardedMsg', params={'id': id})
        if 'application/json' in resp.content_type:
            data = ujson.loads(await resp.text())
            if data['status']['code'] == 0:
                ret = []
                for msg in data['msgs']:
                    ret.append(GroupedSegment.ContextFreeMessage(
                        id=msg['id'],
                        time=msg['time'],
                        nickname=msg['nickname'],
                        content=MyBotProtocol.parse_msg_content(msg['msgContent'])
                    ))
                return ret
            else:
                raise Exception('remote returned status ' + data['status']['code'] + ' on /mesg/parseForwardedMsg')
        raise Exception('unexpected result from /mesg/parseForwardedMsg')

    async def query_msg_by_id(self, channel_type: Channel.ChannelType, channel_id: int, msgid: str) -> Union[PrivateMessageContext, GroupMessageContext]:
        channel_type_str = ''
        if channel_type == Channel.ChannelType.P2P:
            channel_type_str = 'private'
        elif channel_type == Channel.ChannelType.MultiUser:
            channel_type_str = 'group'
        resp = await self._http_hdl.get('/mesg/queryMsg', params={'id': msgid, 'type': channel_type_str, 'channel': channel_id})
        if 'application/json' in resp.content_type:
            data = ujson.loads(await resp.text())
            if data['status']['code'] == 0:
                msgdata = data['data']
                reply: typing.Union[RepliedMessageContent, None] = None
                if 'reply' in msgdata:
                    reply = MyBotProtocol.parse_reply_content(msgdata['reply'])
                if msgdata['type'] == 'private':
                    return PrivateMessageContext(
                        time=datetime.datetime.fromtimestamp(msgdata['time']),
                        sender_id=msgdata['sender'],
                        sender_nick=msgdata['sender_nick'],
                        channel_id=msgdata['channel'],
                        channel_nick=msgdata['channel_name'],
                        msgid=msgdata['msgID'],
                        msgcontent=MyBotProtocol.parse_msg_content(msgdata['msgContent']),
                        summary=msgdata['msgString'],
                        is_friend=msgdata['known'],
                        from_channel=msgdata['ref_channel'],
                        from_channel_name=msgdata['ref_channel_name'],
                        reply=reply
                    )
                elif msgdata['type'] == 'group':
                    return GroupMessageContext(
                        time=datetime.datetime.fromtimestamp(msgdata['time']),
                        sender_id=msgdata['sender'],
                        sender_nick=msgdata['sender_nick'],
                        group_id=msgdata['channel'],
                        group_name=msgdata['channel_name'],
                        msgid=msgdata['msgID'],
                        msgcontent=MyBotProtocol.parse_msg_content(msgdata['msgContent']),
                        summary=msgdata['msgString'],
                        is_anonymous=not msgdata['known'],
                        reply=reply
                    )
            else:
                raise Exception('remote returned status ' + str(data['status']['code']) + ' on /mesg/queryMsg')
        raise Exception('unexpected result from /mesg/queryMsg')

    async def get_friend_list(self) -> typing.Dict[int, str]:
        resp = await self._http_hdl.get('/user/getFriendList')
        if 'application/json' in resp.content_type:
            data = ujson.loads(await resp.text())
            if data['status']['code'] == 0:
                ret = dict()
                for friend in data['list']:
                    ret[friend['id']] = friend['nickname']
                return ret
            else:
                raise Exception('remote returned status ' + str(data['status']['code']) + ' on /user/getFriendList')
        raise Exception('unexpected result from /user/getFriendList')

    async def get_group_list(self) -> typing.Dict[int, str]:
        resp = await self._http_hdl.get('/user/getGroupList')
        if 'application/json' in resp.content_type:
            data = ujson.loads(await resp.text())
            if data['status']['code'] == 0:
                ret = dict()
                for group in data['list']:
                    ret[group['id']] = group['name']
                return ret
            else:
                raise Exception('remote returned status ' + str(data['status']['code']) + ' on /user/getGroupList')
        raise Exception('unexpected result from /user/getGroupList')

    async def get_group_members(self, id: int) -> typing.Dict[int, str]:
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
                raise Exception('remote returned status ' + str(data['status']['code']) + ' on /user/getGroupList')
        raise Exception('unexpected result from /user/getGroupList')

    async def serv_private_message(self, id: int, msg_content: MessageContent, *, from_channel: int = None, reply: RepliedMessageContent = None) -> str:
        post_data = {
            'dest': id,
            'from': from_channel,
            'msgContent': self.generate_message_content(msg_content),
            'reply': self.generate_reply_content(reply)
        }
        if from_channel is None:
            del post_data['from']
        if reply is None:
            del post_data['reply']
        resp = await self._http_hdl.post('/sendMsg/private', ujson.dumps(post_data), headers={'content-type': 'application/json'})
        resp = ujson.loads(await resp.text())
        if resp['status']['code'] == 0:
            return resp['msgID']
        else:
            return None

    async def serv_group_message(self, id: int, msg_content: MessageContent, *, as_anonymous: bool = False, reply: RepliedMessageContent = None) -> str:
        post_data = {
            'dest': id,
            'msgContent': self.generate_message_content(msg_content),
            'reply': self.generate_reply_content(reply)
        }
        if reply is None:
            del post_data['reply']
        resp = await self._http_hdl.post('/sendMsg/group', ujson.dumps(post_data),
                                         headers={'content-type': 'application/json'})
        resp = ujson.loads(await resp.text())
        if resp['status']['code'] == 0:
            return resp['msgID']
        else:
            return None

    async def serv_private_revoke(self, id: int, msgid: str) -> bool:
        resp = await self._http_hdl.post('/revoke/private',
                                         ujson.dumps({
                                             'channel': id,
                                             'msgID': msgid,
                                         }),
                                         headers={'content-type': 'application/json'}
                                         )
        resp = ujson.loads(await resp.text())
        if resp['status']['code'] == 0:
            return True
        else:
            return False

    async def serv_group_revoke(self, id: int, msgid: str) -> bool:
        resp = await self._http_hdl.post('/revoke/group',
                                         ujson.dumps({
                                             'channel': id,
                                             'msgID': msgid,
                                         }),
                                         headers={'content-type': 'application/json'}
                                         )
        resp = ujson.loads(await resp.text())
        if resp['status']['code'] == 0:
            return True
        else:
            return False

    async def deal_friend_request(self, id: int, event_id: str, is_accept: bool) -> bool:
        resp = await self._http_hdl.post('/user/acceptFriend',
                                         ujson.dumps({
                                             'who': id,
                                             'eventID': event_id,
                                             'accept': is_accept
                                         }),
                                         headers={'content-type': 'application/json'}
                                         )
        resp = ujson.loads(await resp.text())
        if resp['status']['code'] == 0:
            return True
        else:
            return False

    async def deal_group_invitation(self, id: int, event_id: str, is_accept: bool) -> bool:
        resp = await self._http_hdl.post('/user/acceptGroupInvite',
                                         ujson.dumps({
                                             'who': id,
                                             'eventID': event_id,
                                             'accept': is_accept
                                         }),
                                         headers={'content-type': 'application/json'}
                                         )
        resp = ujson.loads(await resp.text())
        if resp['status']['code'] == 0:
            return True
        else:
            return False

    async def deal_group_member_join_request(self, gid: int, event_id: str, is_accept: bool) -> bool:
        resp = await self._http_hdl.post('/group/acceptJoin',
                                         ujson.dumps({
                                             'group': gid,
                                             'eventID': event_id,
                                             'accept': is_accept
                                         }),
                                         headers={'content-type': 'application/json'}
                                         )
        resp = ujson.loads(await resp.text())
        if resp['status']['code'] == 0:
            return True
        else:
            return False
