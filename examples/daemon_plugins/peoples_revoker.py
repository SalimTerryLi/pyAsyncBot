# -*- coding: utf-8 -*-

"""
服务于具有自发意志的群员的撤回插件，解放群管理
"""

from datetime import datetime, timedelta
from pyasyncbot.Message import ReceivedGroupMessage
from pyasyncbot.MsgContent import MentionSegment, TextSegment, MessageContent


async def on_group_message(msg: ReceivedGroupMessage):
    msg_segs = msg.get_content().get_segments()
    if len(msg_segs) == 2:
        if isinstance(msg_segs[0], MentionSegment) and isinstance(msg_segs[1], TextSegment):
            reply_msg = msg_segs[1].get_text()
            if len(reply_msg) < 4 and reply_msg.endswith('撤回'):
                orig_msg = await msg.get_replied().get_original_msg()
                if datetime.now() - orig_msg._time > timedelta(minutes=20):
                    await msg.quoted_reply(MessageContent('禁止撤回过早的消息'))
                    return
                if await msg.get_channel().revoke_msg(msg.get_replied().get_msgid()):
                    msg_content = MessageContent(
                        '已根据群员@' + str(msg.get_sender().get_id()) +
                        '的意见撤回了@' + str(orig_msg.get_sender().get_id()) +
                        '的消息')
                    await msg.quoted_reply(msg_content)
