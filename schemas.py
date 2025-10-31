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