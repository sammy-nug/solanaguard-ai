from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.ai import AIExplanation
from app.schemas.transaction import TransactionResponse


FindingKind = Literal["verified", "potential", "unavailable"]
FindingSeverity = Literal["info", "low", "medium", "high", "critical"]
RiskCategory = Literal["low", "medium", "high", "critical", "insufficient_data"]
AnalysisStatus = Literal["complete", "incomplete"]


class RiskFinding(BaseModel):
    code: str
    title: str
    severity: FindingSeverity
    kind: FindingKind
    explanation: str
    evidence: list[str] = Field(min_length=1)
    score_impact: int = Field(ge=0, le=100)
    program_id: str | None = None
    account: str | None = None


class RiskAnalysis(BaseModel):
    score: int = Field(ge=0, le=100)
    category: RiskCategory
    analysis_status: AnalysisStatus
    findings: list[RiskFinding] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class AnalyzeRequest(BaseModel):
    signature: str = Field(min_length=1, max_length=128)


class AnalyzeResponse(BaseModel):
    transaction: TransactionResponse
    analysis: RiskAnalysis
    ai_explanation: AIExplanation
