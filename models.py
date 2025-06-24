from sqlalchemy import (Column, Integer, String, Date, JSON, create_engine)
from sqlalchemy.orm import relationship, declarative_base, sessionmaker

Base = declarative_base()

class Program(Base):
    __tablename__ = 'programs'
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)

class Pillar(Base):
    __tablename__ = 'pillars'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    indicators = relationship('Indicator', back_populates='pillar')

class Indicator(Base):
    __tablename__ = 'indicators'
    id = Column(Integer, primary_key=True)
    pillar_id = Column(Integer, nullable=False)
    name = Column(String, nullable=False)
    goal_per_year = Column(Integer, nullable=False)
    allowed_statuses = Column(JSON, nullable=False)
    pillar = relationship('Pillar', back_populates='indicators')

class Activity(Base):
    __tablename__ = 'activities'
    id = Column(Integer, primary_key=True)
    program_code = Column(String, nullable=False)
    pillar_name = Column(String, nullable=False)
    indicator_name = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    year = Column(Integer, nullable=False)
    quarter = Column(String, nullable=False)
    status = Column(String, nullable=False)
    trigger = Column(String)
    organization = Column(String)
    contact_person = Column(String)
    contact_info = Column(String)
    outcome = Column(String)
    comments = Column(String)

# Engine & Session
engine = create_engine('sqlite:///database.db', echo=False)
SessionLocal = sessionmaker(bind=engine)

# Create tables
Base.metadata.create_all(engine)
