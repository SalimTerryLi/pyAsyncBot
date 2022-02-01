# -*- coding: utf-8 -*-
from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .Message import MessageContent
    from .FrameworkWrapper import ProtocolWrapper

from .Message import SentMessage

from loguru import logger
from ujson import dumps
from typing import Union, Dict, Any
from abc import ABC, abstractmethod


class Channel(ABC):
    """
    Where messaging tasks is capable
    """
    def __init__(self, contacts: Contacts):
        self._contacts: Contacts = contacts

    @abstractmethod
    async def send_msg(self, content: MessageContent) -> SentMessage:
        """
        Override this function to implement message sending

        :param content: msg content
        :return: sent message, or None if failed
        """
        pass

    @abstractmethod
    async def revoke_msg(self, msgid: str) -> bool:
        """
        Override this function to implement message revoking

        :param msgid: msg ID
        :return: success
        """
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
            'nick': self.get_nick_name()
        }, ensure_ascii=False)

    async def send_msg(self, content: MessageContent) -> SentMessage:
        msgid = await self._contacts._proto_wrapper.serv_private_message(self.get_id(), content)
        if msgid is None:
            return None
        else:
            ret = SentMessage()
            ret._msgid = msgid
            ret._channel = self
            return ret

    async def revoke_msg(self, msgid: str) -> bool:
        return await self._contacts._proto_wrapper.serv_private_revoke(self.get_id(), msgid)


class Stranger(User, Channel):
    def __init__(self, contact: Contacts, uid: int, nickname: str, gid: int = None):
        User.__init__(self, uid, nickname)
        Channel.__init__(self, contact)
        self._gid = gid

    def __str__(self):
        return dumps({
            'type': 'Stranger',
            'id': self.get_id(),
            'nick': self.get_nick_name(),
            'from_group_id': self._gid
        }, ensure_ascii=False)

    async def send_msg(self, content: MessageContent) -> SentMessage:
        pass

    async def revoke_msg(self, msgid: str) -> bool:
        pass


class GroupMember(User):
    def __init__(self, contact: Contacts, uid: int, nickname: str, gid: int):
        User.__init__(self, uid, nickname)
        self._contact = contact
        self._gid = gid

    def __str__(self):
        return dumps({
            'type': 'GroupMember',
            'group_id': self._gid,
            'nick': self.get_nick_name(),
            'sender_id': self.get_id(),
        }, ensure_ascii=False)

    async def open_private_channel(self) -> Channel:
        """
        If the group member is one of the friends then a Friend object is returned.

        Else will return a Stranger instance instead
        """
        ret = await self._contact.get_friend(self._uid)
        if ret is None:
            ret = Stranger(self._contact, self._uid, self._nick, self._gid)
        return ret

    async def send_msg(self, content: MessageContent) -> SentMessage:
        pass

    async def revoke_msg(self, msgid: str) -> bool:
        pass


class GroupAnonymousMember(User):
    def __init__(self, contact: Contacts, uid: int, nickname: str, gid: int):
        User.__init__(self, uid, nickname)
        self._contact = contact
        self._gid = gid

    def __str__(self):
        return dumps({
            'type': 'GroupAnonymousMember',
            'group_id': self._gid,
            'nick': self.get_nick_name(),
            'anonymous_id': self.get_id(),
        }, ensure_ascii=False)

    async def send_msg(self, content: MessageContent) -> SentMessage:
        pass

    async def revoke_msg(self, msgid: str) -> bool:
        pass


class Group(Channel):
    def __init__(self, contact: Contacts, gid: int, name: str):
        super().__init__(contact)
        self._gid = gid
        self._name = name
        self._members: Dict[int, GroupMember] = None
        self._members_tmp: Dict[int, GroupMember] = dict()

    def __eq__(self, other):
        if type(other) == Group:
            return self._gid == other._gid
        elif type(other) == int:
            return self._gid == other
        return False

    def __str__(self):
        return str({
            'group_id': self._gid,
            'name': self._name
        })

    async def send_msg(self, content: MessageContent) -> SentMessage:
        pass

    async def revoke_msg(self, msgid: str) -> bool:
        pass

    async def get_member(self, id: int, nick: str = None) -> Union[GroupMember, None]:
        """
        Pick a group member obj from given id

        Will not try to populate member list if nick is provided, as lazy loading is

        :param id: user id
        :param nick: user nickname
        """
        if self._members is None:
            # member list is not populated
            if id in self._members_tmp:
                # but the member is in cache, that's all
                return self._members_tmp[id]
            # if that member is also not in cache, so that we must get one
            if nick is None:
                # no nick is provided so that the whole member list must be obtained
                self._members = dict()
                for uid, nick in (await self._contacts._proto_wrapper.get_group_members(self._gid)).items():
                    self._members[uid] = GroupMember(self._contacts, uid, nick, self._gid)
                logger.debug('group member list initially forced fetched for {gid}, with {size} entries'.format(
                    gid=self._gid, size=len(self._members))
                )
                # disable the cached list
                self.__disable_cached_member_list()
                # return the requested member below later
            else:
                # nick is also provided so that we find or create a mock member object
                self._members_tmp[id] = GroupMember(self._contacts, id, nick, self._gid)
                logger.debug('mocked group member list of {gid}: append {uid}, total {size}'.format(
                    gid=self._gid, uid=id,size=len(self._members_tmp)))
                return self._members_tmp[id]
        else:
            # always use the populated list
            pass
        if id in self._members:
            return self._members[id]
        return None

    async def get_members(self) -> Dict[int, GroupMember]:
        """
        Get all members in this group

        :return: {uid, GroupMember} dict
        """
        # always make sure the list is available
        if self._members is None:
            self._members = dict()
            for uid, nick in (await self._contacts._proto_wrapper.get_group_members(self._gid)).items():
                self._members[uid] = GroupMember(self._contacts, uid, nick, self._gid)
            logger.debug('group member list initially fetched for {gid}, with {size} entries'.format(
                gid=self._gid, size=len(self._members))
            )
        if self._members_tmp is not None:
            # there's something in cache, check and cleanup
            self.__disable_cached_member_list()
        return self._members

    def __disable_cached_member_list(self):
        logger.debug('group {gid} member cached list disabled'.format(gid=self._gid))
        for uid in self._members_tmp:
            if uid not in self._members:
                logger.warning('member {uid} doesn\' t exist in group {gid}'.format(uid=uid, gid=self._gid))
            else:
                # use cached version
                self._members[uid] = self._members_tmp[uid]
        self._members_tmp = None


class Contacts:
    # TODO: abstract and make lazy init unified
    def __init__(self, protocol: ProtocolWrapper):
        self._proto_wrapper: ProtocolWrapper = protocol
        # lazy init of dicts
        self._friends: Dict[int, Friend] = None
        self._groups: Dict[int, Group] = None
        self._friends_tmp: Dict[int, Friend] = dict()
        self._groups_tmp: Dict[int, Group] = dict()

    async def get_friend(self, id: int, nick: str = None) -> Union[Friend, None]:
        """
        Query the friend object from given id

        Will not try to populate friend list if nick is provided, as lazy loading is

        :param id: user id
        :param nick: user nickname
        :return: None if not found
        """
        if self._friends is None:
            # friend list is not populated
            if id in self._friends_tmp:
                # but the friend is in cache, that's all
                return self._friends_tmp[id]
            # if that member is also not in cache, so that we must get one
            if nick is None:
                # no nick is provided so that the whole member list must be obtained
                self._friends = dict()
                for uid, nick in (await self._proto_wrapper.get_friend_list()).items():
                    self._friends[uid] = Friend(self, uid, nick)
                logger.debug('friend list initially forced fetched, with {size} entries'.format(
                    size=len(self._friends))
                )
                # disable the cached list
                self.__disable_cached_friends_list()
                # return the requested member below later
            else:
                # nick is also provided so that we create a mock friend object
                self._friends_tmp[id] = Friend(self, id, nick)
                logger.debug('mocked friend list: append {uid}, total {size}'.format(uid=id,size=len(self._friends_tmp)))
                return self._friends_tmp[id]
        else:
            # always use the populated list
            pass
        if id in self._friends:
            return self._friends[id]
        return None

    async def get_friends(self) -> Dict[int, Friend]:
        """
        Get all friends of the bot

        :return: {uid, Friend} dict
        """
        # ensure list is available
        if self._friends is None:
            self._friends = dict()
            for uid, nick in (await self._proto_wrapper.get_friend_list()).items():
                self._friends[uid] = Friend(self, uid, nick)
            logger.debug('friend list initially fetched, with {size} entries'.format(
                size=len(self._friends))
            )
        if self._friends_tmp is not None:
            # there's something in cache, check and cleanup
            self.__disable_cached_friends_list()
        return self._friends

    def __disable_cached_friends_list(self):
        logger.debug('friend cached list disabled')
        for uid in self._friends_tmp:
            if uid not in self._friends:
                logger.warning('friend {uid} doesn\' t exist'.format(uid=uid))
            # use cached version
            self._friends[uid] = self._friends_tmp[uid]
        self._friends_tmp = None

    async def get_group(self, id: int, name: str = None) -> Union[Group, None]:
        """
        Query the group object from given id

        Will not try to populate group list if name is provided, as lazy loading is

        :param id: group id
        :param name: group name
        :return: None if not found
        """
        if self._groups is None:
            # group list is not populated
            if id in self._groups_tmp:
                # but the friend is in cache, that's all
                return self._groups_tmp[id]
            # if that member is also not in cache, so that we must get one
            if name is None:
                # no nick is provided so that the whole member list must be obtained
                self._groups = dict()
                for gid, name in (await self._proto_wrapper.get_group_list()).items():
                    self._groups[gid] = Group(self, gid, name)
                logger.debug('group list initially forced fetched, with {size} entries'.format(
                    size=len(self._groups))
                )
                # disable the cached list
                self.__disable_cached_groups_list()
                # return the requested member below later
            else:
                # name is also provided so that we create a mock group object
                self._groups_tmp[id] = Group(self, id, name)
                logger.debug('mocked group list: append {gid}, total {size}'.format(gid=id,size=len(self._groups_tmp)))
                return self._groups_tmp[id]
        else:
            # always use the populated list
            pass
        if id in self._groups:
            return self._groups[id]
        return None

    async def get_groups(self) -> Dict[int, Group]:
        """
        Get all joined groups of the bot

        :return: {uid, Group} dict
        """
        # ensure list is available
        if self._groups is None:
            self._groups = dict()
            for gid, name in (await self._proto_wrapper.get_group_list()).items():
                self._groups[gid] = Group(self, gid, name)
            logger.debug('group list initially fetched, with {size} entries'.format(
                size=len(self._groups))
            )
        if self._groups_tmp is not None:
            # there's something in cache, check and cleanup
            self.__disable_cached_groups_list()
        return self._groups

    def __disable_cached_groups_list(self):
        logger.debug('group cached list disabled')
        for gid in self._groups_tmp:
            if gid not in self._groups:
                logger.warning('group {gid} doesn\' t exist'.format(gid=gid))
            else:
                # use cached version
                self._groups[gid] = self._groups_tmp[gid]
        self._groups_tmp = None
