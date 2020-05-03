from queue import Queue
from typing import List
import logging

import aiohttp
import websocket
import threading
from time import sleep
from src import orderbookconstants as obc


class SyncBitMexSocketListener:

    def __init__(self, symbols: List, websocket_msg_queue: Queue):
        self.symbols = symbols
        self.msg_queue = websocket_msg_queue
        self.exited = False

        symbol_subs = ["orderBookL2", "orderBook10"]
        subscriptions = [f'{sub}:{symbol}' for sub in symbol_subs for symbol in self.symbols]
        ws_url = f'{obc.BITMEX_WS_ENDPOINT}{",".join(subscriptions)}'

        self.ws = websocket.WebSocketApp(ws_url,
                                         on_message=self._on_message,
                                         on_close=self._on_close,
                                         on_open=self._on_open,
                                         on_error=self._on_error)

    def start(self):
        self._start_listening()

    def exit(self):
        if not self.exited:
            self.exited = True
            self.ws.close()

    def _start_listening(self):
        self.wst = threading.Thread(target=lambda: self.ws.run_forever())
        self.wst.daemon = True
        self.wst.start()

        conn_timeout = 5
        while (not self.ws.sock or not self.ws.sock.connected) and conn_timeout:
            sleep(obc.DEFAULT_JOIN_TIME)
            conn_timeout -= 1
        if not conn_timeout:
            self.exit()
            raise websocket.WebSocketException('Could not connect to bitmex websocket')

    def _on_message(self, message):
        self.msg_queue.put(message)

    def _on_error(self, error):
        if not self.exited:
            logging.error(f'Error during websocket listening {error}')
            raise websocket.WebSocketException(error)

    def _on_open(self):
        logging.debug('Websocket Opened')

    def _on_close(self):
        logging.debug('Websocket Closed')


class AsyncBitMexSocketListener:

    def __init__(self, symbols: List, msg_queue: Queue, shutdown_event):
        self.symbols = symbols
        self.msg_queue = msg_queue
        self.exited = False
        self.shutdown_event = shutdown_event

        symbol_subs = ["orderBookL2", "orderBook10"]
        subscriptions = [f'{sub}:{symbol}' for sub in symbol_subs for symbol in self.symbols]
        self.ws_url = f'{obc.BITMEX_WS_ENDPOINT}{",".join(subscriptions)}'

    async def get_orderbook_feed(self, loop):
        async with aiohttp.ClientSession(loop=loop).ws_connect(self.ws_url) as ws:
            async for feed in ws:
                await self.msg_queue.put(feed.data)
