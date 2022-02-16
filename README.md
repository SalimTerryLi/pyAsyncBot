# pyAsyncBot

Yet another async chat bot framework running on python3.8. 

The framework is designed to be OOP friendly with minimum python syntactic sugar. Implementation has proper startup and graceful shutdown procedure to make it suitable to be integerated into other existing async projects and safely sharing the same event loop in the same thread.

The framework also shipping a simple daemon implementation which can serve multiple simple plugins.

This framework is highly inspired by [OICQ2](https://github.com/takayama-lily/oicq)

## API BACKEND

Surrently only the one defined by me is supported: https://github.com/SalimTerryLi/oicq_webd

## INSTALL

Python 3.8+ is required. I strongly recommend to install the package into virtualenv.

```sh
pip install pyasyncbot
```

## EXAMPLE

Under `examples` folder of this repo

## DAEMON

```sh
pyasyncbotd -h
```
