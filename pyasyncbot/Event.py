# -*- coding: utf-8 -*-

from typing import Union

from .Contacts import Contacts, Friend, Group, GroupMember


class BotEvent:
    def __init__(self):
        self._contacts: Contacts = None


# below are bot status events


class OnlineEvent(BotEvent):
    pass


class OfflineEvent(BotEvent):
    pass


# below are events of friend contacts

class FriendAdded(BotEvent):
    def __init__(self, id: int, nick: str):
        super().__init__()
        self._id = id
        self._nick = nick

    def __str__(self):
        return str({
            'FriendAdded': {
                'id': self._id,
                'nick': self._nick
            }
        })

    async def get(self) -> Friend:
        """
        Get the new friend object

        :return: friend
        """
        return await self._contacts.get_friend(self._id, self._nick)

    def get_id(self) -> int:
        """
        Get the ID of the friend

        :return: uid
        """
        return self._id

    def get_nickname(self) -> str:
        """
        Get the nickname of the friend

        :return: name
        """
        return self._nick


class FriendRemoved(BotEvent):
    def __init__(self, id: int, nick: str):
        super().__init__()
        self._id = id
        self._nick = nick

    def __str__(self):
        return str({
            'FriendRemoved': {
                'id': self._id,
                'nick': self._nick
            }
        })

    def get_friend_id(self) -> int:
        """
        Get the ID of the friend

        :return: uid
        """
        return self._id

    def get_friend_nickname(self) -> str:
        """
        Get the nickname of the friend

        :return: name
        """
        return self._nick


class NewFriendRequest(BotEvent):
    def __init__(self, id: int, nick: str, comment: str, event_id: str, source: int = None):
        super().__init__()
        self._id = id
        self._nick = nick
        self._comment = comment
        self._evid = event_id
        self._ref = source

    def get_id(self) ->int:
        return self._id

    def get_nickname(self) ->str:
        return self._nick

    def get_comment(self) -> str:
        return self._comment

    def get_coming_from(self) -> Union[int, None]:
        """
        If he is making friend request from another group then will return that group. Else None

        :return: group, or None
        """
        return self._ref

    async def accept_request(self) -> bool:
        return await self._contacts._proto_wrapper.deal_friend_request(self._id, self._evid, True)

    async def reject_request(self) -> bool:
        return await self._contacts._proto_wrapper.deal_friend_request(self._id, self._evid, False)


# below are events of group contacts

class GroupAdded(BotEvent):
    def __init__(self, id: int, name: str):
        super().__init__()
        self._id = id
        self._name = name

    def __str__(self):
        return str({
            'GroupAdded': {
                'id': self._id,
                'name': self._name
            }
        })

    async def get(self) -> Group:
        """
        Get the group object

        :return: group
        """
        return await self._contacts.get_group(self._id, self._name)

    def get_id(self) -> int:
        """
        Get the ID of the group

        :return: uid
        """
        return self._id

    def get_name(self) -> str:
        """
        Get the name of the group

        :return: name
        """
        return self._name


class GroupRemoved(BotEvent):
    def __init__(self, id: int, name: str, op: int = None):
        super().__init__()
        self._id = id
        self._name = name
        self._operator = op

    def __str__(self):
        return str({
            'GroupRemoved': {
                'id': self._id,
                'name': self._name,
                'isKicked': self._operator is not None
            }
        })

    def get_id(self) -> int:
        """
        Get the ID of the group

        :return: uid
        """
        return self._id

    def get_name(self) -> str:
        """
        Get the name of the group

        :return: name
        """
        return self._name

    def get_kicked_by(self) -> Union[int, None]:
        """
        Get the one who kicked the bot out. None if bot left by itself

        :return: id or None
        """
        return self._operator


class NewGroupInvitation(BotEvent):
    def __init__(self, gid: int, group_name: str, inviter: int, event_id: str):
        super().__init__()
        self._gid = gid
        self._gname = group_name
        self._inviter = inviter
        self._evid = event_id

    def get_group_id(self):
        return self._gid

    def get_group_name(self):
        return self._gname

    def get_inviter_id(self):
        return self._inviter

    async def accept(self) -> bool:
        return await self._contacts._proto_wrapper.deal_friend_request(self._inviter, self._evid, True)

    async def reject(self) -> bool:
        return await self._contacts._proto_wrapper.deal_friend_request(self._inviter, self._evid, False)


# below are group management events

class GroupMemberAdded(BotEvent):
    def __init__(self, gid: int, group_name: str, uid: int, nick: str):
        super().__init__()
        self._gid = gid
        self._gname = group_name
        self._uid = uid
        self._nick = nick

    def __str__(self):
        return str({
            'GroupMemberAdded': {
                'group_id': self._gid,
                'group_name': self._gname,
                'user_id': self._uid,
                'user_nick': self._nick
            }
        })

    async def get_group(self) -> Group:
        return await self._contacts.get_group(self._gid, self._gname)

    def get_group_id(self) -> int:
        return self._gid

    def get_group_name(self) -> str:
        return self._gname

    async def get_member(self) -> GroupMember:
        return await (await self.get_group()).get_member(self._uid, self._nick)

    def get_member_id(self) -> int:
        return self._uid

    def get_member_nickname(self) -> str:
        return self._nick


class GroupMemberRemoved(BotEvent):
    def __init__(self, gid: int, group_name: str, uid: int):
        super().__init__()
        self._gid = gid
        self._gname = group_name
        self._uid = uid

    def __str__(self):
        return str({
            'GroupMemberRemoved': {
                'group_id': self._gid,
                'group_name': self._gname,
                'user_id': self._uid,
            }
        })

    async def get_group(self) -> Group:
        return await self._contacts.get_group(self._gid, self._gname)

    def get_group_id(self) -> int:
        return self._gid

    def get_group_name(self) -> str:
        return self._gname

    def get_member_id(self) -> int:
        return self._uid


class GroupMemberJoinRequest(BotEvent):
    def __init__(self, uid: int, gid: int, event_id: str, comment: str, inviter_id: int = None):
        super().__init__()
        self._uid = uid
        self._gid = gid
        self._evid = event_id
        self._comment = comment
        self._inviter_id = inviter_id

    def get_group_id(self) -> int:
        return self._gid

    def get_requester_id(self):
        return self._uid

    def get_comment(self):
        return self._comment

    def get_inviter_id(self) -> Union[int, None]:
        return self._inviter_id

    async def get_group(self) -> Group:
        return await self._contacts.get_group(self._gid)

    async def get_inviter(self) -> GroupMember:
        return await (await self.get_group()).get_member(self._inviter_id)

    async def accept(self) -> bool:
        return await self._contacts._proto_wrapper.deal_group_member_join_request(self._gid, self._evid, True)

    async def reject(self) -> bool:
        return await self._contacts._proto_wrapper.deal_group_member_join_request(self._gid, self._evid, False)


class GroupAdminChange(BotEvent):
    def __init__(self, gid: int, uid: int, flag: bool):
        super().__init__()
        self._gid = gid
        self._uid = uid
        self._set = flag

    def get_group_id(self) -> int:
        return self._gid

    def get_user_id(self) -> int:
        return self._uid

    def get_flag(self) -> bool:
        """
        Get the admin status of the user

        :return: True if set, False if removed
        """
        return self._set

    async def get_group(self) -> Group:
        return await self._contacts.get_group(self._gid)

    async def get_member(self) -> GroupMember:
        return await (await self.get_group()).get_member(self._uid)


class GroupMute(BotEvent):
    def __init__(self, gid: int, uid: int, duration: int):
        super().__init__()
        self._gid = gid
        self._uid = uid
        self._duration = duration

    def __str__(self):
        return str({
            'GroupMute': {
                'group_id': self._gid,
                'user_id': self._uid,
                'duration': self._duration
            }
        })

    async def get_group(self) -> Group:
        return await self._contacts.get_group(self._gid)

    def get_group_id(self) -> int:
        return self._gid

    async def get_muted_member(self) -> Union[GroupMember, None]:
        """
        Get the muted member, None if group-wide mute

        :return: GroupMember
        """
        return await (await self.get_group()).get_member(self._uid)

    def get_member_id(self) -> int:
        """
        Get the uid of muted member, 0 if group-wide mute

        :return: uid
        """
        return self._uid

    def get_duration(self) -> int:
        """
        Get the muted duration, in second

        :return: second
        """
        return self._duration
