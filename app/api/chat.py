from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user_from_token
from app.models.models import User
from app.schemas.schemas import ChatRequest, ChatResponse
from app.crud.crud import get_chat_session, get_session_messages, create_chat_session, create_chat_message, update_chat_session_timestamp, get_user_chat_sessions, get_document
from app.core.alternative_ai_service import alternative_ai_service as ai_service

router = APIRouter()


@router.post("/start", response_model=ChatResponse)
async def start_new_chat(
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Start a new chat session"""
    # Get document ID and validate
    document_id = chat_request.session_id
    if not document_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document ID required"
        )
    
    # Verify the document exists and belongs to the user
    document = get_document(db, document_id, current_user.id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )
    
    # Create new chat session
    chat_title = ai_service.get_chat_title(chat_request.message)
    chat_session = create_chat_session(db, {"title": chat_title, "document_id": document_id}, current_user.id)
    
    # Chat with document
    response = ai_service.chat_with_document(document_id, chat_request.message, [])
    
    # Record messages
    create_chat_message(db, {"content": chat_request.message, "is_user": True, "session_id": chat_session.id})
    create_chat_message(db, {"content": response, "is_user": False, "session_id": chat_session.id})
    
    return {"response": response, "session_id": chat_session.id}


@router.post("/message")
async def send_chat_message(
    chat_request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Chat with document"""
    session_id = chat_request.session_id
    message = chat_request.message
    
    # Validate session
    chat_session = get_chat_session(db, session_id, current_user.id)
    if not chat_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found"
        )
    
    document_id = chat_session.document_id
    
    # Get existing chat history
    history = get_session_messages(db, session_id)
    chat_history = [(msg.content, "") if msg.is_user else ("", msg.content) for msg in history]
    
    # Chat with document
    response = ai_service.chat_with_document(document_id, message, chat_history)
    
    # Record messages
    create_chat_message(db, {"content": message, "is_user": True, "session_id": session_id})
    create_chat_message(db, {"content": response, "is_user": False, "session_id": session_id})
    update_chat_session_timestamp(db, session_id)
    
    return {"response": response, "session_id": session_id}


@router.get("/sessions", response_model=List[ChatResponse])
async def get_user_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user_from_token)
):
    """Get all chat sessions for user"""
    chats = get_user_chat_sessions(db, current_user.id)
    return [{"title": chat.title, "session_id": chat.id, "created_at": chat.created_at} for chat in chats]
