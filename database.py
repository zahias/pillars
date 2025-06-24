from sqlalchemy import (
    create_engine, Column, Integer, String, ForeignKey
)
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

# --- DB setup ---
engine = create_engine("sqlite:///data.db", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

# --- Models ---
class Program(Base):
    __tablename__ = "programs"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    activities = relationship("Activity", back_populates="program")

class Pillar(Base):
    __tablename__ = "pillars"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String, nullable=True)
    indicators = relationship("Indicator", back_populates="pillar")

class Indicator(Base):
    __tablename__ = "indicators"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    pillar_id = Column(Integer, ForeignKey("pillars.id"), nullable=False)
    goal_per_year = Column(Integer, nullable=False)
    statuses = Column(String, nullable=False)  # comma-separated list
    pillar = relationship("Pillar", back_populates="indicators")
    activities = relationship("Activity", back_populates="indicator")

class Activity(Base):
    __tablename__ = "activities"
    id = Column(Integer, primary_key=True)
    year = Column(Integer, nullable=False)
    quarter = Column(String, nullable=False)
    program_id = Column(Integer, ForeignKey("programs.id"), nullable=False)
    indicator_id = Column(Integer, ForeignKey("indicators.id"), nullable=False)
    status = Column(String, nullable=False)
    type = Column(String, nullable=False)
    participation = Column(String, nullable=False)
    format = Column(String, nullable=False)
    title = Column(String, nullable=False)

    program = relationship("Program", back_populates="activities")
    indicator = relationship("Indicator", back_populates="activities")

def init_db():
    Base.metadata.create_all(bind=engine)
