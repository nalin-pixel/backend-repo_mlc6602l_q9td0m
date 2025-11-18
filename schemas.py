"""
Database Schemas

Define your MongoDB collection schemas here using Pydantic models.
These schemas are used for data validation in your application.

Each Pydantic model represents a collection in your database.
Model name is converted to lowercase for the collection name:
- User -> "user" collection
- Product -> "product" collection
- BlogPost -> "blogs" collection
"""

from pydantic import BaseModel, Field
from typing import Optional

# Event, Message, and Membership schemas for the app

class Event(BaseModel):
    host_name: str = Field(..., description="Name of the event host")
    activity: str = Field(..., description="Activity or event title")
    lat: float = Field(..., description="Latitude of the event")
    lng: float = Field(..., description="Longitude of the event")
    attendees: int = Field(0, ge=0, description="Number of people going")

class Message(BaseModel):
    event_id: str = Field(..., description="ID of the event this message belongs to")
    user: str = Field(..., description="Sender display name")
    text: str = Field(..., description="Message content")

class Membership(BaseModel):
    event_id: str = Field(..., description="ID of the event")
    user: str = Field(..., description="Member display name")

# Example schemas kept for reference (not used by this app)
class User(BaseModel):
    name: str = Field(..., description="Full name")
    email: str = Field(..., description="Email address")
    address: str = Field(..., description="Address")
    age: Optional[int] = Field(None, ge=0, le=120, description="Age in years")
    is_active: bool = Field(True, description="Whether user is active")

class Product(BaseModel):
    title: str = Field(..., description="Product title")
    description: Optional[str] = Field(None, description="Product description")
    price: float = Field(..., ge=0, description="Price in dollars")
    category: str = Field(..., description="Product category")
    in_stock: bool = Field(True, description="Whether product is in stock")
