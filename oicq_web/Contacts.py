# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .Message import MessageContent, SentMessage
    from .FrameworkWrapper import ProtocolWrapper

from ujson import dumps
from typing import Union, Dict


class Channel:
    """
    Where messaging tasks is capable
    """
    def __init__(self, contacts: Contacts):
        self._contacts: Contacts = contacts

    async def send_msg(self, content: MessageContent) -> SentMessage:
        pass

    async def revoke_msg(self, msgid: str) -> bool:
        pass


class User:
    def __init__(self, uid: int, nickname: str):
        self._uid = uid
        self._nick = nickname

    def __eq__(self, other):
        if type(other) == User:
            return self._uid == other._uid
        elif type(other) == int:
            return self._uid == other
        return False

    def get_id(self):
        return self._uid

    def get_nick_name(self):
        return self._nick


class Friend(User, Channel):
    def __init__(self, contact: Contacts, uid: int, nickname: str):
        User.__init__(self, uid, nickname)
        Channel.__init__(self, contact)

    def __str__(self):
        return dumps({
            'type': 'Friend',
            'id': self.get_id(),
        }, ensure_ascii=False)


class Stranger(User, Channel):
    def __init__(self, contact: Contacts, uid: int, nickname: str, gid: int = None):
        User.__init__(self, uid, nickname)
        Channel.__init__(self, contact)
        self._gid = gid

    def __str__(self):
        return dumps({
            'type': 'Stranger',
            'id': self.get_id(),
            'from_group_id': self._gid
        }, ensure_ascii=False)


class GroupMember(User):
    def __init__(self, contact: Contacts, uid: int, nickname: str, gid: int):
        User.__init__(self, uid, nickname)
        self._contact = contact
        self._gid = gid

    def __str__(self):
        return dumps({
            'type': 'GroupMember',
            'group_id': self._gid,
            'sender_id': self.get_id(),
        }, ensure_ascii=False)

    def open_private_channel(self) -> Channel:
        """
        If the group member is one of the friends then a Friend object is returned.

        Else will return a Stranger instance instead
        """
        ret = self._contact.get_friend(self._uid)
        if ret is None:
            ret = Stranger(self._contact, self._uid, self._nick, self._gid)
        return ret


class GroupAnonymousMember(User):
    def __init__(self, contact: Contacts, uid: int, nickname: str, gid: int):
        User.__init__(self, uid, nickname)
        self._contact = contact
        self._gid = gid

    def __str__(self):
        return dumps({
            'type': 'GroupAnonymousMember',
            'group_id': self._gid,
            'anonymous_id': self.get_id(),
        }, ensure_ascii=False)


class Group(Channel):
    # TODO: lazy loading lists
    def __init__(self, contact: Contacts, gid: int, name: str):
        super().__init__(contact)
        self._gid = gid
        self._name = name
        self._members: Dict[int, GroupMember] = None

    def __eq__(self, other):
        if type(other) == Group:
            return self._gid == other._gid
        elif type(other) == int:
            return self._gid == other
        return False

    async def get_member(self, id: int) -> Union[GroupMember, None]:
        """
        Pick a group member obj from given id

        :param id: user id
        """
        if self._members is None:
            self._members = dict()
            for uid, nick in (await self._contacts._proto_wrapper.get_group_members(self._gid)).items():
                self._members[uid] = GroupMember(self._contacts, uid, nick, self._gid)
        if id in self._members:
            return self._members[id]
        return None

    async def get_members(self) -> Dict[int, GroupMember]:
        """
        Get all members in this group

        :return: {uid, GroupMember} dict
        """
        pass


class Contacts:
    # TODO: lazy loading lists
    def __init__(self, protocol: ProtocolWrapper):
        self._proto_wrapper: ProtocolWrapper = protocol
        # lazy init of dicts
        self._friends: Dict[int, Friend] = None
        self._groups: Dict[int, Group] = None

    async def get_friend(self, id: int) -> Union[Friend, None]:
        """
        Query the friend object from given id

        :param id: user id
        :return: None if not found
        """
        if self._friends is None:
            self._friends = dict()
            for uid, nick in (await self._proto_wrapper.get_friend_list()).items():
                self._friends[uid] = Friend(self, uid, nick)
        if id in self._friends:
            return self._friends[id]
        return None

    async def get_friends(self) -> Dict[int, Friend]:
        """
        Get all friends of the bot

        :return: {uid, Friend} dict
        """
        pass

    async def get_group(self, id: int) -> Union[Group, None]:
        """
        Query the group object from given id

        :param id: group id
        :return: None if not found
        """
        if self._groups is None:
            self._groups = dict()
            for gid, name in (await self._proto_wrapper.get_group_list()).items():
                self._groups[gid] = Group(self, gid, name)
        if id in self._groups:
            return self._groups[id]
        return None

    async def get_groups(self) -> Dict[int, Group]:
        """
        Get all joined groups of the bot

        :return: {uid, Group} dict
        """
        pass
