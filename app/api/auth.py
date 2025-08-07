from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import create_access_token
from app.core.config import settings
from app.schemas.schemas import UserCreate, UserLogin, Token
from app.crud.crud import create_user, authenticate_user, get_user_by_username, get_user_by_email

router = APIRouter()


@router.post("/signup", response_model=Token)
async def signup(user: UserCreate, db: Session = Depends(get_db)):
    """Create new user account"""
    # Check if user already exists
    if get_user_by_username(db, user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    if get_user_by_email(db, user.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    db_user = create_user(db, user)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Authenticate user and return token"""
    user = authenticate_user(db, user_credentials.username, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/web/login")
async def web_login(request: Request, response: Response, db: Session = Depends(get_db)):
    """Web-based login that sets cookie"""
    form = await request.form()
    username = form.get("username")
    password = form.get("password")
    
    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password required"
        )
    
    user = authenticate_user(db, username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Set cookie and redirect
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=False  # Set to True in production with HTTPS
    )
    
    return response


@router.post("/web/signup")
async def web_signup(request: Request, response: Response, db: Session = Depends(get_db)):
    """Web-based signup that sets cookie"""
    form = await request.form()
    username = form.get("username")
    email = form.get("email")
    password = form.get("password")
    
    if not username or not email or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username, email, and password required"
        )
    
    # Check if user already exists
    if get_user_by_username(db, username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    if get_user_by_email(db, email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    user_create = UserCreate(username=username, email=email, password=password)
    db_user = create_user(db, user_create)
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.username}, expires_delta=access_token_expires
    )
    
    # Set cookie and redirect
    response = RedirectResponse(url="/dashboard", status_code=302)
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=False  # Set to True in production with HTTPS
    )
    
    return response


@router.post("/logout")
async def logout():
    """Logout user by clearing cookie"""
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie(key="access_token")
    return response
