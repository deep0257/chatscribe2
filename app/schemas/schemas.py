from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, EmailStr


# User schemas
class UserBase(BaseModel):
    username: str
    email: EmailStr


class UserCreate(UserBase):
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Document schemas
class DocumentBase(BaseModel):
    filename: str
    original_filename: str
    file_type: str


class DocumentCreate(DocumentBase):
    file_path: str
    file_size: int
    content: Optional[str] = None


class Document(DocumentBase):
    id: int
    file_size: int
    uploaded_at: datetime
    user_id: int

    class Config:
        from_attributes = True


# Chat message schemas
class ChatMessageBase(BaseModel):
    content: str
    is_user: bool


class ChatMessageCreate(ChatMessageBase):
    session_id: int


class ChatMessage(ChatMessageBase):
    id: int
    created_at: datetime
    session_id: int

    class Config:
        from_attributes = True


# Chat session schemas
class ChatSessionBase(BaseModel):
    title: str


class ChatSessionCreate(ChatSessionBase):
    document_id: int


class ChatSession(ChatSessionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    user_id: int
    document_id: int
    messages: List[ChatMessage] = []

    class Config:
        from_attributes = True


# API response schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class ChatRequest(BaseModel):
    message: str
    session_id: int


class ChatResponse(BaseModel):
    response: str
    session_id: int
