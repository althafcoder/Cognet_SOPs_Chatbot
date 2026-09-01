from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from rag.scope.models import Client, Team, Benefit, Process
from rag.scope.schemas import ScopeSession

def parse_scope_command(db: Session, session: ScopeSession, command: str) -> ScopeSession:
    cmd_parts = command.strip().split(" ", 1)
    if not cmd_parts:
        return session
        
    cmd_type = cmd_parts[0].lower()
    cmd_val = cmd_parts[1] if len(cmd_parts) > 1 else ""
    
    if cmd_type == "/clear":
        session.client_id = None
        session.team_id = None
        session.benefit_id = None
        session.process_id = None
    elif cmd_type == "/client":
        client = db.query(Client).filter(Client.client_name.ilike(f"%{cmd_val}%")).first()
        if client:
            session.client_id = client.client_id
            session.team_id = None
            session.benefit_id = None
            session.process_id = None
    elif cmd_type == "/team":
        if session.client_id:
            team = db.query(Team).filter(Team.team_name.ilike(f"%{cmd_val}%"), Team.client_id == session.client_id).first()
            if team:
                session.team_id = team.team_id
                session.benefit_id = None
                session.process_id = None
    elif cmd_type == "/benefit":
        if session.team_id:
            benefit = db.query(Benefit).filter(Benefit.benefit_name.ilike(f"%{cmd_val}%"), Benefit.team_id == session.team_id).first()
            if benefit:
                session.benefit_id = benefit.benefit_id
                session.process_id = None
    elif cmd_type == "/process":
        if session.benefit_id:
            process = db.query(Process).filter(Process.process_name.ilike(f"%{cmd_val}%"), Process.benefit_id == session.benefit_id).first()
            if process:
                session.process_id = process.process_id
                
    return session
