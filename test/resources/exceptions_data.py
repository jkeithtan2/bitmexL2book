partial = {
    "table": "orderBookL2",
    "action": "partial",
    "keys": ["symbol", "id", "side"],
    "types": {
        "symbol": "symbol",
        "id": "long",
        "side": "symbol",
        "size": "long",
        "price": "float"
    },
    "foreignKeys": {
        "symbol": "instrument",
        "side": "side"
    },
    "attributes": {
        "symbol": "parted",
        "id": "sorted"
    },
    "filter": {
        "symbol": "XBTUSD"
    },
    "data": [{
        "symbol": "XBTUSD",
        "id": 15500000000,
        "side": "Sell",
        "size": 1004,
        "price": 1000000
    }]
}
