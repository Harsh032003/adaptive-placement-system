from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..auth import ADMIN_SIGNUP_CODE, create_access_token, get_current_user, hash_password, verify_password
from ..db import get_db
from ..models import User
from ..schemas import SignupRequest, LoginRequest

router = APIRouter()


@router.post("/signup")
def signup(payload: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == payload.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    is_admin = False
    if payload.admin_code and ADMIN_SIGNUP_CODE and payload.admin_code == ADMIN_SIGNUP_CODE:
        is_admin = True
    if not ADMIN_SIGNUP_CODE:
        admin_count = db.query(User).filter(User.is_admin.is_(True)).count()
        if admin_count == 0:
            is_admin = True

    user = User(
        username=payload.username,
        password_hash=hash_password(payload.password),
        is_admin=is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    token = create_access_token({"user_id": user.id, "username": user.username, "is_admin": user.is_admin})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "username": user.username, "is_admin": user.is_admin},
    }


@router.post("/login")
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == payload.username).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({"user_id": user.id, "username": user.username, "is_admin": user.is_admin})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {"id": user.id, "username": user.username, "is_admin": user.is_admin},
    }


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": user.id, "username": user.username, "is_admin": user.is_admin}
