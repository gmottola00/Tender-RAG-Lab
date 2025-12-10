from fastapi import FastAPI
from api.services.ingestion import ingestion
from configs.config import settings
from fastapi.middleware.cors import CORSMiddleware

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
