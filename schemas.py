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