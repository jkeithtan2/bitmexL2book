import unittest
import json
import src.orderbookconstants as obc
from sortedcontainers import SortedDict
from src.orderbook.l2orderbook import L2OrderBook
import time


def current_milli_time():
    return int(round(time.time() * 1000))


class TestReplayDataFeed(unittest.TestCase):

    def test_orderbook_should_be_similar_to_orderbook_from_bitmex_feed(self):
        et_count = 0
        ft_count = 0
        expected_orderbooks = []
        actual_orderbooks = []
        symbol = None

        with open('resources/expected_result.txt') as et:
            start_et = current_milli_time()
            line = et.readline()
            while line:
                orderbook = json.loads(line)
                if not symbol:
                    symbol = orderbook[0][obc.EXC_DATA_FIELD.SYMBOL]
                sorted_orderbook_dict = {
                    'bids': SortedDict(lambda x: -x),
                    'asks': SortedDict()
                }
                for order in orderbook:
                    order_size = order[obc.EXC_DATA_FIELD.SIZE]
                    order_price = order[obc.EXC_DATA_FIELD.PRICE]
                    side = 'bids' if order[obc.EXC_DATA_FIELD.SIDE] == 'Buy' else 'asks'
                    sorted_orderbook_dict[side][order_price] = order_size
                expected_orderbooks.append({
                    'symbol': symbol,
                    'bids': list(sorted_orderbook_dict['bids'].items()),
                    'asks': list(sorted_orderbook_dict['asks'].items())
                })
                ft_count += 1
                line = et.readline()
            end_et = current_milli_time()

        actual_l2_orderbook = L2OrderBook(symbol)
        with open('resources/orderbookL2_feed_test.txt') as ft:
            start_ft = current_milli_time()
            feed = ft.readline()
            while feed:
                actual_l2_orderbook.handle_exchange_msg(json.loads(feed))
                actual_orderbooks.append(actual_l2_orderbook.orderbook_repr())
                et_count += 1
                feed = ft.readline()
            end_ft = current_milli_time()

        print(end_et - start_et)
        print(end_ft - start_ft)
        self.assertEqual(len(expected_orderbooks), len(actual_orderbooks))
        self.assertEqual(json.dumps(expected_orderbooks), json.dumps(actual_orderbooks))

