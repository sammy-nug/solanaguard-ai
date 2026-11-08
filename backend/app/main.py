import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from app.routes.transaction import router as transaction_router
from app.routes.analysis import router as analysis_router


def configured_origins() -> list[str]:
    origins = os.getenv("FRONTEND_ORIGINS", os.getenv("FRONTEND_ORIGIN", "http://localhost:5173"))
    return [origin.strip() for origin in origins.split(",") if origin.strip()]


app = FastAPI(
    title="SolanaGuard AI API",
    description="Read-only transaction security analysis API.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=configured_origins(),
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

app.include_router(transaction_router)
app.include_router(analysis_router)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "solanaguard-api"}
