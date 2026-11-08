from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.schemas.risk import AnalyzeRequest, AnalyzeResponse
from app.services.backboard_service import BackboardExplanationService
from app.services.risk_engine import analyze_transaction
from app.services.solana_service import SolanaService, TransactionServiceError
from app.services.transaction_parser import parse_transaction
from app.routes.transaction import get_solana_service


router = APIRouter(prefix="/api", tags=["analysis"])


def get_backboard_service() -> BackboardExplanationService:
    return BackboardExplanationService()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze(
    request: AnalyzeRequest,
    service: Annotated[SolanaService, Depends(get_solana_service)],
    backboard: Annotated[BackboardExplanationService, Depends(get_backboard_service)],
) -> AnalyzeResponse | JSONResponse:
    try:
        raw_transaction = await service.get_transaction(request.signature)
    except TransactionServiceError as error:
        return JSONResponse(
            status_code=error.status_code,
            content={"error": {"code": error.code, "message": error.message}},
        )

    transaction = parse_transaction(request.signature, raw_transaction)
    analysis = analyze_transaction(transaction)
    ai_explanation = await backboard.explain(transaction, analysis)
    return AnalyzeResponse(
        transaction=transaction,
        analysis=analysis,
        ai_explanation=ai_explanation,
    )
