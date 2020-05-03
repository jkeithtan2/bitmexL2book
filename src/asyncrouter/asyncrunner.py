import asyncio
import functools
import json
import logging
import signal
from src import orderbookconstants as obc
import multiprocessing as mp

from src.clients.cache_client_factory import CacheClientFactory
from src.clients.db_client_factory import DbClientFactory
from src.clients.socketlisteners import AsyncBitMexSocketListener
from src.orderbook.orderbook_msg_receiver import L2OrderbookExcMsgReceiver
from src.orderbook.orderbookcache import OrderBookCache
from src.signalprocessors import async_shutdown_handler


async def exc_message_router(shutdown_event, websocket_queue, l2orderbook_receiver_queue):
    cache_client_factory = CacheClientFactory()
    async_redis_client = await cache_client_factory.async_redis_client()
    orderbook_cache = OrderBookCache(async_redis_client)
    while not shutdown_event.is_set():
        exc_msg = await websocket_queue.get()
        exc_msg = json.loads(exc_msg)
        table = exc_msg.get(obc.EXC_MSG_STRUCT.TABLE)
        if table == obc.TABLES.CACHE_ORDERBOOK:
            await orderbook_cache.async_handle_exchange_message(exc_msg)
        elif table == obc.TABLES.L2_ORDERBOOK:
            await l2orderbook_receiver_queue.put(exc_msg)
    async_redis_client.close()


def setup_async_runner():
    loop = asyncio.get_event_loop()
    shutdown_event = mp.Event()
    db_client_factory = DbClientFactory()
    async_websocket_queue = asyncio.Queue()
    async_l2orderbook_receiver_queue = asyncio.Queue()
    async_bitmex_socket = AsyncBitMexSocketListener(obc.SYMBOLS,
                                                    async_websocket_queue,
                                                    shutdown_event)
    async_l2orderbook_receiver = L2OrderbookExcMsgReceiver(async_l2orderbook_receiver_queue,
                                                           db_client_factory,
                                                           shutdown_event,
                                                           obc.SYMBOLS)
    exc_msg_router_task = loop.create_task(
        exc_message_router(shutdown_event, async_websocket_queue, async_l2orderbook_receiver_queue)
    )
    loop.create_task(
        async_bitmex_socket.get_orderbook_feed(loop)
    )
    async_l2orderbook_task = loop.create_task(
        async_l2orderbook_receiver.async_run()
    )
    graceful_shutdown_tasks = [exc_msg_router_task, async_l2orderbook_task]
    signals_to_handle = [signal.SIGTERM, signal.SIGINT]
    for s in signals_to_handle:
        loop.add_signal_handler(
            s,
            functools.partial(
                asyncio.create_task, async_shutdown_handler(shutdown_event, graceful_shutdown_tasks, loop)
            )
        )
    loop.run_forever()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    setup_async_runner()
