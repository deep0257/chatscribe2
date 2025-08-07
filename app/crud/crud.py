from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.models import User, Document, ChatSession, ChatMessage
from app.schemas.schemas import UserCreate, DocumentCreate, ChatSessionCreate, ChatMessageCreate
from app.core.security import get_password_hash, verify_password


# User CRUD
def get_user(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, user: UserCreate) -> User:
    hashed_password = get_password_hash(user.password)
    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# Document CRUD
def create_document(db: Session, document: DocumentCreate, user_id: int) -> Document:
    db_document = Document(**document.dict(), user_id=user_id)
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


def get_user_documents(db: Session, user_id: int) -> List[Document]:
    return db.query(Document).filter(Document.user_id == user_id).order_by(Document.uploaded_at.desc()).all()


def get_document(db: Session, document_id: int, user_id: int) -> Optional[Document]:
    return db.query(Document).filter(Document.id == document_id, Document.user_id == user_id).first()


# Chat Session CRUD
def create_chat_session(db: Session, session: ChatSessionCreate, user_id: int) -> ChatSession:
    db_session = ChatSession(**session.dict(), user_id=user_id)
    db.add(db_session)
    db.commit()
    db.refresh(db_session)
    return db_session


def get_user_chat_sessions(db: Session, user_id: int) -> List[ChatSession]:
    return db.query(ChatSession).filter(ChatSession.user_id == user_id).order_by(ChatSession.updated_at.desc()).all()


def get_chat_session(db: Session, session_id: int, user_id: int) -> Optional[ChatSession]:
    return db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == user_id).first()


def update_chat_session_timestamp(db: Session, session_id: int):
    db.query(ChatSession).filter(ChatSession.id == session_id).update({"updated_at": "now()"})
    db.commit()


# Chat Message CRUD
def create_chat_message(db: Session, message: ChatMessageCreate) -> ChatMessage:
    db_message = ChatMessage(**message.dict())
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


def get_session_messages(db: Session, session_id: int) -> List[ChatMessage]:
    return db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
