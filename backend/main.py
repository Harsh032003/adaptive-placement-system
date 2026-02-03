import os

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .db import Base, engine
from . import models
from .routes import admin_routes, auth_routes, quiz_routes

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")

os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

Base.metadata.create_all(bind=engine)

app.include_router(auth_routes.router)
app.include_router(quiz_routes.router)
app.include_router(admin_routes.router)
