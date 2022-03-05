# -*- coding: utf-8 -*-

"""
插件模板
"""

from pyasyncbot.Event import BotEvent, NewFriendRequest, NewGroupInvitation, GroupMemberJoinRequest

from loguru import logger


async def on_event(event: BotEvent):
    if isinstance(event, NewFriendRequest):
        logger.info('好友申请: UID={uid}, Nickname="{nick}", Comment="{comment}", FromGroup={src}'.format(
            uid=event.get_id(),
            nick=event.get_nickname(),
            comment=event.get_comment(),
            src=event.get_coming_from()
        ))
        result = await event.reject()
        #result = await event.accept()
        if result is False:
            logger.warning('Failed to deal with NewFriendRequest')
    elif isinstance(event, NewGroupInvitation):
        logger.info('群邀请: GroupName="{name}", GroupID={id}, InviterID={iid}'.format(
            name=event.get_group_name(),
            id=event.get_group_id(),
            iid=event.get_inviter_id()
        ))
        result = await event.reject()
        #result = await event.accept()
        if result is False:
            logger.warning('Failed to deal with NewGroupInvitation')
    elif isinstance(event, GroupMemberJoinRequest):
        logger.info('申请加群: UserID={uid}, GroupID={gid}, Comment="{comment}", Inviter={iid}'.format(
            uid=event.get_requester_id(),
            gid=event.get_group_id(),
            comment=event.get_comment(),
            iid=event.get_inviter_id()
        ))
        result = await event.reject()
        #result = await event.accept()
        if result is False:
            logger.warning('Failed to deal with GroupMemberJoinRequest')
