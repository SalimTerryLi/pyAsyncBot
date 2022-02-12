# Standalone Daemon

在使用 pip 安装本框架后，默认附带了一个简单的 daemon 工具，可以通过

```sh
pyasyncbotd -d /path/to/plugins/dir
```

来启动。插件路径若不提供则为当前目录。

将会检查插件目录下所有 `*.py` 文件，并尝试进行 import。不会检查子文件夹内容。

## Callbacks

- `async def on_private_message(msg: ReceivedPrivateMessage)`
- `async def on_group_message(msg: ReceivedGroupMessage)`
- `async def on_private_revoke(msg: RevokedMessage)`
- `async def on_group_revoke(msg: RevokedMessage)`
- `async def on_event(event: BotEvent)`
- `async def on_loaded()`

列出的函数签名供插件实现，接收 bot 的回调消息

