from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text # pyre-ignore[21]
from sqlalchemy.orm import relationship # pyre-ignore[21]
from sqlalchemy.sql import func # pyre-ignore[21]
from app.core.database import Base # pyre-ignore[21]

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    books = relationship("Book", back_populates="owner")
    api_keys = relationship("ApiKey", back_populates="owner")

class ApiKey(Base):
    __tablename__ = "api_keys"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    service = Column(String, nullable=False)  # 'hf', 'openrouter', 'grok'
    encrypted_key = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    owner = relationship("User", back_populates="api_keys")

class Book(Base):
    __tablename__ = "books"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    genre = Column(String)
    status = Column(String, default="pending")  # pending, generating, completed, failed
    progress = Column(Integer, default=0)
    word_count = Column(Integer, default=0)
    docx_path = Column(String)
    cover_path = Column(String)
    marketing_kit_path = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    owner = relationship("User", back_populates="books")
