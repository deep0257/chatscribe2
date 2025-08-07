from fastapi import APIRouter, Request, Depends, HTTPException, UploadFile, File, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from typing import Optional
from app.core.database import get_db
from app.api.deps import get_current_user_from_cookie, require_auth
from app.models.models import User
from app.crud.crud import get_user_documents, get_user_chat_sessions, get_document, get_chat_session, get_session_messages, create_document, create_chat_session, create_chat_message, update_chat_session_timestamp
from app.schemas.schemas import DocumentCreate, ChatSessionCreate, ChatMessageCreate
from app.core.file_processor import file_processor
from app.core.alternative_ai_service import alternative_ai_service as ai_service
from app.core.config import settings

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
async def home(request: Request, user: Optional[User] = Depends(get_current_user_from_cookie)):
    """Home page - landing page with login/signup"""
    if user:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("home.html", {"request": request})


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, user: Optional[User] = Depends(get_current_user_from_cookie)):
    """Login page"""
    if user:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/signup", response_class=HTMLResponse)
async def signup_page(request: Request, user: Optional[User] = Depends(get_current_user_from_cookie)):
    """Signup page"""
    if user:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("signup.html", {"request": request})


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Main dashboard - shows documents and recent chats"""
    documents = get_user_documents(db, user.id)
    recent_chats = get_user_chat_sessions(db, user.id)[:10]  # Last 10 chats
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "documents": documents,
        "recent_chats": recent_chats
    })


@router.post("/upload")
async def upload_document_web(
    request: Request,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Handle document upload from web form"""
    try:
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        if not file_processor.is_allowed_file(file.filename):
            raise HTTPException(
                status_code=400, 
                detail=f"File type not allowed. Allowed types: {', '.join(settings.ALLOWED_EXTENSIONS)}"
            )
        
        # Check file size
        file_content = await file.read()
        if len(file_content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {settings.MAX_FILE_SIZE / (1024*1024):.1f} MB"
            )
        
        # Process file
        file_path, unique_filename, extracted_text = file_processor.process_uploaded_file(
            file_content, file.filename
        )
        
        if not file_path or not extracted_text:
            raise HTTPException(status_code=500, detail="Failed to process file")
        
        # Create document record
        document_create = DocumentCreate(
            filename=unique_filename,
            original_filename=file.filename,
            file_path=file_path,
            file_type=file.filename.split('.')[-1].lower(),
            file_size=len(file_content),
            content=extracted_text
        )
        
        document = create_document(db, document_create, user.id)
        
        # Process document for AI
        try:
            ai_service.process_document_content(extracted_text, document.id)
        except Exception as e:
            print(f"Error processing document for AI: {e}")
        
        return RedirectResponse(url=f"/document/{document.id}", status_code=302)
    
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": str(e),
            "user": user
        })


@router.get("/document/{document_id}", response_class=HTMLResponse)
async def document_detail(
    document_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Document detail page with chat interface"""
    document = get_document(db, document_id, user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # Get chat sessions for this document
    chat_sessions = [session for session in get_user_chat_sessions(db, user.id) 
                    if session.document_id == document_id]
    
    return templates.TemplateResponse("document.html", {
        "request": request,
        "user": user,
        "document": document,
        "chat_sessions": chat_sessions
    })


@router.get("/chat/{session_id}", response_class=HTMLResponse)
async def chat_session(
    session_id: int,
    request: Request,
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Chat session page"""
    session = get_chat_session(db, session_id, user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    messages = get_session_messages(db, session_id)
    document = get_document(db, session.document_id, user.id)
    
    # Get all user's chat sessions for sidebar
    all_sessions = get_user_chat_sessions(db, user.id)
    
    return templates.TemplateResponse("chat.html", {
        "request": request,
        "user": user,
        "session": session,
        "document": document,
        "messages": messages,
        "all_sessions": all_sessions
    })


@router.post("/chat/{session_id}/send")
async def send_message(
    session_id: int,
    request: Request,
    message: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Send message in chat session"""
    session = get_chat_session(db, session_id, user.id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    
    try:
        # Get existing chat history
        history = get_session_messages(db, session_id)
        chat_history = []
        for msg in history:
            if msg.is_user:
                chat_history.append((msg.content, ""))
            else:
                if chat_history:
                    chat_history[-1] = (chat_history[-1][0], msg.content)
        
        # Get AI response
        response = ai_service.chat_with_document(session.document_id, message, chat_history)
        
        # Save messages
        user_message = ChatMessageCreate(
            content=message,
            is_user=True,
            session_id=session_id
        )
        create_chat_message(db, user_message)
        
        ai_message = ChatMessageCreate(
            content=response,
            is_user=False,
            session_id=session_id
        )
        create_chat_message(db, ai_message)
        
        # Update session timestamp
        update_chat_session_timestamp(db, session_id)
        
        return RedirectResponse(url=f"/chat/{session_id}", status_code=302)
        
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Failed to send message: {str(e)}",
            "user": user
        })


@router.post("/document/{document_id}/new-chat")
async def start_new_chat_web(
    document_id: int,
    request: Request,
    message: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_auth)
):
    """Start new chat session from web"""
    document = get_document(db, document_id, user.id)
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    try:
        # Create new chat session
        chat_title = ai_service.get_chat_title(message)
        session_create = ChatSessionCreate(
            title=chat_title,
            document_id=document_id
        )
        session = create_chat_session(db, session_create, user.id)
        
        # Send first message
        return await send_message(session.id, request, message, db, user)
        
    except Exception as e:
        return templates.TemplateResponse("error.html", {
            "request": request,
            "error": f"Failed to start chat: {str(e)}",
            "user": user
        })
