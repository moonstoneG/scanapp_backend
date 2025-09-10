from ast import List
from pydantic import BaseModel
from typing import Optional

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
    items: List[DocItem]
    
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

class UserOut(BaseModel):
    id: int
    username: str
    is_admin: bool = False
    class Config:
        from_attributes = True  # Pydantic v2