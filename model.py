from sqlalchemy import (
    Column, Integer, String, Float, Boolean, text, ForeignKey, DateTime, JSON, create_engine
)
from datetime import datetime
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.engine import URL

DATABASE_URL="postgresql://postgres:i0Z8jha2M0RgDDyF@db.qzleirzfkdjbvozhptxi.supabase.co:5432/postgres"

# DATABASE_URL = URL.create(
#     drivername="postgresql+psycopg2",
#     username="postgres",
#     password="i0Z8jha2M0RgDDyF",
#     host="db.qzleirzfkdjbvozhptxi.supabase.co", 
#     port=5432,
#     database="postgres"
# )
engine = create_engine(DATABASE_URL)

# Test the connection
try:
    with engine.connect() as connection:
        print("Connection successful!")
except Exception as e:
    print(f"Failed to connect: {e}")

# Base class
Base = declarative_base()

# 1. Customer Table
class Customer(Base):
    __tablename__ = 'customers'

    c_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), nullable=False)
    gstno = Column(String(15), unique=True)
    address = Column(String(255), nullable=False)
    phone_no = Column(String(15), nullable=False)
    email = Column(String(100), unique=True)

    sales = relationship("Sale", back_populates="customer")

# 2. Product Table
class Product(Base):
    __tablename__ = 'products'

    product_id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True)
    description = Column(String(255))
    category = Column(String(50))

    stock = relationship("Stock", uselist=False, back_populates="product")
    purchases = relationship("Purchase", back_populates="product")
    sales = relationship("Sale", back_populates="product")

# 3. Stock Table
class Stock(Base):
    __tablename__ = 'stocks'

    stock_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.product_id'), nullable=False)
    available_quantity = Column(Integer, nullable=False, default=0)
    cost_price = Column(Float, nullable=False)
    selling_price = Column(Float, nullable=False)
    last_updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    product = relationship("Product", back_populates="stock")

# 4. Purchase Table
class Purchase(Base):
    __tablename__ = 'purchases'

    purchase_id = Column(Integer, primary_key=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey('products.product_id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    cost_price = Column(Float, nullable=False)
    purchase_date = Column(DateTime, default=datetime.utcnow)
    serial_no = Column(JSON)
    is_paid = Column(Boolean, default=False)

    product = relationship("Product", back_populates="purchases")

# 5. Sale Table
class Sale(Base):
    __tablename__ = 'sales'

    sale_id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(Integer, ForeignKey('customers.c_id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.product_id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    selling_price = Column(Float, nullable=False)
    discount_percentage = Column(Float, default=0.0)
    total_amount = Column(Float, nullable=False)
    sale_date = Column(DateTime, default=datetime.utcnow)
    serial_numbers = Column(JSON)
    is_paid = Column(Boolean, default=False)

    customer = relationship("Customer", back_populates="sales")
    product = relationship("Product", back_populates="sales")

# Create all tables
Base.metadata.create_all(engine)