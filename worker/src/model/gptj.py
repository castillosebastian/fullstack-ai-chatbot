import os
from dotenv import load_dotenv
import requests
import json
from datetime import datetime

# from pathlib import Path
# import sys
# project_root = str(Path(__file__).parents[3])  # Go up 3 levels to reach project root
# sys.path.append(project_root)
# from server.src.redis.config import Redis
# from server.src.schema.chat import Message

# Comment out these imports when running as standalone
from ..redis.config import Redis
from ..redis.producer import Producer
from ..schema.chat import Message


from openai import AzureOpenAI

load_dotenv()
redis = Redis()

class GPT:
    def __init__(self):
        self.client = AzureOpenAI(
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        self.deployment_name = os.getenv("AZURE_OPENAI_LLM_DEPLOYMENT")
        self.json_client = redis.create_rejson_connection()

    async def initialize(self):
        self.redis_client = await redis.create_connection()
        self.producer = Producer(self.redis_client)
        return self

    async def query(self, input: str) -> str:
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "user", "content": f"{input} Bot:"}
                ],
                max_tokens=250,
                temperature=0.7,
            )
            generated_text = response.choices[0].message.content
            res = str(generated_text.split("Human:")[0]).strip("\n").strip()
            
            return res

        except Exception as e:
            print(f"Error in query: {str(e)}")
            raise

# Add test code to run when file is executed directly
if __name__ == "__main__":
    gpt = GPT()
    response = gpt.query("Hello, what can you do for me?")
    print("Response:", response)
