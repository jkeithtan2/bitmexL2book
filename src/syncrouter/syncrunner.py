import json
import queue
import logging
import multiprocessing as mp
from multiprocessing import Process

import websocket

from src.orderbook.l2orderbook import L2OrderBook
from src.signalprocessors import init_signals
from src import orderbookconstants as obc
from src.clients.cache_client_factory import CacheClientFactory
from src.clients.db_client_factory import DbClientFactory
from src.orderbook.orderbookcache import OrderBookCache
from src.clients.socketlisteners import SyncBitMexSocketListener
from src.orderbook.orderbook_msg_receiver import L2OrderbookExcMsgReceiver


class SyncRunner:
    def __init__(self):
        cache_client_factory = CacheClientFactory()
        db_client_factory = DbClientFactory()
        self.shutdown_event = mp.Event()
        self.websocket_message_queue = queue.Queue()
        self.l2_orderbook_msg_queue = mp.Queue()
        self.orderbook_receiver = L2OrderbookExcMsgReceiver(
            self.l2_orderbook_msg_queue,
            db_client_factory,
            self.shutdown_event,
            obc.SYMBOLS
        )
        self.orderbook_cache = OrderBookCache(cache_client_factory.redis_client())
        self.full_l2_orderbooks = {symbol: L2OrderBook(symbol) for symbol in symbols}
        self.has_received_orderbook10_partial = False
        self.ws = None
        self.orderbook_receiver_process = Process(target=self.orderbook_receiver.run)
        init_signals(self.shutdown_event)

    def run(self):
        logging.info('Starting orderbook listener')
        self.ws = SyncBitMexSocketListener(symbols=obc.SYMBOLS,
                                           websocket_msg_queue=self.websocket_message_queue)
        self.orderbook_receiver_process.start()
        try:
            self.ws.start()
            while not self.shutdown_event.is_set():
                try:
                    msg = self.websocket_message_queue.get(block=True, timeout=obc.DEFAULT_POLLING_TIME)
                    logging.debug(msg)
                    json_msg = json.loads(msg)
                    table = json_msg.get(obc.EXC_MSG_STRUCT.TABLE)
                    if table == obc.TABLES.CACHE_ORDERBOOK:
                        self.orderbook_cache.handle_exchange_message(json_msg)
                    elif table == obc.TABLES.L2_ORDERBOOK:
                        self.l2_orderbook_msg_queue.put(json_msg)
                except queue.Empty:
                    continue
        except websocket.WebSocketException as ws:
            logging.error(str(ws))
        self.shutdown()

    def shutdown(self):
        logging.info('Beginning Shutdown')
        if self.ws:
            self.ws.exit()
        self.orderbook_receiver_process.join(obc.DEFAULT_JOIN_TIME)
        if self.orderbook_receiver_process.is_alive():
            self.orderbook_receiver_process.terminate()
        self.l2_orderbook_msg_queue.close()
        self.l2_orderbook_msg_queue.join_thread()
        logging.info('Shutdown complete')


if __name__ == "__main__":
    logging_format = '%(asctime)s %(processName)s %(message)s'
    logging.basicConfig(format=logging_format, level=logging.INFO)
    symbols = obc.SYMBOLS
    sync_runner = SyncRunner()
    sync_runner.run()
