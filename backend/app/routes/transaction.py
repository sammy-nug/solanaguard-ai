from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse

from app.schemas.transaction import TransactionResponse
from app.services.solana_service import SolanaService, TransactionServiceError
from app.services.transaction_parser import parse_transaction


router = APIRouter(prefix="/api/transaction", tags=["transactions"])


def get_solana_service() -> SolanaService:
    return SolanaService()


@router.get("/{signature}", response_model=TransactionResponse)
async def get_transaction(
    signature: str,
    service: Annotated[SolanaService, Depends(get_solana_service)],
) -> TransactionResponse | JSONResponse:
    try:
        transaction = await service.get_transaction(signature)
    except TransactionServiceError as error:
        return JSONResponse(
            status_code=error.status_code,
            content={"error": {"code": error.code, "message": error.message}},
        )
    return parse_transaction(signature, transaction)
