import json
from collections import namedtuple

from sortedcontainers import SortedDict
import logging
from src import orderbookconstants as obc
from src.exceptions import OrderBookException

Order = namedtuple('Order', ['id', 'size', 'price', 'side'])


# need id dict because delete and update does not give price only id
# For those curious, the id on an orderBookL2_25 or orderBookL2 entry is a composite of price and symbol,
# and is always unique for any given price level. It should be used to apply update and delete actions.


class L2OrderBook:
    def __init__(self, symbol):
        self.symbol = symbol
        self._init_orderbook()
        self.curr_exc_msg = None
        self.has_received_partial = False

    def _init_orderbook(self):
        self.keys = []
        self.id_to_orders = {
            'bids': {},
            'asks': {}
        }
        self._orderbook = {
            'bids': SortedDict(lambda x: -x),
            'asks': SortedDict()
        }

    def orderbook_repr(self):
        return {
            'symbol': self.symbol,
            'bids': list(self._orderbook['bids'].items()),
            'asks': list(self._orderbook['asks'].items())
        }

    def handle_exchange_msg(self, exchange_msg: dict):
        self.curr_exc_msg = json.dumps(exchange_msg)
        action = exchange_msg[obc.EXC_MSG_STRUCT.ACTION]
        orders = exchange_msg[obc.EXC_MSG_STRUCT.DATA]
        if not self.has_received_partial:
            if action == obc.EXC_ACTION_TYPE.PARTIAL:
                self._do_partial(exchange_msg)
            else:
                logging.info(f'{self.curr_exc_msg} received before orderbook partial')
        else:
            if action == obc.EXC_ACTION_TYPE.INSERT:
                self._do_orders_insert(orders)
            elif action == obc.EXC_ACTION_TYPE.DELETE:
                self._do_orders_delete(orders)
            elif action == obc.EXC_ACTION_TYPE.UPDATE:
                self._do_orders_update(orders)
            else:
                logging.error(f'partial has been received, '
                              f'msg {self.curr_exc_msg} invalid action')

    def _do_partial(self, orderbookl2_partial_action: dict):
        self.keys.extend(
            orderbookl2_partial_action.get(obc.EXC_MSG_STRUCT.KEYS)
        )
        for order in orderbookl2_partial_action[obc.EXC_MSG_STRUCT.DATA]:
            self._order_insert(order)
        self.has_received_partial = True

    def _do_orders_update(self, orders: list):
        try:
            for order in orders:
                order = self.get_order_params(order)
                price_of_id = self.id_to_orders[order.side][order.id]
                self._orderbook[order.side][price_of_id] = order.size
        except KeyError:
            raise OrderBookException(
                f'cannot update orderbook, exc msg f{self.curr_exc_msg} invalid'
            )

    def _do_orders_delete(self, orders: list):
        try:
            for order in orders:
                order = self.get_order_params(order)
                price_of_id = self.id_to_orders[order.side][order.id]
                self._orderbook[order.side].pop(price_of_id)
                self.id_to_orders[order.side].pop(order.id)
        except KeyError:
            raise OrderBookException(
                f'cannot delete from orderbook, exc msg f{self.curr_exc_msg} invalid'
            )

    def _do_orders_insert(self, orders: list):
        for order in orders:
            self._order_insert(order)

    def _order_insert(self, order: dict):
        order = self.get_order_params(order)
        try:
            self.id_to_orders[order.side][order.id] = order.price
            self._orderbook[order.side][order.price] = order.size
        except (TypeError, KeyError):
            raise OrderBookException(f'id {order.id} or price {order.price} is invalid for {self.curr_exc_msg}')

    def get_order_params(self, order):
        order_symbol = order.get(obc.EXC_DATA_FIELD.SYMBOL)
        if order_symbol != self.symbol:
            raise OrderBookException(f'order symbol {self.curr_exc_msg} not same as orderbook symbol {self.symbol}')
        try:
            order_side = order[obc.EXC_DATA_FIELD.SIDE]
            order_id = order[obc.EXC_DATA_FIELD.ID]
        except KeyError:
            raise OrderBookException(f'{self.curr_exc_msg} missing side and/or id')
        order_size = order.get(obc.EXC_DATA_FIELD.SIZE)
        order_price = order.get(obc.EXC_DATA_FIELD.PRICE)
        side = self.get_book_side(order_side)
        return Order(order_id, order_size, order_price, side)

    def get_book_side(self, order_side):
        if order_side == obc.EXC_MSG_SIDE.BIDS:
            return 'bids'
        elif order_side == obc.EXC_MSG_SIDE.ASKS:
            return 'asks'
        else:
            raise OrderBookException(f'{self.curr_exc_msg} side is neither bid or ask')
