import json
import logging

from src import orderbookconstants as obc
from src.utils import get_symbol_from_exc_msg


class OrderBookCache:
    def __init__(self, client):
        self.has_received_partial = False
        self.client = client

    def handle_exchange_message(self, message: dict):
        symbol, cache_data = self._should_cache(message)
        if not symbol or not cache_data:
            logging.error(f'symbol or cache_data is empty for {message}')
        else:
            self.client.set(symbol, cache_data)

    async def async_handle_exchange_message(self, message: dict):
        symbol, cache_data = self._should_cache(message)
        if not symbol or not cache_data:
            logging.error(f'symbol or cache_data is empty for {message}')
        else:
            await self.client.set(f'async||{symbol}', cache_data)

    def _should_cache(self, message: dict):
        data = message.get(obc.EXC_MSG_STRUCT.DATA)
        action = message.get(obc.EXC_MSG_STRUCT.ACTION)
        try:
            symbol = get_symbol_from_exc_msg(message)
            if action == obc.EXC_ACTION_TYPE.PARTIAL:
                self.has_received_partial = True
            if (action == obc.EXC_ACTION_TYPE.PARTIAL or action == obc.EXC_ACTION_TYPE.UPDATE) \
                    and self.has_received_partial:
                return symbol, json.dumps(data)
        except Exception as e:
            logging.error(str(e))
        return None, None
