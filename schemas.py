from pydantic import BaseModel
from typing import List, Optional

# ======================
# ------- 单位 -------
# ======================

class UnitOut(BaseModel):
    id: int
    name: str
    class Config:
        from_attributes = True  # Pydantic v2


class UnitBase(BaseModel):
    name: str


class UnitCreate(UnitBase):
    pass


# ================================
# ------- 清单商品条目（数据库）-------
# ================================

class ScanItemOut(BaseModel):
    id: int
    sku: str
    name: str
    qty: float
    price: float
    unit: str

    class Config:
        from_attributes = True


# ======================
# ------- 创建清单 -------
# ======================

class ListCreate(BaseModel):
    name: str        # ← 统一为 name（原来 title 全部改掉）


# 清单添加商品
class AddItem(BaseModel):
    sku: str
    qty: float


# 修改商品数量
class UpdateItem(BaseModel):
    qty: float


# ===================================
# ------- 协作模式（前端 / 后端）-------
# ===================================

class CollabItem(BaseModel):
    sku: Optional[str] = None
    name: str
    unit: Optional[str] = None
    price: float = 0.0
    qty: float = 0.0


class CollabList(BaseModel):
    id: str
    name: str      # ← 与前端保持一致
    items: List[CollabItem]


# =======================================
# ------- 清单返回给前端（完整） -------
# =======================================

class ScanListOut(BaseModel):
    id: str
    name: str              # ← 统一为 name，不再用 title
    created_by: Optional[str] = None
    items: List[ScanItemOut] = []

    class Config:
        from_attributes = True


# ======================
# ------- 文书 -------
# ======================

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


# ======================
# ------- 商品 -------
# ======================

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


# ======================
# ------- 用户 -------
# ======================

class UserBase(BaseModel):
    username: str
    is_admin: bool = False


class UserCreate(UserBase):
    password: str
    full_name: Optional[str] = None
    department: Optional[str] = None


class UserOut(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    department: Optional[str] = None
    is_admin: bool = False

    class Config:
        from_attributes = True   # Pydantic v2