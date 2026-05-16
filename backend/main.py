import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from api import auth, portfolios
from api.ws import router as ws_router

Base.metadata.create_all(bind=engine)

app = FastAPI(title="rentSIM API")

_raw = os.environ.get("ALLOWED_ORIGINS", "")
allowed_origins = [o.strip() for o in _raw.split(",") if o.strip()] or ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(portfolios.router)
app.include_router(ws_router)


@app.get("/health")
def health():
    return {"status": "ok"}
