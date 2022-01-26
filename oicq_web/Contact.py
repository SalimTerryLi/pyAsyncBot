# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .Message import MessageContent, SentMessage
    from .proto.Protocol import Protocol

from ujson import dumps
from typing import Union, Dict


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


class Contact:
    _proto: Protocol
    # lazy init of dicts
    _friends: Dict[int, Friend]
    _groups: Dict[int, Group]

    def __init__(self, protocol: Protocol):
        self._proto = protocol
        self._friends = None
        self._groups = None

    async def get_friend(self, id: int) -> Union[Friend, None]:
        """
        Query the friend object from given id

        :param id: user id
        :return: None if not found
        """
        if self._friends is None:
            self._friends = dict()
            for uid in await self._proto.get_friend_list():
                self._friends[uid] = Friend(uid)
        if id in self._friends:
            return self._friends[id]
        return None

    async def get_group(self, id: int) -> Union[Group, None]:
        """
        Query the group object from given id

        :param id: group id
        :return: None if not found
        """
        if self._groups is None:
            self._groups = dict()
            for gid in await self._proto.get_group_list():
                self._groups[gid] = Group(gid)
        if id in self._groups:
            return self._groups[id]
        return None
