# users.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
from database import get_db
from auth import get_current_user, get_password_hash  # 假设已有
import models

router = APIRouter(tags=["用户管理"])

class UserCreate(BaseModel):
    username: str
    password: str
    is_admin: bool = False
    full_name: Optional[str] = None
    department: Optional[str] = None
class UserOut(BaseModel):
    id: int
    username: str
    is_admin: bool = False
    full_name: Optional[str] = None
    department: Optional[str] = None

    class Config:
        orm_mode = True


@router.get("/", response_model=List[UserOut])
def list_users(db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="非管理员无权查看")
    return db.query(models.User).all()


@router.post("/", response_model=UserOut)
def create_user(user: UserCreate, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="非管理员无权添加")

    if db.query(models.User).filter(models.User.username == user.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")

    u = models.User(
     username=user.username,
     password_hash=get_password_hash(user.password),
     is_admin=user.is_admin,
     full_name=user.full_name,      # 新增
     department=user.department     # 新增
)
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


@router.delete("/{uid}")
def delete_user(uid: int, db: Session = Depends(get_db), current_user=Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="非管理员无权删除")
    u = db.query(models.User).filter(models.User.id == uid).first()
    if not u:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(u)
    db.commit()
    return {"ok": True}