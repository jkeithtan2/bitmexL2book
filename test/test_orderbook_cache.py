import json
import unittest

from src import orderbookconstants as obc

from src.orderbook.orderbookcache import OrderBookCache


class MockCacheClient:
    def __init__(self):
        self.set_vals = {}

    def set(self, symbol, data):
        self.set_vals[symbol] = data


class TestOrderBookCache(unittest.TestCase):
    def setUp(self):
        self.mock_cache = MockCacheClient()
        self.order_book_cache = OrderBookCache(self.mock_cache)

    def test_latest_data_should_be_set_in_cache(self):
        symbol = None
        prev_line = None
        with open('resources/orderbook10_feed_test.txt', 'r') as f:
            line = f.readline()
            while line:
                line = json.loads(line)
                if not symbol:
                    symbol = line[obc.EXC_MSG_STRUCT.DATA][0][obc.EXC_DATA_FIELD.SYMBOL]
                self.order_book_cache.handle_exchange_message(line)
                prev_line = line
                line = f.readline()
        self.assertEqual(self.mock_cache.set_vals[symbol], json.dumps(prev_line[obc.EXC_MSG_STRUCT.DATA]))

    def test_error_msg_when_no_symbol_in_exc_msg(self):
        fake_exc_msg = {"table": "orderBook10", "action": "partial", "data":[{"asks": [], "bids": []}]}
        with self.assertLogs(level='ERROR') as al:
            self.order_book_cache.handle_exchange_message(fake_exc_msg)
        self.assertEqual("ERROR:root:symbol or cache_data is empty for {'table': 'orderBook10', 'action': 'partial', 'data': [{'asks': [], 'bids': []}]}",
                         al.output[0])
