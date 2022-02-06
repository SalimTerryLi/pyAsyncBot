# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .Contacts import *

import datetime
from typing import Union
import ast

from .MsgContent import *


class RepliedMessage:
    """
    A small structure which contains information of a replied reference message.
    """

    def __init__(self, contacts: Contacts, content: RepliedMessageContent, ctx: ReceivedMessage):
        self._content = content
        self._contacts = contacts
        self._ctx = ctx

    def __str__(self):
        if self._content is None:
            return str(None)
        return str(self._content)

    def get_msgid(self):
        """
        Advanced: Get the message id of the message being replied

        :return: msgid
        """
        return self._content.to_msgid

    async def get_original_msg(self) -> Union[ReceivedMessage, None]:
        """
        Get the original message this one is replied to.

        May fail due to the replied message is flushed out of chat history, or it is a constructed one

        :return: content or None
        """
        pass

    async def get_sender(self) -> Union[Friend, GroupMember, Stranger, GroupAnonymousMember]:
        """
        Get the sender of the message being replied

        :return: sender
        """
        pass


class ReceivedMessage:
    """
    Received message
    """

    def __init__(self, contacts):
        self.__contacts = contacts
        self._time: datetime.datetime = None
        self._channel: Union[Friend, Stranger, Group] = None
        self._sender: Union[Friend, Stranger, GroupMember, GroupAnonymousMember] = None
        self._msgID: str = None
        self._msgContent: MessageContent = None
        self._reply: RepliedMessage = None
        self._summary: str = None

    def __str__(self):
        return str({
            'time': str(self._time),
            'sender': str(self._sender),
            'channel': str(self._channel),
            'msgID': self._msgID,
            'msgContent': str(self._msgContent),
            'reply_to': str(self._reply),
        })

    def get_content(self) -> MessageContent:
        """
        Get the message content

        :return: a content object
        """
        return self._msgContent

    def get_msg_id(self) -> str:
        """
        Advanced: get message ID

        :return: message id as string
        """
        return self._msgID

    def get_replied(self) -> Union[RepliedMessage, None]:
        """
        Get the replied message obj. None if not exist

        :return: replied message obj
        """
        return self._reply

    async def reply(self, content: MessageContent) -> SentMessage:
        """
        Reply to the channel which this message comes from

        :param content: message content
        :return: sent msg obj or None if failed
        """
        return await self._channel.send_msg(content)

    async def quoted_reply(self, content: MessageContent) -> Union[str, None]:
        """
        Reply to original message with its content summarized and quoted

        :param content: message content
        :return: msgID of reply msg or None if failed
        """
        pass


class ReceivedPrivateMessage(ReceivedMessage):
    def __init__(self, contacts):
        super().__init__(contacts)
        self._ref_channel: Group = None

    def __str__(self):
        dictionary = ast.literal_eval(super().__str__())
        dictionary['ref_channel'] = str(self._ref_channel)
        return str(dictionary)

    def get_ref_channel(self) -> Union[Group, None]:
        """
        If the message is from a stranger, then the group he started the private channel can be fetched here.

        :return: Group or None
        """
        return self._ref_channel

    def get_channel(self) -> Union[Friend, Stranger]:
        """
        Get the channel this message comes from

        :return: channel obj
        """
        return self._channel

    def get_sender(self) -> Union[Friend, Stranger]:
        """
        Get the sender of this message

        :return: sender object
        """
        return self._sender
    

class ReceivedGroupMessage(ReceivedMessage):
    def get_channel(self) -> Group:
        """
        Get the group this message comes from

        :return: channel obj
        """
        return self._channel

    def get_sender(self) -> Union[GroupMember, GroupAnonymousMember]:
        """
        Get the sender of this message

        :return: sender object
        """
        return self._sender


class SentMessage:
    """
    A message that is sent by us
    """
    _msgid: str
    _channel: Channel

    def __init__(self):
        self._msgid = None
        self._channel = None

    async def revoke(self) -> bool:
        return await self._channel.revoke_msg(self._msgid)


class RevokedMessage:
    """
    Revoked Message
    """

    def __init(self):
        self._time: datetime.datetime = None
        self._msgid: str = None
        self._channel: Channel = None
        self._revoker: Union[Friend, Stranger, GroupMember, GroupAnonymousMember] = None

    def __str__(self):
        return str({
            'time': str(self._time),
            'channel': str(self._channel),
            'revoker': str(self._revoker),
            'msgid': self._msgid,
        })

    def get_channel(self) -> Channel:
        """
        Get the channel this message comes from

        :return: channel obj
        """
        return self._channel

    def get_revoker(self) -> User:
        """
        Get the one who revoked the message

        :return: user object
        """
        return self._revoker

    async def get_remoked_msg(self) -> ReceivedMessage:
        """
        Get the original message which was revoked

        May fail due to the replied message is flushed out of chat history

        :return: message object, None if failed to get
        """
        pass
