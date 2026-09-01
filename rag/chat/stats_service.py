from typing import Dict, Any, List
from sqlalchemy.orm import Session
from rag.scope.models import Client, Team, Benefit, Process, Document
from rag.scope.schemas import ScopeSession


def get_client_stats(db: Session, session: ScopeSession = None) -> Dict[str, Any]:
    result = {"clients": []}

    clients = db.query(Client).filter(Client.active == True).all()
    for client in clients:
        teams = db.query(Team).filter(Team.client_id == client.client_id).all()
        client_total = 0
        processes = []

        for team in teams:
            benefits = db.query(Benefit).filter(Benefit.team_id == team.team_id).all()
            for benefit in benefits:
                procs = db.query(Process).filter(Process.benefit_id == benefit.benefit_id).all()
                for proc in procs:
                    count = db.query(Document).filter(
                        Document.process_id == proc.process_id,
                        Document.active == True
                    ).count()
                    client_total += count
                    processes.append({
                        "process_name": proc.process_name,
                        "file_count": count
                    })

        result["clients"].append({
            "client_name": client.client_name,
            "file_count": client_total,
            "processes": processes
        })

    if session and session.client_id:
        result["current_client"] = None
        for c in result["clients"]:
            c_obj = db.query(Client).filter(Client.client_id == session.client_id).first()
            if c_obj and c["client_name"] == c_obj.client_name:
                c["is_current"] = True
                result["current_client"] = c

    return result


def format_stats_text(stats: Dict[str, Any]) -> str:
    lines = []
    total_all = 0

    for client in stats["clients"]:
        total_all += client["file_count"]
        lines.append(f"{client['client_name']}: {client['file_count']} file(s)")
        for proc in client["processes"]:
            if proc["file_count"] > 0:
                lines.append(f"  - {proc['process_name']}: {proc['file_count']} file(s)")

    header = f"Knowledge Base Stats\nTotal files indexed: {total_all}\n\n"
    return header + "\n".join(lines)


def lookup_file_count_for_client(db: Session, client_name: str) -> Dict[str, Any]:
    client = db.query(Client).filter(Client.client_name.ilike(f"%{client_name}%")).first()
    if not client:
        return {"found": False, "message": f"No client named '{client_name}' found in the knowledge base."}

    teams = db.query(Team).filter(Team.client_id == client.client_id).all()
    process_breakdown = []
    total = 0

    for team in teams:
        benefits = db.query(Benefit).filter(Benefit.team_id == team.team_id).all()
        for benefit in benefits:
            procs = db.query(Process).filter(Process.benefit_id == benefit.benefit_id).all()
            for proc in procs:
                count = db.query(Document).filter(
                    Document.process_id == proc.process_id,
                    Document.active == True
                ).count()
                total += count
                process_breakdown.append({"process": proc.process_name, "count": count})

    return {
        "found": True,
        "client_name": client.client_name,
        "file_count": total,
        "processes": process_breakdown
    }


COUNT_QUERY_PATTERNS = [
    "how many source",
    "how many files",
    "how many documents",
    "how many doc",
    "number of source file",
    "number of files",
    "number of document",
]
