import os
import uvicorn
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from database import init_db, get_db
from routers import upload, search
import logging

app = FastAPI(title="FaceFind AI Backend", version="1.0.0")

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize DB on startup
@app.on_event("startup")
def startup_event():
    logger.info("Initializing database...")
    init_db()
    logger.info("Database initialized.")

# CORS Setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to the frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(upload.router)
app.include_router(search.router)

# Serve photos as static files for testing
if os.path.exists("data/uploads"):
    app.mount("/photos", StaticFiles(directory="data/uploads"), name="photos")

@app.get("/")
def read_root():
    return {"message": "FaceFind AI Backend is running."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
