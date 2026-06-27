from typing import Optional
from pydantic import BaseModel


class CustomerBase(BaseModel):
    name: str
    email: str
    phone_number: str
    product_id: Optional[int] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    product_id: Optional[int] = None


class CustomerResponse(CustomerBase):
    id: int

    class Config:
        from_attributes = True
