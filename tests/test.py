#!/usr/bin/env python

from context import oicq_web
from oicq_web import Bot

import signal
import sys

bot = Bot()


def signal_handler(sig, frame):
    print('Request stopping...')
    bot.request_stop()


signal.signal(signal.SIGINT, signal_handler)

exit(bot.run())
