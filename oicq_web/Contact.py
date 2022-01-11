# -*- coding: utf-8 -*-
from ujson import dumps


class User:
    def __init__(self, uid: int):
        self._uid = uid

    def __eq__(self, other):
        return self._uid == other._uid

    def get_id(self):
        return self._uid


class Friend(User):
    def __init__(self, uid: int):
        super().__init__(uid)

    def __str__(self):
        return dumps({
            'type': 'Friend',
            'id': self.get_id(),
        })


class Stranger(User):
    def __init__(self, uid: int, gid: int):
        super().__init__(uid)
        self._gid = gid

    def __str__(self):
        return dumps({
            'type': 'Stranger',
            'id': self.get_id(),
            'from_group_id': self._gid
        })


class GroupMember(User):
    def __init__(self, uid: int, gid: int):
        super().__init__(uid)
        self._gid = gid

    def __str__(self):
        return dumps({
            'type': 'GroupMember',
            'group_id': self._gid,
            'sender_id': self.get_id(),
        })


class GroupAnonymousMember(User):
    def __init__(self, uid: int, gid: int):
        super().__init__(uid)
        self._gid = gid

    def __str__(self):
        return dumps({
            'type': 'GroupAnonymousMember',
            'group_id': self._gid,
            'anonymous_id': self.get_id(),
        })


class Group:
    def __init__(self, gid: int):
        self._gid = gid

    def __eq__(self, other):
        return self._gid == other._gid
