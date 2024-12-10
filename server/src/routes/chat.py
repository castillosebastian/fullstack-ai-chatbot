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
import ast

chat = APIRouter()
manager = ConnectionManager()
redis = Redis()


# @route   POST /token
# @desc    Route to generate chat token
# @access  Public
# utility
import ast

def extract_msg_value(s: str) -> str:
    # Remove any leading/trailing quotes if present
    # The given string is wrapped with two double quotes at the start and end.
    # For example: ""{'id': '...', 'msg': '...', 'timestamp': '...'}""
    # This will strip those outer quotes if they exist.
    s = s.strip('"')
    
    try:
        # Convert the string representation of a dict into an actual dictionary
        data = ast.literal_eval(s)
        # Safely get the 'msg' value
        return data.get('msg', None)
    except (SyntaxError, ValueError):
        # If the string can't be parsed as a dictionary, return None
        return None


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
            try:
                # 1. Receive message from client with error handling
                data = await websocket.receive_text()
                if not data:
                    continue
                
                # Log received message for debugging
                print(f"Received message: {data}")
                
            except WebSocketDisconnect:
                print("WebSocket disconnected during message reception")
                manager.disconnect(websocket)
                break
            except Exception as e:
                print(f"Error receiving message: {str(e)}")
                await manager.send_personal_message("Error processing your message", websocket)
                continue
            
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
                                
                                # Use the new safe parsing function
                                response_json = {
                                    "msg": extract_msg_value(response_message)
                                } 
                                await manager.send_personal_message(
                                    response_json.get('msg', 'sorry, I could not process that'), 
                                    websocket
                                )
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

def safe_json_loads(json_str: str) -> dict:
    """
    Safely parse a JSON string with common cleanup operations.
    Returns empty dict if parsing fails.
    """
    try:
        # Remove any outer quotes
        json_str = json_str.strip('"\'')
        
        # Handle already escaped quotes - unescape them first
        json_str = json_str.replace('\\"', '"')
        
        # Replace problematic escaped quotes
        json_str = json_str.replace('\"', '"')
        
        # Ensure proper quote escaping
        json_str = json_str.replace('"', '\\"')
        
        # Fix double-escaped quotes
        json_str = json_str.replace('\\\\"', '\\"')
        
        # Parse the JSON
        result = json.loads(json_str)
        
        # Ensure we return a dictionary
        if isinstance(result, str):
            # Try parsing one more time if we got a string
            try:
                result = json.loads(result)
            except:
                return {"msg": result}
        
        return result if isinstance(result, dict) else {"msg": str(result)}
        
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {str(e)}, Input string: {json_str}")
        return {}
    except Exception as e:
        print(f"Unexpected error parsing JSON: {str(e)}")
        return {}
