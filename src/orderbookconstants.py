class dotdict(dict):
    __getattr__ = dict.get
    __setattr__ = dict.__setitem__
    __delattr__ = dict.__delitem__


SYMBOLS = ['XBTUSD', 'XRPUSD', 'ETHUSD']


DEFAULT_REDIS_SYNC_HOST = 'localhost'
DEFAULT_REDIS_ASYNC_HOST = 'redis://localhost'

BITMEX_WS_ENDPOINT = 'wss://testnet.bitmex.com/realtime?subscribe='

DEFAULT_POLLING_TIME = 0.02

DEFAULT_JOIN_TIME = 1

STOP_Q_MSG = '_END'

TABLES = dotdict({
    'CACHE_ORDERBOOK': 'orderBook10',
    'L2_ORDERBOOK': 'orderBookL2'
})

EXC_MSG_STRUCT = dotdict({
    'TABLE': 'table',
    'DATA': 'data',
    'SYMBOL': 'symbol',
    'ACTION': 'action',
    'KEYS': 'keys'
})

EXC_ACTION_TYPE = dotdict({
    'UPDATE': 'update',
    'INSERT': 'insert',
    'PARTIAL': 'partial',
    'DELETE': 'delete'
})

EXC_DATA_FIELD = dotdict({
    'SIDE': 'side',
    'ID': 'id',
    'SIZE': 'size',
    'PRICE': 'price',
    'SYMBOL': 'symbol'
})

EXC_MSG_SIDE = dotdict({
    'BIDS': 'Buy',
    'ASKS': 'Sell'
})
