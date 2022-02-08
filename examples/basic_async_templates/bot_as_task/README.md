# Bot 作为 Task

Advanced 方案。

好处在于可以并入其它已有的异步项目中，共享同一个event_loop。

由自己负责管理asyncio的事件循环。

可以通过调用`bot.request_stop()`来退出Bot。本例程简单地使用了一个异步sleep并退出运行。

