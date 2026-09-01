from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any
from pydantic import BaseModel
from sqlalchemy.orm import Session
from rag.database import get_db
from rag.core.config import settings
from rag.ingestion.onedrive_client import (
    get_access_token, get_user_drive, search_folder_in_drive,
    list_drive_items, download_file, get_all_files_in_folder
)
from rag.ingestion.folder_discovery import register_hierarchy
from rag.ingestion.change_detector import calculate_file_hash, is_file_already_indexed, update_file_hash
from rag.extraction.docx_extractor import extract_docx_content
from rag.extraction.pdf_extractor import extract_pdf_content
from rag.chunking.chunk_service import chunk_text
from rag.embeddings.dense_embedding import get_dense_embedding
from rag.qdrant.indexing_service import upsert_chunks, delete_chunks_by_document_id
from rag.scope.models import Document, Process, Client, Team, Benefit
import os
import uuid
import time
import gc

router = APIRouter()

class SyncClientRequest(BaseModel):
    client_name: str

# In-memory store for sync results keyed by sync_id
sync_status_store: Dict[str, Dict[str, Any]] = {}

@router.get("/clients")
def get_onedrive_clients():
    if not settings.MICROSOFT_USER_EMAIL:
        raise HTTPException(status_code=400, detail="MICROSOFT_USER_EMAIL not configured")

    try:
        access_token = get_access_token()
        drive_data = get_user_drive(access_token, settings.MICROSOFT_USER_EMAIL)
        drive_id = drive_data.get("id")

        folder = search_folder_in_drive(access_token, drive_id, "SOPs")
        if not folder:
            return {"clients": []}

        children = list_drive_items(access_token, drive_id, folder.get("id"))
        clients = [child.get("name") for child in children if child.get("folder")]
        return {"clients": clients}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def process_file(db, access_token, file_info, client_name):
    file_name = file_info.get("name")
    download_url = file_info.get("download_url")
    file_path = file_info.get("path")

    if not download_url:
        return "skipped"

    ext = os.path.splitext(file_name)[1].lower()
    if ext not in [".docx", ".pdf"]:
        return "skipped"

    temp_path = f"temp_downloads/{file_info.get('id')}_{os.getpid()}_{uuid.uuid4().hex[:8]}_{file_name}"

    try:
        download_file(access_token, download_url, temp_path)

        file_hash = calculate_file_hash(temp_path)
        source_path = f"{file_path}/{file_name}"

        if is_file_already_indexed(db, source_path, file_hash):
            return "unchanged"

        if ext == ".docx":
            pages = extract_docx_content(temp_path)
        elif ext == ".pdf":
            pages = extract_pdf_content(temp_path)
        else:
            return "skipped"

        chunks = chunk_text(pages)

        ids = register_hierarchy(db, file_path)
        process_id = ids.get("process_id")
        client_id = ids.get("client_id")
        team_id = ids.get("team_id")
        benefit_id = ids.get("benefit_id")

        if not process_id:
            return "skipped"

        client = db.query(Client).filter(Client.client_id == client_id).first()
        team = db.query(Team).filter(Team.team_id == team_id).first()
        benefit = db.query(Benefit).filter(Benefit.benefit_id == benefit_id).first()
        process = db.query(Process).filter(Process.process_id == process_id).first()

        client_name_val = client.client_name if client else ""
        team_name_val = team.team_name if team else ""
        benefit_name_val = benefit.benefit_name if benefit else ""
        process_name_val = process.process_name if process else ""

        existing_doc = db.query(Document).filter(Document.source_path == source_path).first()

        if existing_doc:
            doc_id = existing_doc.document_id
            delete_chunks_by_document_id(doc_id)
            existing_doc.file_hash = file_hash
            db.commit()
        else:
            doc_id = str(uuid.uuid4())
            db_doc = Document(
                document_id=doc_id,
                process_id=process_id,
                file_name=file_name,
                source_path=source_path,
                file_hash=file_hash,
                index_status="COMPLETED"
            )
            db.add(db_doc)
            db.commit()

        for chunk in chunks:
            chunk["document_id"] = doc_id
            chunk["document_name"] = file_name
            chunk["client_id"] = client_id
            chunk["client_name"] = client_name_val
            chunk["team_id"] = team_id
            chunk["team_name"] = team_name_val
            chunk["benefit_id"] = benefit_id
            chunk["benefit_name"] = benefit_name_val
            chunk["process_id"] = process_id
            chunk["process_name"] = process_name_val
            chunk["embedding"] = get_dense_embedding(chunk["content"])

        upsert_chunks(chunks)
        return "indexed"

    except Exception as e:
        print(f"Error processing file {file_name}: {e}")
        return "error"
    finally:
        gc.collect()
        for attempt in range(5):
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                break
            except OSError as e:
                print(f"Retry {attempt + 1} removing {temp_path}: {e}")
                time.sleep(1)
        else:
            print(f"Could not remove temp file after retries: {temp_path}")


def background_sync_client(sync_id: str, request: SyncClientRequest):
    db = next(get_db())
    stats = {"indexed": 0, "unchanged": 0, "skipped": 0, "error": 0}
    try:
        access_token = get_access_token()
        drive_data = get_user_drive(access_token, settings.MICROSOFT_USER_EMAIL)
        drive_id = drive_data.get("id")

        sops_folder = search_folder_in_drive(access_token, drive_id, "SOPs")
        if not sops_folder:
            sync_status_store[sync_id] = {"status": "error", "message": "SOPs folder not found", "stats": stats}
            return

        client_folder = None
        children = list_drive_items(access_token, drive_id, sops_folder.get("id"))
        for child in children:
            if child.get("name") == request.client_name and child.get("folder"):
                client_folder = child
                break

        if not client_folder:
            sync_status_store[sync_id] = {"status": "error", "message": f"Client folder '{request.client_name}' not found", "stats": stats}
            return

        files = get_all_files_in_folder(
            access_token, drive_id, client_folder.get("id"),
            current_path=f"SOPs/{request.client_name}"
        )

        for file_info in files:
            result = process_file(db, access_token, file_info, request.client_name)
            stats[result] = stats.get(result, 0) + 1

        sync_status_store[sync_id] = {
            "status": "completed",
            "message": "Sync completed",
            "client": request.client_name,
            "stats": stats
        }
        print(f"Sync completed for {request.client_name}: {stats}")

    except Exception as e:
        sync_status_store[sync_id] = {"status": "error", "message": str(e), "stats": stats}
        print(f"Sync failed: {e}")
    finally:
        db.close()


@router.post("/sync_client")
def sync_client_files(request: SyncClientRequest, background_tasks: BackgroundTasks):
    sync_id = str(uuid.uuid4())
    sync_status_store[sync_id] = {"status": "pending", "message": "Sync started", "client": request.client_name, "stats": {"indexed": 0, "unchanged": 0, "skipped": 0, "error": 0}}
    background_tasks.add_task(background_sync_client, sync_id, request)
    return {"status": "Sync started in background", "sync_id": sync_id, "client": request.client_name}


@router.get("/sync_status/{sync_id}")
def get_sync_status(sync_id: str):
    if sync_id not in sync_status_store:
        raise HTTPException(status_code=404, detail="Sync not found")
    return sync_status_store[sync_id]
