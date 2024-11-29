class StreamConsumer:
    def __init__(self, redis_client):
        self.redis_client = redis_client

    async def consume_stream(self, stream_channel: str, count: int, block: int = None):
        try:
            response = await self.redis_client.xread(
                streams={stream_channel: '$'},
                count=count,
                block=block
            )
            return response
        except Exception as e:
            print(f"Error consuming stream: {e}")
            return None

    async def delete_message(self, stream_channel, message_id):
        await self.redis_client.xdel(stream_channel, message_id)
