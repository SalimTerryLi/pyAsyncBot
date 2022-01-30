# -*- coding: utf-8 -*-
from dataclasses import dataclass


@dataclass
class BotConfig:
    @dataclass
    class HTTPClientSetting:
        remote_addr: str
        remote_port: int

    @dataclass
    class WebSocketClientSetting:
        remote_addr: str
        remote_port: int

    bot_protocol: str
    http_setting: HTTPClientSetting = None
    ws_setting: WebSocketClientSetting = None