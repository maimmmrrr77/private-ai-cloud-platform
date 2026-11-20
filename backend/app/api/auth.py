from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.models.database import get_db, User
from app.core.security import (
    verify_password, get_password_hash, create_access_token,
    get_current_user, require_admin
)

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & Users (RBAC)"])

class UserCreate(BaseModel):
    username: str
    full_name: str
    password: str
    role: str = "user"  # "admin" hoặc "user"

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

@router.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Sai tên đăng nhập hoặc mật khẩu")
    
    access_token = create_access_token(data={"sub": user.username, "role": user.role})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {"username": user.username, "full_name": user.full_name, "role": user.role}
    }

@router.get("/me")
def get_my_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "full_name": current_user.full_name,
        "role": current_user.role
    }

@router.post("/change-password")
def change_password(
    req: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if not verify_password(req.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Mật khẩu cũ không chính xác")
    
    current_user.hashed_password = get_password_hash(req.new_password)
    db.commit()
    return {"success": True, "message": "Đổi mật khẩu thành công!"}

# --- CÁC API QUẢN TRỊ USER (CHỈ ADMIN MỚI ĐƯỢC GỌI) ---
@router.post("/users", dependencies=[Depends(require_admin)])
def create_new_user(user_in: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")
    
    new_user = User(
        username=user_in.username,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        role=user_in.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return {"message": "Tạo người dùng thành công", "username": new_user.username, "role": new_user.role}

@router.get("/users", dependencies=[Depends(require_admin)])
def list_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()
    return [{"id": u.id, "username": u.username, "full_name": u.full_name, "role": u.role} for u in users]