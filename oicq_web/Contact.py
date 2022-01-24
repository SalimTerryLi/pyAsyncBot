# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .Message import MessageContent, SentMessage

from ujson import dumps
from typing import Union


class Channel:
    async def send_msg(self, content: MessageContent) -> SentMessage:
        pass

    async def revoke_msg(self, msgid: str) -> bool:
        pass


class User(Channel):
    def __init__(self, uid: int):
        self._uid = uid

    def __eq__(self, other):
        if type(other) == User:
            return self._uid == other._uid
        elif type(other) == int:
            return self._uid == other
        return False

    def get_id(self):
        return self._uid


class Friend(User):
    def __init__(self, uid: int):
        super().__init__(uid)

    def __str__(self):
        return dumps({
            'type': 'Friend',
            'id': self.get_id(),
        }, ensure_ascii=False)


class Stranger(User):
    def __init__(self, uid: int, gid: int):
        super().__init__(uid)
        self._gid = gid

    def __str__(self):
        return dumps({
            'type': 'Stranger',
            'id': self.get_id(),
            'from_group_id': self._gid
        }, ensure_ascii=False)


class GroupMember(User):
    def __init__(self, uid: int, gid: int):
        super().__init__(uid)
        self._gid = gid

    def __str__(self):
        return dumps({
            'type': 'GroupMember',
            'group_id': self._gid,
            'sender_id': self.get_id(),
        }, ensure_ascii=False)


class GroupAnonymousMember(User):
    def __init__(self, uid: int, gid: int):
        super().__init__(uid)
        self._gid = gid

    def __str__(self):
        return dumps({
            'type': 'GroupAnonymousMember',
            'group_id': self._gid,
            'anonymous_id': self.get_id(),
        }, ensure_ascii=False)


class Group(Channel):
    def __init__(self, gid: int):
        self._gid = gid

    def __eq__(self, other):
        if type(other) == Group:
            return self._gid == other._gid
        elif type(other) == int:
            return self._gid == other
        return False
