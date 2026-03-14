from fastapi import FastAPI, WebSocket # pyre-ignore[21]
from fastapi.middleware.cors import CORSMiddleware # pyre-ignore[21]
from fastapi.staticfiles import StaticFiles # pyre-ignore[21]
from app.api import auth, books, settings # pyre-ignore[21]
from app.websocket.handler import websocket_endpoint # pyre-ignore[21]
from app.core.database import Base, engine # pyre-ignore[21]
import os

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Book Factory Premium Dashboard")

# Basic CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(books.router, prefix="/api/books", tags=["Books"])
app.include_router(settings.router, prefix="/api/settings", tags=["Settings"])

# WebSockets
@app.websocket("/ws/{job_id}")
async def ws_route(websocket: WebSocket, job_id: str):
    await websocket_endpoint(websocket, job_id)

@app.get("/api/health")
def health():
    return {"status": "healthy"}

# Mount frontend static files
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
app.mount("/outputs", StaticFiles(directory=os.path.join(BASE_DIR, "books")), name="outputs")
app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "frontend"), html=True), name="frontend")
