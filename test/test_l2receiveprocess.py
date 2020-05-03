import json
import queue
import unittest
from src import orderbookconstants as obc

from src.orderbook.l2orderbook import L2OrderBook
from src.orderbook.orderbook_msg_receiver import L2OrderbookExcMsgReceiver


class MockShutDownEvent():
    def __init__(self):
        self.shutdown = False

    def is_set(self):
        return self.shutdown

    def set(self):
        self.shutdown = True


class MockDbClientFactory:
    def mongo_client(self):
        return self

    def __init__(self):
        self.orderbooks = []

    def persist_to_orderbook_collection(self, update):
        self.orderbooks.append(update)

    def close_connection(self):
        pass


class TestL2OrderbookReceiver(unittest.TestCase):
    def setUp(self):
        self.test_queue = queue.Queue()
        self.db_client_factory = MockDbClientFactory()
        self.shutdown_event = MockShutDownEvent()
        symbols = ['XBTUSD']
        self.test_receiver = L2OrderbookExcMsgReceiver(
            self.test_queue,
            self.db_client_factory,
            self.shutdown_event,
            symbols
        )
        self.l2_orderbook = L2OrderBook(symbols[0])
        self.orderbooks_history = []

    def test_correct_results_with_l2orderbook_feed(self):
        with open('resources/orderbookL2_feed_test.txt') as ft:
            feed = ft.readline()
            while feed:
                feed = json.loads(feed)
                self.l2_orderbook.handle_exchange_msg(feed)
                self.orderbooks_history.append(self.l2_orderbook.orderbook_repr())
                self.test_queue.put(feed)
                feed = ft.readline()
        self.test_queue.put(obc.STOP_Q_MSG)
        self.test_receiver.run()
        self.assertEqual(len(self.orderbooks_history), len(self.db_client_factory.orderbooks))
        for orderbook in self.db_client_factory.orderbooks:
            orderbook.pop('_id')
            orderbook.pop('timestamp')
        self.assertEqual(json.dumps(self.orderbooks_history), json.dumps(self.db_client_factory.orderbooks))



