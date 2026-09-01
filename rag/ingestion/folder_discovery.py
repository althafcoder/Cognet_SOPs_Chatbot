import os
from sqlalchemy.orm import Session
from rag.scope.models import Client, Team, Benefit, Process

def register_hierarchy(db: Session, relative_path: str):
    # relative_path might be "SOPs/Deutz/BPO/file.docx" or similar
    parts = relative_path.strip("/").split("/")
    
    # Remove SOPs if it is the first part
    if parts and parts[0].lower() == "sops":
        parts = parts[1:]
        
    if len(parts) >= 1:
        client_name = parts[0]
        client = db.query(Client).filter(Client.client_name == client_name).first()
        if not client:
            client = Client(client_name=client_name, source_path=parts[0])
            db.add(client)
            db.commit()
            db.refresh(client)
            
        # Create a default Team for the Client since the new hierarchy skips it
        team_name = "Default Team"
        team = db.query(Team).filter(Team.team_name == team_name, Team.client_id == client.client_id).first()
        if not team:
            team = Team(team_name=team_name, client_id=client.client_id)
            db.add(team)
            db.commit()
            db.refresh(team)
            
        # Create a default Benefit for the Team
        benefit_name = "Default Benefit"
        benefit = db.query(Benefit).filter(Benefit.benefit_name == benefit_name, Benefit.team_id == team.team_id).first()
        if not benefit:
            benefit = Benefit(benefit_name=benefit_name, team_id=team.team_id)
            db.add(benefit)
            db.commit()
            db.refresh(benefit)
            
        if len(parts) >= 2:
            process_name = parts[1]
            process = db.query(Process).filter(Process.process_name == process_name, Process.benefit_id == benefit.benefit_id).first()
            if not process:
                process = Process(process_name=process_name, benefit_id=benefit.benefit_id)
                db.add(process)
                db.commit()
                db.refresh(process)
                        
    return get_hierarchy_ids(db, relative_path)

def get_hierarchy_ids(db: Session, relative_path: str):
    parts = relative_path.strip("/").split("/")
    
    if parts and parts[0].lower() == "sops":
        parts = parts[1:]
        
    ids = {"client_id": None, "team_id": None, "benefit_id": None, "process_id": None}
    
    if len(parts) >= 1:
        client = db.query(Client).filter(Client.client_name == parts[0]).first()
        if client: 
            ids["client_id"] = client.client_id
            
            team = db.query(Team).filter(Team.team_name == "Default Team", Team.client_id == client.client_id).first()
            if team: 
                ids["team_id"] = team.team_id
                
                benefit = db.query(Benefit).filter(Benefit.benefit_name == "Default Benefit", Benefit.team_id == team.team_id).first()
                if benefit: 
                    ids["benefit_id"] = benefit.benefit_id
                    
                    if len(parts) >= 2:
                        process = db.query(Process).filter(Process.process_name == parts[1], Process.benefit_id == benefit.benefit_id).first()
                        if process: 
                            ids["process_id"] = process.process_id
                    
    return ids
