from sqlalchemy import create_engine, Column, String, Boolean, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, Column, String, Boolean, Integer, DateTime
from sqlalchemy.sql import func
from sqlalchemy import Column, Integer, String, DateTime

# This creates your local database file
SQLALCHEMY_DATABASE_URL = "sqlite:///./contractors.db"

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# In database.py
class UserTable(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    email = Column(String, unique=True)
    dept = Column(String)
    role = Column(String)
    location = Column(String, nullable=True)     # Ensure this exists
    manager_name = Column(String, nullable=True) # Ensure this exists
    created_at = Column(DateTime)
    contract_end = Column(DateTime, nullable=True)


# Create the table
Base.metadata.create_all(bind=engine)




