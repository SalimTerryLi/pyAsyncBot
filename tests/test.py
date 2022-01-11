#!/usr/bin/env python

from context import oicq_web


from oicq_web import Bot
import signal

bot = Bot()


# setup exit notification
def signal_handler(sig, frame):
    print('Request stopping...')
    bot.request_stop()


signal.signal(signal.SIGINT, signal_handler)


@bot.on_private_message
async def on_private_message(msg):
    print(msg)


@bot.on_group_message
async def on_group_message(msg):
    print(msg)


exit(bot.run())
