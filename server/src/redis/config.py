import os
from dotenv import load_dotenv
import aioredis
from rejson import Client


load_dotenv()


class Redis():
    def __init__(self):
        """initialize  connection """
        self.REDIS_URL = os.environ['REDIS_URL']
        self.REDIS_PASSWORD = os.environ['REDIS_PASSWORD']
        self.REDIS_USER = os.environ['REDIS_USER']
        self.connection_url = f"redis://{self.REDIS_USER}:{self.REDIS_PASSWORD}@{self.REDIS_URL}"

    async def create_connection(self):
        self.connection = aioredis.from_url(
            self.connection_url, db=0)

        return self.connection

    def create_rejson_connection(self):
        # Extract host and port from REDIS_URL
        host, port = self.REDIS_URL.split(':')
        
        self.redisJson = Client(
            host=host,
            port=int(port),
            decode_responses=True,
            username=self.REDIS_USER,
            password=self.REDIS_PASSWORD
        )

        return self.redisJson
