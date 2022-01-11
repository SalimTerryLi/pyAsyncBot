# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime
from typing import Union
from ujson import dumps

from .MsgContent import *
from .Contact import *


class RepliedMessage:
    """
    A small structure which contains information of a replied reference message.
    """

    def __init__(self):
        self._to: User = None
        self._time: datetime.datetime = None
        self._text: str = None
        self._id: str = None

    def __str__(self):
        return dumps({
            'user_id': str(self._to),
            'time': str(self._time),
            'summary': self._text,
            'msgID': self._id
        })

    def _gen_json_dict(self):
        return {
            'to': self._to.get_id(),
            'time': int(self._time.timestamp()),
            'summary': self._text,
            'id': self._id
        }

    @classmethod
    def _parse_from_dict(cls, data):
        ret = RepliedMessage()
        ret._id = data['reply']['id']
        ret._text = data['reply']['summary']
        ret._time = datetime.datetime.fromtimestamp(data['reply']['time'])
        if data['type'] == 'private':
            if data['known']:
                ret._to = Friend(data['reply']['to'])
            else:
                ret._to = Stranger(data['reply']['to'], data['channel'])
        elif data['type'] == 'group':
            if data['known']:
                ret._to = GroupMember(data['reply']['to'], data['channel'])
            else:
                ret._to = GroupAnonymousMember(data['reply']['to'], data['channel'])
        return ret


class ReceivedMessage:
    """
    Received message
    """

    def __init__(self):
        self._sender: Union[Friend, GroupMember] = None
        self._msgID: str = None
        self._msgContent: MessageContent = None
        self._reply: RepliedMessage = None

    def __str__(self):
        return dumps({
            'sender': str(self._sender),
            'msgID': self._msgID,
            'msgContent': str(self._msgContent),
            'reply_to': str(self._reply),
        })

    @classmethod
    def _deserialize(cls, data):
        ret = cls()
        if data['type'] == 'private':
            if data['known']:
                ret._sender = Friend(data['sender'])
            else:
                ret._sender = Stranger(data['sender'], data['channel'])
        elif data['type'] == 'group':
            if data['known']:
                ret._sender = GroupMember(data['sender'], data['channel'])
            else:
                ret._sender = GroupAnonymousMember(data['sender'], data['channel'])
        ret._msgID = data['msgID']
        ret._msgContent = MessageContent._parse_from_dict(data['msgContent'])
        if 'reply' in data:
            ret._reply = RepliedMessage._parse_from_dict(data)
        return ret

    def get_sender(self) -> Union[Friend, GroupMember]:
        """
        Get the sender of this message, either a friend or someone from a group

        :return: sender object
        """
        return self._sender

    def get_content(self) -> MessageContent:
        """
        Get the message content

        :return: a content object
        """
        return self._msgContent

    def get_msg_id(self) -> str:
        """
        Advanced: to get message ID

        :return: message id as string
        """
        return self._msgID

    def is_reply_msg(self) -> bool:
        """
        Check if this message did reply to previous one

        :return: boolean yes or no
        """
        return self._reply is None

    def get_replied_msgid(self):
        """
        Advanced: Get the message id of replied message

        :return: msgid
        """
        if not self._reply is None:
            return self._reply._id
        else:
            return None

    async def get_replied_msg(self) -> Union[ReceivedMessage, None]:
        """
        Get the original message this one is replied to.
        May fail due to the replied message is flushed out of chat history cache

        :return: content or None
        """
        if not self._reply is None:
            pass
        else:
            return None

    async def reply(self, content: MessageContent) -> Union[str, None]:
        """
        Reply to the channel which this message comes from

        :param content: message content
        :return: msgID of reply msg or None if failed
        """
        pass

    async def quoted_reply(self, content: MessageContent) -> Union[str, None]:
        """
        Reply to original message with its content summarized and quoted

        :param content: message content
        :return: msgID of reply msg or None if failed
        """
        pass
