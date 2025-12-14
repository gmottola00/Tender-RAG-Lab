from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from configs.config import settings
from src.api.routers.ingestion import ingestion
from src.api.routers.tenders import router as tenders_router
from src.api.routers.lots import router as lots_router
from src.api.routers.documents import router as documents_router
from src.api.routers.ui import router as ui_router
from src.api.routers.milvus_route import router as milvus_router

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION)

# metti qui gli origin del tuo frontend web
ALLOWED_ORIGINS = [
    "http://0.0.0.0:8080",         
    "http://192.168.1.23:8080",    
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,           # tienilo True se usi cookie/sessione, ok anche con Bearer
    allow_methods=["*"],
    allow_headers=["*"],              # oppure ["Authorization", "Content-Type"]
)

app.include_router(
    ingestion, 
    prefix="/api/ingestion", 
    tags=["Pools"]
)
app.include_router(tenders_router, prefix="/api")
app.include_router(lots_router, prefix="/api")
app.include_router(documents_router, prefix="/api")
app.include_router(milvus_router, prefix="/api")
app.include_router(ui_router, prefix="")

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/static/milvus", StaticFiles(directory="static/milvus"), name="static-milvus")
