from typing import List
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, BigInteger, Double, Text, and_, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from constants import (
    DB_USER,
    DB_PASSWORD,
    DB_HOST,
    DB_PORT,
    DB_NAME
)

# Database connection configuration

engine = create_engine(
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}")

SessionLocal = sessionmaker(
    autocommit=False, autoflush=True, bind=engine, expire_on_commit=False)

# Define the declarative Base class
Base = declarative_base()

class Data(Base):
    __tablename__ = "data"
    id = Column(BigInteger, primary_key=True)
    name = Column(String(255), nullable=False)
    created_time = Column(DateTime, nullable=False)
    collected = Column(Boolean, nullable=False)
    upload_type = Column(String(255), nullable=False)
    species = Column(String(255), nullable=True)
    created_from = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    state = Column(String(30), nullable=False)
    error_message = Column(Text, nullable=True)
    buried = Column(Boolean, nullable=False)
    summary = Column(Text, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "createdTime": self.created_time.timestamp() * 1000,
            "collected": self.collected,
            "uploadType": self.upload_type,
            "species": self.species,
            "createdFrom": self.created_from,
            "description": self.description,
            "state": self.state,
            "errorMessage": self.error_message,
            "buried": self.buried,
            "summary": self.summary
        }

def update_data(data_id, attrs):
    with SessionLocal() as session:
        session.query(Data).filter(Data.id == data_id).update(attrs)
        session.commit()


def find_data_by_id(data_id) -> Data:
    with SessionLocal() as session:
        return session.query(Data).filter(Data.id == data_id).first()

def find_data_by_created_from_and_state(created_from, state) -> List[Data]:
    with SessionLocal() as session:
        return session.query(Data).filter(and_(Data.created_from == created_from, Data.state == state)).all()

def find_datas_by_id_list(data_id_list) -> List[Data]:
    with SessionLocal() as session:
        return session.query(Data).filter(Data.id.in_(data_id_list)).all()
