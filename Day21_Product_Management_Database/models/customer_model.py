from sqlalchemy import Column, Integer, String, ForeignKey
from db.database import Base

class Customer(Base):
    __tablename__ = 'customers'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    phone_number = Column(String(20), unique=True, nullable=False)
    product_id = Column(Integer, ForeignKey("products.id"))
    
