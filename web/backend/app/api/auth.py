from fastapi import APIRouter, Depends, HTTPException, status, Response, Request # pyre-ignore[21]
from sqlalchemy.orm import Session # pyre-ignore[21]
from fastapi.security import OAuth2PasswordRequestForm # pyre-ignore[21]
from app.core import security # pyre-ignore[21]
from app.core.database import get_db # pyre-ignore[21]
from app.models import User # pyre-ignore[21]
from pydantic import BaseModel, EmailStr # pyre-ignore[21]

router = APIRouter()

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str = ""

class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str

@router.post("/signup", response_model=UserResponse)
def signup(user_in: UserCreate, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_in.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_user = User(
        email=user_in.email,
        hashed_password=security.get_password_hash(user_in.password),
        full_name=user_in.full_name
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login")
def login(response: Response, form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = security.create_access_token(data={"sub": str(user.id)})
    
    # Store in HttpOnly cookie for premium security
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        samesite="lax",
        secure=False # Set to True in production with HTTPS
    )
    return {"status": "success"}

@router.post("/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"status": "success"}

@router.get("/me", response_model=UserResponse)
def get_me(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token or not token.startswith("Bearer "):
         raise HTTPException(status_code=401, detail="Not authenticated")
    
    try:
        token = token[7:]
        payload = security.jwt.decode(token, security.SECRET_KEY, algorithms=[security.ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except Exception:
        raise HTTPException(status_code=410, detail="Token expired or invalid")

    user = db.query(User).filter(User.id == int(user_id)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
