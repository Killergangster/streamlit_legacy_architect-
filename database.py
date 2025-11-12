
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from sqlalchemy.exc import IntegrityError

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(150), unique=True, nullable=False)
    name = Column(String(250))
    email = Column(String(250))
    hashed_password = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    memories = relationship("Memory", back_populates="user", cascade="all, delete-orphan")
    assets = relationship("Asset", back_populates="user", cascade="all, delete-orphan")

class Memory(Base):
    __tablename__ = "memories"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="memories")

class Asset(Base):
    __tablename__ = "assets"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    filename = Column(String(500))
    filepath = Column(String(1000))
    description = Column(Text)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="assets")

def _get_engine(db_path):
    db_full = f"sqlite:///{db_path}"
    return create_engine(db_full, connect_args={"check_same_thread": False})

def init_db(db_path="data.db"):
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    engine = _get_engine(db_path)
    Base.metadata.create_all(engine)

def _get_session(db_path):
    engine = _get_engine(db_path)
    Session = sessionmaker(bind=engine)
    return Session()

# CRUD helpers
def create_user(db_path, username, name="", email="", hashed_password=None):
    session = _get_session(db_path)
    user = User(username=username, name=name, email=email, hashed_password=hashed_password)
    session.add(user)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        raise
    finally:
        session.close()
    return user

def get_user_by_username(db_path, username):
    session = _get_session(db_path)
    user = session.query(User).filter(User.username == username).first()
    session.close()
    return user

def add_memory(db_path, username, content):
    session = _get_session(db_path)
    user = session.query(User).filter(User.username == username).first()
    if not user:
        session.close()
        raise ValueError("User not found")
    memory = Memory(user_id=user.id, content=content)
    session.add(memory)
    session.commit()
    session.close()
    return memory

def get_memories(db_path, username, limit=100):
    session = _get_session(db_path)
    user = session.query(User).filter(User.username == username).first()
    if not user:
        session.close()
        return []
    memories = session.query(Memory).filter(Memory.user_id == user.id).order_by(Memory.created_at.desc()).limit(limit).all()
    session.close()
    return memories

def add_asset(db_path, username, filename, filepath, description=""):
    session = _get_session(db_path)
    user = session.query(User).filter(User.username == username).first()
    if not user:
        session.close()
        raise ValueError("User not found")
    asset = Asset(user_id=user.id, filename=filename, filepath=filepath, description=description)
    session.add(asset)
    session.commit()
    session.close()
    return asset

def get_assets(db_path, username, limit=100):
    session = _get_session(db_path)
    user = session.query(User).filter(User.username == username).first()
    if not user:
        session.close()
        return []
    assets = session.query(Asset).filter(Asset.user_id == user.id).order_by(Asset.uploaded_at.desc()).limit(limit).all()
    session.close()
    return assets
