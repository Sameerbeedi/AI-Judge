"""
PostgreSQL Database Configuration
Handles case data, documents, and user information
"""
from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database URL from environment or default to SQLite for local dev
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./ai_judge.db")

# Create engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class Case(Base):
    __tablename__ = "cases"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(255), unique=True, index=True, nullable=False)
    status = Column(String(50), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    documents = relationship("Document", back_populates="case")
    arguments = relationship("Argument", back_populates="case")
    verdict = relationship("Verdict", back_populates="case", uselist=False)
    follow_ups = relationship("FollowUp", back_populates="case")


class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(255), ForeignKey("cases.case_id"), nullable=False)
    side = Column(String(1), nullable=False)  # 'A' or 'B'
    filename = Column(String(255))
    file_path = Column(Text)
    extracted_text = Column(Text)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    case = relationship("Case", back_populates="documents")


class Argument(Base):
    __tablename__ = "arguments"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(255), ForeignKey("cases.case_id"), nullable=False)
    side = Column(String(1), nullable=False)  # 'A' or 'B'
    argument_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    case = relationship("Case", back_populates="arguments")


class Verdict(Base):
    __tablename__ = "verdicts"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(255), ForeignKey("cases.case_id"), unique=True, nullable=False)
    verdict_text = Column(Text, nullable=False)
    reasoning = Column(Text)
    decided_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    case = relationship("Case", back_populates="verdict")


class FollowUp(Base):
    __tablename__ = "follow_ups"
    
    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(String(255), ForeignKey("cases.case_id"), nullable=False)
    side = Column(String(1), nullable=False)  # 'A' or 'B'
    argument_text = Column(Text, nullable=False)
    response_text = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship
    case = relationship("Case", back_populates="follow_ups")


# Create tables
def init_db():
    Base.metadata.create_all(bind=engine)


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
