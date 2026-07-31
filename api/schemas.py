from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ProductMentions(BaseModel):
    product_name: str
    mention_count: int

class ChannelActivity(BaseModel):
    date: datetime
    message_count: int

class MessageResult(BaseModel):
    message_id: int
    channel_title: str
    message_text: Optional[str]
    message_date: datetime

class VisualStats(BaseModel):
    image_category: str
    total_count: int
    avg_views: float