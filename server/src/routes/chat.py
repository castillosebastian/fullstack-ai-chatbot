import os
import json
from fastapi import APIRouter, FastAPI, WebSocket, WebSocketDisconnect, Request, Depends, HTTPException
import uuid
from ..socket.connection import ConnectionManager
from ..socket.utils import get_token
import time
from ..redis.producer import Producer
from ..redis.config import Redis
from ..schema.chat import Chat
from rejson import Path
from ..redis.stream import StreamConsumer
from ..redis.cache import Cache
from pydantic import BaseModel
import asyncio

chat = APIRouter()
manager = ConnectionManager()
redis = Redis()


# @route   POST /token
# @desc    Route to generate chat token
# @access  Public


@chat.post("/token")
async def token_generator(name: str, request: Request):
    token = str(uuid.uuid4())

    if name == "":              
        raise HTTPException(status_code=400, detail={
            "loc": "name",  "msg": "Enter a valid name"})

    # Create nee chat session
    json_client = redis.create_rejson_connection()
    chat_session = Chat(
        token=token,
        messages=[],
        name=name
    )

    print(chat_session.model_dump())

    # Store chat session in redis JSON with the token as key
    json_client.jsonset(str(token), Path.rootPath(), chat_session.model_dump())

    # Set a timeout for redis data
    redis_client = await redis.create_connection()
    await redis_client.expire(str(token), 3600)

    return chat_session.model_dump()


# @route   POST /refresh_token
# @desc    Route to refresh token
# @access  Public


@chat.get("/refresh_token")
async def refresh_token(request: Request, token: str):
    json_client = redis.create_rejson_connection()
    cache = Cache(json_client)
    data = await cache.get_chat_history(token)

    if data == None:
        raise HTTPException(
            status_code=400, detail="Session expired or does not exist")
    else:
        return data


# @route   Websocket /chat
# @desc    Socket for chat bot
# @access  Public

@chat.websocket("/chat")
async def websocket_endpoint(websocket: WebSocket, token: str = Depends(get_token)):
    await manager.connect(websocket)
    redis_client = await redis.create_connection()
    producer = Producer(redis_client)
    consumer = StreamConsumer(redis_client)

    try:
        while True:
            # 1. Receive message from client
            data = await websocket.receive_text()
            
            # 2. Send to message channel
            stream_data = {}
            stream_data[str(token)] = str(data)
            await producer.add_to_stream(stream_data, "message_channel")
            
            # 3. Wait for response with a timeout
            response = None
            max_retries = 10
            retry_count = 0
            
            while retry_count < max_retries:
                response = await consumer.consume_stream(
                    stream_channel="response_channel",
                    count=1,
                    block=1000  # Wait 1 second before trying again
                )
                
                if response:
                    for stream, messages in response:
                        for message in messages:
                            response_token = [k.decode('utf-8')
                                            for k, v in message[1].items()][0]
                            
                            if token == response_token:
                                response_message = [v.decode('utf-8')
                                                  for k, v in message[1].items()][0]
                                
                                # Fix invalid JSON
                                fixed_json = response_message.replace("'", "\"").strip('"')
                                response_json = json.loads(fixed_json)                                
                                await manager.send_personal_message(response_json.get('msg', 'sorry, I could not process that'), websocket)
                                await consumer.delete_message(
                                    stream_channel="response_channel",
                                    message_id=message[0].decode('utf-8')
                                )
                                break
                    break
                
                retry_count += 1
                await asyncio.sleep(0.1)  # Small delay between retries

    except WebSocketDisconnect:
        manager.disconnect(websocket)


class ChatMessage(BaseModel):
    message: str

@chat.post("/chat")
async def chat_endpoint(message: ChatMessage):
    try:
        # Here you would typically process the message and generate a response
        # For now, we'll just echo the message back
        return {"response": f"You said: {message.message}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
