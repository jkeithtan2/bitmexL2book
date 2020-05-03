import asyncio
import functools
import logging
import signal


def sigterm_handler(shutdown_event, signal_number, stack_frame):
    shutdown_event.set()


def init_signals(shutdown_event):
    handler = functools.partial(sigterm_handler, shutdown_event)
    signal.signal(signal.SIGTERM, handler)
    signal.signal(signal.SIGINT, handler)


async def async_shutdown_handler(shutdown_event, graceful_shutdown_tasks, loop):
    logging.info(f"Received exit signal")
    shutdown_event.set()
    await asyncio.gather(*graceful_shutdown_tasks)
    tasks = [t for t in asyncio.all_tasks() if t is not
             asyncio.current_task()]
    [task.cancel() for task in tasks]
    loop.stop()




