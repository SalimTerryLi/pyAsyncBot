# -*- coding: utf-8 -*-

import typing
import asyncio
import aiohttp
from asyncio import CancelledError
import ujson

from .Message import ReceivedMessage


class Bot:
    """
    Async Bot client
    """
    # will be valid only inside async context
    _ahttp: aiohttp.ClientSession
    _aws: aiohttp.client.ClientWebSocketResponse
    _main_task: asyncio.Task

    # registered callbacks
    _on_private_msg: typing.Callable[[ReceivedMessage], typing.Awaitable[None]] = None
    _on_group_msg: typing.Callable[[ReceivedMessage], typing.Awaitable[None]] = None

    def __init__(self, addr: str = '127.0.0.1', port: int = 8888):
        """
        Create a bot client object

        :param addr: WebAPI server address
        :param port: WebAPI server port
        """
        self.api_addr = addr
        self.api_port = port
        self._async_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._async_loop)

    def __del__(self):
        self._async_loop.close()

    def run(self):
        """
        Block and run the bot client
        Return when bot exit
        """
        # main loop task, blocking
        self._main_task = self._async_loop.create_task(self._run(), name='main task')
        print('main task emitted')
        ret = self._async_loop.run_until_complete(self._main_task)
        # find sub-tasks that are still running
        curr_tasks = asyncio.Task.all_tasks(loop=self._async_loop)
        curr_tasks = [x for x in curr_tasks if not x.done()]
        print('main task exited. wait for {d} of sub-tasks to complete'.format(d=len(curr_tasks)))
        self._async_loop.run_until_complete(asyncio.gather(*curr_tasks))
        print('all tasks exited')
        return ret

    def request_stop(self):
        """
        Notify the main task to exit

        :return:
        """
        # schedule stop
        self._async_loop.call_soon_threadsafe(self.__request_stop_cb)

    def __request_stop_cb(self):
        self._main_task.cancel()

    async def _run(self):
        self._ahttp = aiohttp.ClientSession(loop=self._async_loop)

        ret = 0
        # check service and version
        if await self._check_remote():
            await self._run_loop()
        else:
            print('failed to verify remote service')
            ret = -1

        await self._ahttp.close()
        return ret

    # do ws connection-oriented maintenance
    async def _run_loop(self):
        # async connect
        self._aws = await self._ahttp.ws_connect('ws://{remote_addr}:{remote_port}'.format(
            remote_addr=self.api_addr,
            remote_port=self.api_port))
        print('WebSocket connection established')

        while True:
            try:
                msg = await self._aws.receive()
                if msg.type == aiohttp.WSMsgType.error:
                    print(msg)
                    # TODO: should we do something here?
                elif msg.type == aiohttp.WSMsgType.closed:
                    print(self._aws.exception())
                    del self._aws
                    while True:
                        try:
                            print('WebSocket disconnected. wait 10s before reconnect')
                            await asyncio.sleep(10)
                            self._aws = await self._ahttp.ws_connect('ws://{remote_addr}:{remote_port}'.format(
                                remote_addr=self.api_addr,
                                remote_port=self.api_port))
                            # no more exception means successfully connected
                            print('successfully reconnected')
                            break
                        except CancelledError:
                            print('reconnecting canceled')
                            return
                        except Exception as e:
                            print(e)
                elif msg.type == aiohttp.WSMsgType.text:
                    self._async_loop.create_task(self._deal_ws_packets(msg.data))
            except CancelledError:
                print('main task canceled')
                await self._aws.close()
                return

    # helper function which checks whether we connected to a oicq-webd or not
    async def _check_remote(self):
        try:
            async with self._ahttp.get('http://{remote_addr}:{remote_port}'.format(
                    remote_addr=self.api_addr,
                    remote_port=self.api_port)) as res:
                if res.content_type == 'application/json':
                    res = await res.json()
                    if res['name'] == 'oicq-webapi':
                        print('remote version: {v}'.format(v=res['version']))
                        return True
        except Exception as e:
            print(e)
        return False

    # launched in separate tasks in parallel
    async def _deal_ws_packets(self, data):
        try:
            json_data = ujson.loads(data)
            if json_data['type'] == 'msg':
                msg_data = json_data['data']
                msg = ReceivedMessage._deserialize(msg_data)
                if msg_data['type'] == 'private':
                    if self._on_private_msg is not None:
                        await self._on_private_msg(msg)
                elif msg_data['type'] == 'group':
                    if self._on_group_msg is not None:
                        await self._on_group_msg(msg)
                else:
                    print('warning: unsupported sub-type: {base}.{sub}'.format(
                        base=json_data['type'],
                        sub=msg_data['type']
                    ))
            elif json_data['type'] == 'revoke':
                pass
            elif json_data['type'] == 'user':
                pass
            elif json_data['type'] == 'group':
                pass
            else:
                print('warning: unsupported type {type}'.format(type=json_data['type']))
        except Exception as e:
            print(e)

    def on_private_message(self, deco):
        """
        Register message callback for private channel
        """
        if self._on_private_msg is not None:
            print('warning: overwrite on_private_msg')
        self._on_private_msg = deco

    def on_group_message(self, deco):
        """
        Register message callback for group channel
        """
        if self._on_group_msg is not None:
            print('warning: overwrite on_group_msg')
        self._on_group_msg = deco
