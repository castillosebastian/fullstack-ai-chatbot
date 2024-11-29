from datetime import datetime
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid


class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))  # Convert UUID to string
    msg: str
    timestamp: str = str(datetime.now())

