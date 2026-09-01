from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from rag.database import engine, Base
from rag.core.config import settings

from rag.api.endpoints import router as chat_router
from rag.api.onedrive_routes import router as onedrive_router
from rag.qdrant.collection_service import create_collection

# Create database tables
Base.metadata.create_all(bind=engine)

# Create Qdrant collection if it doesn't exist
create_collection()

app = FastAPI(title=settings.PROJECT_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router, prefix="/api")
app.include_router(onedrive_router, prefix="/api/onedrive")

from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

app.mount("/static", StaticFiles(directory="temporary_frontend"), name="static")

@app.get("/")
def read_root():
    return FileResponse("temporary_frontend/index.html")
