# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .Bot import Bot

import base64
import datetime
import typing
from typing import List
from dataclasses import dataclass

import aiofiles


class MessageSegment:
    def _gen_json_dict(self):
        pass

    @classmethod
    def _parse_from_dict(cls, obj):
        pass


class TextSegment(MessageSegment):
    """
    Part of a message where continuous characters belong to
    """
    _text: str

    def __init__(self):
        self._text = ''

    @classmethod
    def from_text(cls, text: str):
        """
        Create a text segment from given text

        :param text: text message
        :return: a text segment
        """
        if len(text) > 0:
            ret = TextSegment()
            ret._text = text
            return ret
        raise Exception('Empty string')

    def get_text(self) -> str:
        """
        Get the stored text content

        :return: text str
        """
        return self._text

    def __str__(self):
        return self._text


class ImageSegment(MessageSegment):
    """
    Part of a message where there is an image
    """
    _base64: str
    _url: str

    def __init__(self):
        self._base64 = ''
        self._url = ''

    @classmethod
    def from_base64(cls, base64: str):
        """
        Create an image segment from base64 encoded string buffer

        :param base64: image file content in base64 encoding
        :return: an image segment
        """
        ret = ImageSegment()
        ret._base64 = base64
        return ret

    @classmethod
    async def from_file(cls, filename: str):
        """
        Create an image segment from local filesystem

        :param filename: path of file
        :return: an image segment
        """
        try:
            ret = ImageSegment()
            with aiofiles.open(filename, mode='rb') as f:
                ret._base64 = base64.b64encode(await f.read()).decode('ascii')
            return ret
        except Exception as e:
            raise e

    @classmethod
    def from_url(cls, url: str):
        """
        Create an image segment from url

        :param url: url of image
        :return: an image segment
        """
        ret = ImageSegment()
        ret._url = url
        return ret

    def get_url(self) -> str:
        return self._url

    def __str__(self):
        return '[IMAGE:...]'


class EmojiSegment(MessageSegment):
    """
    Part of a message where a single emoji exists
    """
    _id: int
    _replacement: str

    def __init__(self):
        self._id = None
        self._replacement = None

    @classmethod
    def from_id(cls, eid: int, hint: str = ''):
        """
        Create an emoji from given id

        :param hint: describe the emoji
        :param eid: emoji id
        :return: a text segment
        """
        ret = EmojiSegment()
        ret._id = eid
        ret._replacement = hint
        return ret

    def __str__(self):
        return '[EMOJI:{text}]'.format(text=self._replacement)


class MentionSegment(MessageSegment):
    """
    Part of a message where an @xxx exists
    """
    _target: int
    _replacement: str

    def __init__(self):
        self._target = None
        self._replacement = None

    @classmethod
    def from_id(cls, uid: int, display_text: str = ''):
        """
        Create a mention from given uid

        :param display_text: the displayed text
        :param uid: user id
        :return: a text segment
        """
        ret = MentionSegment()
        ret._target = uid
        ret._replacement = display_text
        return ret

    def __str__(self):
        return self._replacement


class GroupedSegment(MessageSegment):
    """
    Part of a message where continuous characters belong to
    """

    class ContextFreeMessage(typing.TypedDict):
        id: int
        nickname: str
        time: datetime.datetime
        content: MessageContent

    def __init__(self):
        self._grouped_msg_id: str = None

    @classmethod
    def from_grouped_msg_id(cls, grouped_msg_id: str):
        """
        Create grouped message from given id

        :param grouped_msg_id: grouped message id
        :return: a text segment
        """
        ret = GroupedSegment()
        ret._grouped_msg_id = grouped_msg_id
        return ret

    async def from_msgids(self, bot: Bot, msgids: typing.List[str]):
        """
        Create grouped message from given message ids

        :param bot: bot context
        :param msgids: a list of msgIDs
        :return:
        """
        pass

    async def from_raw_messages(self, bot: Bot, msgs: typing.List[ContextFreeMessage]):
        """
        Create grouped message from stretch

        :param bot: bot context
        :param msgs: a list of InGroupMessage
        :return:
        """
        pass

    async def get_contents(self, bot: Bot) -> typing.List[ContextFreeMessage]:
        """
        Fetch the actual contents of this grouped message

        :param bot: bot context
        :return: a list of context-free messages
        """
        return await bot._contacts._proto_wrapper.query_packed_msg(self._grouped_msg_id)

    def __str__(self):
        return '[Grouped:{id}]'.format(id=self._grouped_msg_id)


class ApplicationSegment(MessageSegment):
    """
    Advanced segment which is defined by bot protocol
    """

    def __init__(self):
        self._base: str = None
        self._type: str = None
        self._data: typing.Any = None
        self._bref: str = None

    def __str__(self):
        return 'APPMSG[{type}:{bref}]'.format(type=self._type, bref=self._bref)

    @classmethod
    def from_data(cls, base: str, type: str, data, bref: str = ''):
        ret = ApplicationSegment()
        ret._type = type
        ret._data = data
        ret._bref = bref
        return ret

    def get_type(self):
        return self._type

    def get_data(self):
        return self._data


class MessageContent:
    """
    Context-free message container

    Accept text message as constructor parameter to quickly create a pure text message
    """
    _msgs: List[MessageSegment]

    def __init__(self, text: str = None):
        self._msgs = []
        if text is not None:
            self._msgs.append(TextSegment.from_text(text))

    def append_segment(self, seg: typing.Union[MessageSegment, str]):
        """
        Append a new message segment to the content tail.

        Allow directly pass in a string to create a text segment

        :param seg: message segment
        """
        if isinstance(seg, MessageSegment):
            self._msgs.append(seg)
        else:
            self._msgs.append(TextSegment.from_text(seg))

    def get_segments(self):
        return self._msgs

    def __str__(self):
        result = ""
        for msg in self._msgs:
            result += str(msg)
        return result


@dataclass
class RepliedMessageContent:
    to_uid: int
    time: datetime.datetime
    text: str
    to_msgid: str

    def __str__(self):
        return str({
            'to': self.to_uid,
            'msgid': self.to_msgid,
            'time': str(self.time),
            'text': self.text
        })
