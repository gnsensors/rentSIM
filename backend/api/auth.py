from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

import auth as auth_utils
from database import get_db
from models import User
from schemas import Token, UserCreate, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


def get_current_user(authorization: str = "", db: Session = Depends(get_db)) -> User:
    raise HTTPException(status_code=401, detail="Not authenticated")


def _require_user(token: str, db: Session) -> User:
    user_id = auth_utils.decode_token(token, expected_type="access")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def current_user_dep(authorization: str = "", db: Session = Depends(get_db)) -> User:
    """Dependency — extracts Bearer token from Authorization header."""
    from fastapi import Header
    raise HTTPException(status_code=401, detail="Use get_current_user dependency properly")


# ── Proper dependency using Header ────────────────────────────────────────────

from fastapi import Header


def get_current_user_from_header(
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
) -> User:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    token = authorization.removeprefix("Bearer ")
    return _require_user(token, db)


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(body: UserCreate, response: Response, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(email=body.email, password_hash=auth_utils.hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return _issue_tokens(user, response)


@router.post("/login", response_model=Token)
def login(body: UserCreate, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not auth_utils.verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return _issue_tokens(user, response)


@router.post("/refresh", response_model=Token)
def refresh(response: Response, refresh_token: str = Cookie(default=None), db: Session = Depends(get_db)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="No refresh token")
    user_id = auth_utils.decode_token(refresh_token, expected_type="refresh")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return _issue_tokens(user, response)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("refresh_token")
    return {"detail": "Logged out"}


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user_from_header)):
    return user


# ── Helper ────────────────────────────────────────────────────────────────────

def _issue_tokens(user: User, response: Response) -> dict:
    access  = auth_utils.create_access_token(user.id)
    refresh = auth_utils.create_refresh_token(user.id)
    response.set_cookie(
        key="refresh_token",
        value=refresh,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 30,
    )
    return {"access_token": access, "token_type": "bearer", "user": user}
