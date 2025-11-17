from pydantic import BaseModel
from typing import List, Optional

# ------- 单位 -------
class UnitOut(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True  # Pydantic v2

class UnitBase(BaseModel):
    name: str

class UnitCreate(UnitBase):
    pass


    id: int
    sku: str
    name: str
    qty: float
    price: float
    unit: str

    class Config:
        from_attributes = True


class ScanItemOut(BaseModel):
    """
    清单里的商品条目
    """
    id: int
    sku: str
    name: str
    qty: float
    price: float
    unit: str

    class Config:
        from_attributes = True


# 前端创建清单时使用
class ListCreate(BaseModel):
    title: str


# 向清单添加商品
class AddItem(BaseModel):
    sku: str
    qty: float


# 修改清单条目（数量）
class UpdateItem(BaseModel):
    qty: float


class CollabItem(BaseModel):
    sku: Optional[str] = None
    name: str
    unit: Optional[str] = None
    price: float = 0.0
    qty: float = 0.0

class CollabList(BaseModel):
    id: str
    name: str  # 如果你现在前端是 title，就改成 title
    items: List[CollabItem]
    
class ScanListOut(BaseModel):
    """
    一个完整的清单（包含所有条目）
    """
    id: str
    title: str
    created_by: Optional[str] = None
    items: List[ScanItemOut] = []

    class Config:
        from_attributes = True

class DocItem(BaseModel):
    sku: str
    name: str
    manufacturer: Optional[str] = None
    unit: Optional[str] = None
    price: Optional[float] = 0
    qty: Optional[int] = 1

class DocPayload(BaseModel):
    bureau: str
    suspect: str
    behavior: str
    items: list[DocItem]
    
# ------- 商品 -------
class ProductBase(BaseModel):
    sku: Optional[str] = None  
    name: str
    manufacturer: Optional[str] = None
    price: Optional[float] = 0
    unit: Optional[str] = None
   
    
class ProductCreate(ProductBase):
    pass

class ProductOut(ProductBase):
    id: int
    class Config:
        from_attributes = True

# ------- 用户 -------
class UserBase(BaseModel):
    username: str
    is_admin: bool = False

class UserCreate(UserBase):
    password: str
    full_name: Optional[str] = None
    department: Optional[str] = None
# ------- 用户 -------
class UserOut(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    department: Optional[str] = None
    is_admin: bool = False

    class Config:
        orm_mode = True  # Pydantic v1