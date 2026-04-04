import os
import uuid
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_URL = os.getenv("DATABASE_URL", "sqlite:///./facefind.db")
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True)
    role = Column(String, default="user") # 'admin' or 'user'

class Photo(Base):
    __tablename__ = "photos"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    image_path = Column(String, nullable=False)
    scene_label = Column(Text, nullable=True)
    face_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class Embedding(Base):
    __tablename__ = "embeddings"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    photo_id = Column(String, ForeignKey("photos.id"))
    embedding_vector = Column(Text) # Stored as comma-separated string or JSON

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
