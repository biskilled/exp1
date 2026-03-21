"""
Auth router — register, login, me.

POST /auth/register  {"email": ..., "password": ...}  → {token, user}
POST /auth/login     {"email": ..., "password": ...}  → {token, user}
GET  /auth/me        Bearer <token>                    → user dict
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, field_validator

from core.auth import create_access_token, get_current_user
from models import user as user_store

router = APIRouter()


class RegisterRequest(BaseModel):
    email: str
    password: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class LoginRequest(BaseModel):
    email: str
    password: str


def _token_response(user: dict) -> dict:
    token = create_access_token(user["id"], user["email"])
    return {"token": token, "user": user}


@router.post("/register", status_code=201)
async def register(req: RegisterRequest):
    try:
        user = user_store.create_user(req.email, req.password)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    return _token_response(user)


@router.post("/login")
async def login(req: LoginRequest):
    user = user_store.authenticate(req.email, req.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    return _token_response(user)


@router.get("/me")
async def me(current_user: dict = Depends(get_current_user)):
    # dev_mode returns synthetic admin dict directly
    if current_user.get("id") == "dev-admin":
        return current_user
    # Normal mode: JWT has {sub, email, exp}; look up full user for role/balance
    user_id = current_user.get("sub")
    if user_id:
        full = user_store.find_by_id(user_id)
        if full:
            return full
    return current_user
