# Bot 作为 Daemon

最简单无脑的方案。

由Bot接管asyncio的事件循环，在Python原本的同步程序流中阻塞并运行Bot。

可以通过在Bot线程外调用`bot.request_stop()`来退出Bot。本例程采用捕获系统Signal的形式退出运行。

