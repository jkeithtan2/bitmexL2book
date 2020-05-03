## Before running
pip install -r requirements.txt

ensure there is a 'MONGO_CONNECTION_STRING' 

## BitMex Websocket:

orderBook10 (top 10 orders on each side) is used for caching purposes and orderBookL2 is used 
to recreate the full l2 orderbook

The example BitMex python websocket code has been extended to allow for unlimited symbols but only listens
to orderBookL2 and orderBook10, although that can also be expanded

Redis is used locally, mongoDb is hosted on an online cluster

2 architectures for generating the orderbook have been coded for the purposes of comparing
readability, understandability and speed. Both architectures are designed as a set of tasks chained
together where the output from a task feeds in as the input for another task. This can be thought of similar
to unix pipes.
        

The first architecutre uses a separate thread for the websocket listener, similar to the bitmex example. Two processes
will be created, one to listener on the websocket and write to cache(redis) and the other to generate a
full l2 orderbook and persist it to mongo. Exchange messages are passed through in memory message queues

Process 1: Threaded websocket listener and writer to redis. Communicates with process 2 through a process queue
Process 2: recreates orderbook based on exchange message and persists them to mongoDb

Process1 : Websocket -> orderBook10 -> redis
Prcoess2:   |-> orderbookL2 -> mongoDb


The second architecture uses 1 process but is async in nature. 3 tasks have been resigered with the async loop,
an exchange_message_router task, the websocket listener task and a task to generate the l2 orderbook and persist it
in mongoDb


## Numbers

Numbers are approximate.

#### orderbook structure
The L2OrderBook structure is that of a sorted dictionary. This inccurs a O(lgN) cost for insertion and update and O(1)
cost for deletion. In the example bitmex websocket program, insertion has a O(1) cost while deletion and update has 
a O(n) cost, furthermore in order to perserve anorderbook structure, the list has to resorted. 

The sorted dictionary structure took ~140ms to process 176 l2 orderbook exchange messages and recreate the orderbook. 
Using a list as in the example and recreating the orderbook would take ~2200ms for the same 176 messages. This can be
seen in 'test_l2orderbook.py'

#### websocket to redis threaded architecture
Messages are usually received with a 100-300 ms lag. i.e. The message is received in the websocket thread about 100 - 300ms
later than the timestamp of the message. Messages usually take an additinal 100ms-1000m of time before they are
written to redis

#### websocket to redis async architecture
Messages are usually received with a 130-200ms second lag. Message usually take an adition 20-100ms before they
are written to redis

## Further things that might improve speed
* development time vs run time
* use cython/c++ with static typing (experiments have shown this can give a >20X depending on the computation performed)
* compile python to c++(https://shedskin.readthedocs.io/en/latest/)
* knowing the 'hotpath' will determin what needs to be sped up
* Save orderBook10 as a string, use string manipulation to determine key rather than use json transformation
* Try different json libraries, in my experience the performance varies depending on the original string
* Do we really need another process for the threaded architecture?
* Async process with a process pool
* tweak garbage collection, stop the world times, experiment and do own garbage collection


## Readability and understandability
My perference would be towards an async style of coding as i think its easier to reason about

