from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import time

from src.api.routers import (
    health,
    companies,
    screener,
    sectors,
    peers,
    valuation,
    portfolio,
    documents,
)

app = FastAPI(
    title="Nifty 100 Financial Intelligence API",
    version="1.0.0",
    description="REST API for the Nifty 100 Financial Intelligence Platform",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

START_TIME = time.time()


@app.middleware("http")
async def request_logging(request, call_next):
    start = time.time()

    response = await call_next(request)

    elapsed = time.time() - start

    print(
        f"{request.method} {request.url.path} "
        f"{response.status_code} {elapsed:.4f}s"
    )

    return response


app.include_router(
    health.router,
    prefix="/api/v1",
)

app.include_router(
    companies.router,
    prefix="/api/v1",
)

app.include_router(
    screener.router,
    prefix="/api/v1",
)

app.include_router(
    sectors.router,
    prefix="/api/v1",
)

app.include_router(
    peers.router,
    prefix="/api/v1",
)

app.include_router(
    valuation.router,
    prefix="/api/v1",
)

app.include_router(
    portfolio.router,
    prefix="/api/v1",
)

app.include_router(
    documents.router,
    prefix="/api/v1",
)


@app.get("/")
def root():
    return {
        "status": "ok",
        "service": "Nifty 100 Financial Intelligence API",
        "version": "1.0.0",
    }