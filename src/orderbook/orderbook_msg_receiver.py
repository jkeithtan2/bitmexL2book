import json
from queue import Empty
import logging
from datetime import datetime

from src.exceptions import OrderBookException
from src.orderbook.l2orderbook import L2OrderBook
from src.signalprocessors import init_signals
from src.utils import get_symbol_from_exc_msg
from src import orderbookconstants as obc


class L2OrderbookExcMsgReceiver:
    CHANGE_STATE_ACTIONS = {'update', 'partial', 'insert', 'delete'}

    def __init__(self, msg_queue, db_client_factory, shutdown_event, symbols):
        super(L2OrderbookExcMsgReceiver, self).__init__()
        self.l2OrderbookDict = {
            symbol: L2OrderBook(symbol) for symbol in symbols
        }
        self.db_client_factory = db_client_factory
        self.mongo_client = None
        self.msg_queue = msg_queue
        self.shutdown_event = shutdown_event

    def run(self):
        logging.info('Starting L2 orderbook msg receiver')
        init_signals(self.shutdown_event)
        """
        https://api.mongodb.com/python/current/faq.html#using-pymongo-with-multiprocessing
        
        Specifically, instances of MongoClient must not be copied from a parent process to a child process. 
        Instead, the parent process and each child process must create their own instances of MongoClient
        """
        self.mongo_client = self.db_client_factory.mongo_client()
        while not self.shutdown_event.is_set():
            try:
                msg = self.msg_queue.get(block=True, timeout=obc.DEFAULT_POLLING_TIME)
                logging.info(msg)
                if msg == obc.STOP_Q_MSG:
                    break
                l2orderbook = self._exc_msg_handler(msg)
                self._persist(l2orderbook.symbol, l2orderbook)
            except Empty:
                continue
            except OrderBookException as obe:
                logging.error(obe)
        self.mongo_client.close_connection()

    async def async_run(self):
        logging.info('starting async L2 orderbook msg receiver')
        self.mongo_client = self.db_client_factory.async_mongo_client()
        while not self.shutdown_event.is_set():
            try:
                exc_msg = await self.msg_queue.get()
                logging.debug(exc_msg)
                if exc_msg == obc.STOP_Q_MSG:
                    break
                l2orderbook = self._exc_msg_handler(exc_msg)
                await self._async_persist(l2orderbook.symbol, l2orderbook)
            except OrderBookException as obe:
                logging.error(obe)
        self.mongo_client.close_connection()
        logging.info('Finishing l2 orderbook task')

    def _exc_msg_handler(self, msg):
        symbol = get_symbol_from_exc_msg(msg)
        action = msg[obc.EXC_MSG_STRUCT.ACTION]
        if symbol and action in L2OrderbookExcMsgReceiver.CHANGE_STATE_ACTIONS:
            l2orderbook = self.l2OrderbookDict.get(symbol)
            l2orderbook.handle_exchange_msg(msg)
            return l2orderbook
        else:
            logging.info(f'L2 orderbook ignoring {json.dumps(msg)}')

    def _persist(self, symbol, l2orderbook):
        doc = self._prep_doc_to_persist(symbol, l2orderbook)
        try:
            self.mongo_client.persist_to_orderbook_collection(doc)
        except Exception as e:
            logging.error(str(e))

    async def _async_persist(self, symbol, l2orderbook):
        doc = self._prep_doc_to_persist(symbol, l2orderbook)
        try:
            await self.mongo_client.persist_to_orderbook_collection(doc)
        except Exception as e:
            logging.error(str(e))

    def _prep_doc_to_persist(self, symbol, l2orderbook):
        persist_orderbook_repr = l2orderbook.orderbook_repr()
        curr_time = datetime.utcnow().isoformat()
        return ({
            '_id': f'{symbol}_{curr_time}',
            'timestamp': curr_time,
            **persist_orderbook_repr
        })
