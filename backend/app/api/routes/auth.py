from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_db
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse, UserCreate, UserRead, UserUpdate

router = APIRouter(prefix="/auth", tags=["auth"])


def build_token_response(user: User) -> TokenResponse:
    return TokenResponse(
        access_token=create_access_token(str(user.id)),
        user=user,
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)) -> TokenResponse:
    email = payload.email.strip().lower()
    if not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="请输入手机号或邮箱")
    username = (payload.username or email.split("@", 1)[0]).strip()
    existing_user = db.scalar(select(User).where(User.email == email))

    if existing_user:
        if existing_user.password_hash:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="邮箱已注册")

        existing_user.username = username
        existing_user.password_hash = get_password_hash(payload.password)
        db.add(existing_user)
        db.commit()
        db.refresh(existing_user)
        return build_token_response(existing_user)

    user = User(email=email, username=username, password_hash=get_password_hash(payload.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return build_token_response(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    email = payload.email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))

    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号或密码错误")

    return build_token_response(user)


@router.get("/me", response_model=UserRead)
def read_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user


@router.put("/me", response_model=UserRead)
def update_me(
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> User:
    if payload.username is not None:
        current_user.username = payload.username.strip()
    if payload.default_salary_income is not None:
        current_user.default_salary_income = payload.default_salary_income
    if "opening_balance_date" in payload.model_fields_set:
        current_user.opening_balance_date = payload.opening_balance_date
    if "opening_balance_amount" in payload.model_fields_set:
        next_opening_balance = payload.opening_balance_amount or 0
        if current_user.opening_balance_amount != next_opening_balance:
            current_user.opening_balance_reset_at = datetime.now()
        current_user.opening_balance_amount = next_opening_balance
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Response:
    db.delete(current_user)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
