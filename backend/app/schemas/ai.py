from typing import Literal

from pydantic import BaseModel, Field


class AIDetectedIssue(BaseModel):
    code: str
    explanation: str


class AIExplanationContent(BaseModel):
    summary: str
    transaction_purpose: str
    risk_explanation: str
    detected_issues: list[AIDetectedIssue] = Field(default_factory=list)
    positive_indicators: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    confidence_notes: list[str] = Field(default_factory=list)


class AIExplanation(BaseModel):
    available: bool
    status: Literal["available", "unavailable"]
    summary: str | None = None
    transaction_purpose: str | None = None
    risk_explanation: str | None = None
    detected_issues: list[AIDetectedIssue] = Field(default_factory=list)
    positive_indicators: list[str] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    confidence_notes: list[str] = Field(default_factory=list)
    error: str | None = None
