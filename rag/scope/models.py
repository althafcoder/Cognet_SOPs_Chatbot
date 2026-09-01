from sqlalchemy import Boolean, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from rag.database import Base

class Client(Base):
    __tablename__ = "clients"

    client_id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, index=True, default=1)
    client_name = Column(String, unique=True, index=True)
    source_path = Column(String)
    active = Column(Boolean, default=True)

    teams = relationship("Team", back_populates="client")

class Team(Base):
    __tablename__ = "teams"

    team_id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.client_id"))
    team_name = Column(String, index=True)
    active = Column(Boolean, default=True)

    client = relationship("Client", back_populates="teams")
    benefits = relationship("Benefit", back_populates="team")

class Benefit(Base):
    __tablename__ = "benefits"

    benefit_id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.team_id"))
    benefit_name = Column(String, index=True)
    active = Column(Boolean, default=True)

    team = relationship("Team", back_populates="benefits")
    processes = relationship("Process", back_populates="benefit")

class Process(Base):
    __tablename__ = "processes"

    process_id = Column(Integer, primary_key=True, index=True)
    benefit_id = Column(Integer, ForeignKey("benefits.benefit_id"))
    process_name = Column(String, index=True)
    active = Column(Boolean, default=True)

    benefit = relationship("Benefit", back_populates="processes")

class Document(Base):
    __tablename__ = "documents"

    document_id = Column(String, primary_key=True, index=True) # E.g., DOC-123
    process_id = Column(Integer, ForeignKey("processes.process_id"), nullable=True)
    file_name = Column(String)
    source_path = Column(String)
    file_hash = Column(String)
    index_status = Column(String, default="PENDING")
    modified_at = Column(DateTime, default=datetime.utcnow)
    active = Column(Boolean, default=True)
