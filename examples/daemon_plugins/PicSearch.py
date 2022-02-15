"""
搜图插件
使用时需要将本文件与 SearchEngineAPI 目录置于 bot daemon 的插件目录下
依赖： httpx asyncio
"""

import traceback, sys
from loguru import logger

from SearchEngineAPI.SauceNAOAPI import query_pic_saucenao_by_url, SauceNAOPictureInformation, LowSimilarityException
from pyasyncbot.Message import ReceivedPrivateMessage, ReceivedGroupMessage
from pyasyncbot.MsgContent import ImageSegment, MessageContent


# Fill your APIKEY here --- I don't know whose key this is, but it works
SAUCENAO_APIKEY = 'f6fe1a86a6e1ef87926c013aa4a99ad58273d636'
# Optional http proxy url
HTTP_PROXY = None


async def on_group_message(msg: ReceivedGroupMessage):
    if '搜图' in str(msg.get_content()):
        curr_msg_reply_seg = msg.get_replied()
        if curr_msg_reply_seg is not None:
            replied_msg = await curr_msg_reply_seg.get_original_msg()
            if replied_msg is None:
                logger.error('failed to get originally replied message')
                return
            for seg in replied_msg.get_content().get_segments():
                if isinstance(seg, ImageSegment):
                    try:
                        logger.debug('search pic: ' + seg.get_url())
                        search_result = await query_pic_saucenao_by_url(seg.get_url(),
                                                                        SAUCENAO_APIKEY,
                                                                        HTTP_PROXY)
                        if isinstance(search_result, SauceNAOPictureInformation):
                            content = MessageContent()
                            content.append_segment(ImageSegment.from_url(search_result.thumbnail_url))
                            text_msg = '来源：' + search_result.site + '\n'
                            text_msg += '作者：' + search_result.author + '\n'
                            if search_result.title is not None:
                                text_msg += '标题：' + search_result.title + '\n'
                            text_msg += '链接：' + search_result.url + '\n'
                            if search_result.topic is not None:
                                text_msg += '题材：' + search_result.topic + '\n'
                            if search_result.characters is not None:
                                text_msg += '相关角色：' + search_result.characters + '\n'
                            content.append_segment(text_msg)
                            await msg.get_channel().send_msg(content)
                            return
                    except LowSimilarityException:
                        await msg.quoted_reply(MessageContent('未找到或相似都过低'))
                        return
                    except Exception:
                        traceback.print_exc(file=sys.stderr)
                        await msg.quoted_reply(MessageContent('搜索出错'))
                        return
            await msg.quoted_reply(MessageContent('没有图片'))
