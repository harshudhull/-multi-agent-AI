from sqlalchemy import create_engine, Column, String, Text, TIMESTAMP, Integer
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.sql import func
from typing import Dict, Any, List, Optional
import json

# ✅ Replace these with your actual MySQL credentials
DATABASE_URL = "mysql+pymysql://root:1234@localhost:3306/intake_system"

# Set up SQLAlchemy
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

# === Table Models ===

class ExtractedData(Base):
    __tablename__ = "extracted_data"

    id = Column(String(255), primary_key=True)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    classification = Column(String(255))
    extracted_data = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())


class Memory(Base):
    __tablename__ = "memory"

    id = Column(String(255), primary_key=True)
    data = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())


class UserProfile(Base):
    __tablename__ = "user_profiles"

    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    role = Column(String(50), default="user")
    created_at = Column(TIMESTAMP, server_default=func.now())

# === Initialize DB ===

def init_db():
    Base.metadata.create_all(bind=engine)

# === Save Data ===

def save_extracted_data(data_id: str, original_filename: str, file_type: str, 
                        extracted_data: Dict[str, Any], classification: Optional[str] = None) -> bool:
    session = SessionLocal()
    try:
        item = ExtractedData(
            id=data_id,
            original_filename=original_filename,
            file_type=file_type,
            classification=classification,
            extracted_data=json.dumps(extracted_data)
        )
        session.merge(item)
        session.commit()
        return True
    except Exception as e:
        print(f"Error saving extracted data: {e}")
        session.rollback()
        return False
    finally:
        session.close()

# === Get History ===

def get_history() -> List[Dict[str, Any]]:
    session = SessionLocal()
    try:
        results = session.query(ExtractedData).order_by(ExtractedData.created_at.desc()).limit(50).all()
        return [
            {
                "id": r.id,
                "filename": r.original_filename,
                "file_type": r.file_type,
                "classification": r.classification,
                "created_at": r.created_at.isoformat()
            }
            for r in results
        ]
    except Exception as e:
        print(f"Error getting history: {e}")
        return []
    finally:
        session.close()

# === Get Specific Data ===

def get_extracted_data(data_id: str) -> Optional[Dict[str, Any]]:
    session = SessionLocal()
    try:
        result = session.query(ExtractedData).filter(ExtractedData.id == data_id).first()
        if result:
            return json.loads(result.extracted_data)
        return None
    except Exception as e:
        print(f"Error getting extracted data: {e}")
        return None
    finally:
        session.close()
