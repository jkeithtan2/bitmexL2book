import motor.motor_asyncio
import pymongo

from src import orderbookconstants as obc


class DbClientFactory:
    def __init__(self):
        pass

    def mongo_client(self):
        return self.DbClientFactoryMongoClient()

    def async_mongo_client(self):
        return self.DbClientFactoryAsyncMongoClient()

    class DbClientFactoryAsyncMongoClient:
        def __init__(self):
            self._mongo_client = motor.motor_asyncio.AsyncIOMotorClient(obc.MONGO_CONNECTION_STRING)
            self._trading_db = self._mongo_client.trading
            self.orderbook_table = self._trading_db.orderbook

        async def persist_to_orderbook_collection(self, orderbook_doc):
            await self.orderbook_table.insert_one(orderbook_doc)

        def close_connection(self):
            self._mongo_client.close()

    class DbClientFactoryMongoClient:
        def __init__(self):
            self._mongo_client = pymongo.MongoClient(
                obc.MONGO_CONNECTION_STRING,
                connect=False)
            self._trading_db = self._mongo_client.trading
            self.orderbook_table = self._trading_db.orderbook

        def persist_to_orderbook_collection(self, orderbook_doc):
            self.orderbook_table.insert_one(orderbook_doc)

        def close_connection(self):
            self._mongo_client.close()
