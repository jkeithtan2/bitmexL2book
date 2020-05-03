import unittest

from src.exceptions import OrderBookException
from src.orderbook.l2orderbook import L2OrderBook
from test.resources import exceptions_data


class TestReplayDataFeed(unittest.TestCase):
    def setUp(self):
        self.l2_order_book = L2OrderBook('XBTUSD')
        self.l2_order_book.handle_exchange_msg(exceptions_data.partial)

    def test_side_missing_should_raise_exception(self):
        self._assert_orderbook_exception({
            "action": "insert",
            "data": [{
                "symbol": "XBTUSD",
                "id": 15500000000,
                "side": "wrong side",
                "size": 1004,
                "price": 1000000
            }]
        })

    def test_wrong_symbol_should_raise_exception(self):
        self._assert_orderbook_exception({
            "action": "insert",
            "data": [{
                "symbol": "ETHUSD",
                "id": 15500000000,
                "side": 'Sell',
                "size": 1004,
                "price": 1000000
            }]
        })

    def test_no_id_when_insert_should_raise_exception(self):
        self._assert_orderbook_exception({
            "action": "insert",
            "data": [
                {
                    "symbol": "XBTUSD",
                    "side": 'Sell',
                    "id": 123,
                    "size": 1004,
                    "price": 1000000
                },
                {
                    "symbol": "XBTUSD",
                    "side": 'Sell',
                    "size": 1004,
                    "price": 1000000
                }]
        })

    def test_no_price_when_insert_should_raise_exception(self):
        self._assert_orderbook_exception({
            "action": "insert",
            "data": [
                {
                    "symbol": "XBTUSD",
                    "side": 'Sell',
                    "id": 123,
                    "size": 1004
                }]
        })

    def test_when_delete_wrong_id_should_raise_exception(self):
        self._assert_orderbook_exception({
            "action": "delete",
            "data": [
                {
                    "symbol": "XBTUSD",
                    "side": 'Sell',
                    "price": 123,
                    "id": 123,
                    "size": 1004
                }]
        })

    def test_when_update_wrong_id_should_raise_exception(self):
        self._assert_orderbook_exception({
            "action": "update",
            "data": [
                {
                    "symbol": "XBTUSD",
                    "side": 'Sell',
                    "price": 123,
                    "id": 123,
                    "size": 1004
                }]
        })

    def _assert_orderbook_exception(self, exc_msg):
        with self.assertRaises(OrderBookException) as obe:
            self.l2_order_book.handle_exchange_msg(exc_msg)
        self.assertEqual(OrderBookException, type(obe.exception))
