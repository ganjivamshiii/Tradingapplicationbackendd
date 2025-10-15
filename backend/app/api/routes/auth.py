from fastapi import APIRouter , Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta, datetime
from ...core.database import get_db
from ...core.security import (
    get_current_user,
    verify_password,
    get_password_hash,
    create_access_token,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from ...models.user import User
from ...schemas.user import UserCreate, UserResponse, Token , UserLogin

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    print("🚀 [DEBUG] /register endpoint hit")
    print(f"📦 Received data: {user_data}")
    
    existing_user = db.query(User).filter(
        (User.email == user_data.email) | (User.username == user_data.username)
    ).first()
    
    if existing_user:
        if existing_user.email == user_data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_password,
        username=user_data.username,
        full_name=user_data.full_name,
        initial_capital=user_data.initial_capital,
        risk_tolerance=user_data.risk_tolerance
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    print(f"✅ User registered: {new_user.username}")
    return new_user


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    print("🚀 [DEBUG] /login endpoint hit")
    print(f"📦 Login attempt for username: {form_data.username}")

    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        print("❌ Login failed: invalid credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        print("❌ Login failed: inactive user")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    user.last_login = datetime.utcnow()
    db.commit()

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires
    )

    print(f"✅ Login successful, token generated for {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login-json", response_model=Token)
async def login_json(user_login: UserLogin, db: Session = Depends(get_db)):
    print("🚀 [DEBUG] /login-json endpoint hit")
    print(f"📦 Login attempt for username: {user_login.username}")

    user = db.query(User).filter(User.username == user_login.username).first()
    if not user or not verify_password(user_login.password, user.hashed_password):
        print("❌ Login failed: invalid credentials")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        print("❌ Login failed: inactive user")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    user.last_login = datetime.utcnow()
    db.commit()

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id), "username": user.username},
        expires_delta=access_token_expires
    )

    print(f"✅ Login successful, token generated for {user.username}")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    print("🚀 [DEBUG] /me endpoint hit")
    print(f"📦 Current user: {current_user.username}")
    return current_user


@router.post("/logout")
async def logout():
    print("🚀 [DEBUG] /logout endpoint hit")
    return {"message": "Successfully logged out"}
