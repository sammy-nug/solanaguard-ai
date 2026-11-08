from collections.abc import Iterable
from dataclasses import dataclass

from app.schemas.risk import RiskAnalysis, RiskFinding
from app.schemas.transaction import ParsedInstruction, TransactionResponse

KNOWN_PROGRAM_IDS = {"11111111111111111111111111111111": "System Program", "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA": "SPL Token Program", "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb": "Token-2022 Program", "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL": "Associated Token Program", "ComputeBudget111111111111111111111111111111": "Compute Budget Program", "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr": "Memo Program"}
TOKEN_PROGRAM_NAMES = {"spl-token", "spl-token-2022", "token"}
AUTHORITY_CHANGE_TYPES = {"setAuthority"}
DELEGATION_TYPES = {"approve", "approveChecked"}
PERMISSION_CHANGE_TYPES = {"assign", "allocate", "authorizeNonce"}

@dataclass(frozen=True)
class RiskScoringConfig:
    unfamiliar_program: int = 15
    token_authority_change: int = 30
    token_delegation: int = 25
    unusual_permission_change: int = 15
    maximum_score: int = 100

DEFAULT_SCORING = RiskScoringConfig()


def analyze_transaction(transaction: TransactionResponse, scoring: RiskScoringConfig = DEFAULT_SCORING) -> RiskAnalysis:
    findings: list[RiskFinding] = []
    warnings = list(transaction.warnings)
    score = 0
    unfamiliar_programs = unfamiliar_program_findings(transaction.instructions, transaction.inner_instructions, score_impact=scoring.unfamiliar_program)
    findings.extend(unfamiliar_programs)
    score += sum(finding.score_impact for finding in unfamiliar_programs)
    authority_finding = find_token_operation(transaction.instructions, transaction.inner_instructions, AUTHORITY_CHANGE_TYPES, code="token_authority_change", title="Token authority change requested", explanation="A parsed token instruction requests a change to an account or mint authority.", evidence_label="Parsed token authority instruction", score_impact=scoring.token_authority_change)
    if authority_finding is not None:
        findings.append(authority_finding)
        score += authority_finding.score_impact
    delegation_finding = find_token_operation(transaction.instructions, transaction.inner_instructions, DELEGATION_TYPES, code="token_delegation", title="Token delegation or approval requested", explanation="A parsed token instruction requests delegated spending authority over tokens.", evidence_label="Parsed token delegation instruction", score_impact=scoring.token_delegation)
    if delegation_finding is not None:
        findings.append(delegation_finding)
        score += delegation_finding.score_impact
    permission_finding = find_permission_change(transaction.instructions, transaction.inner_instructions, score_impact=scoring.unusual_permission_change)
    if permission_finding is not None:
        findings.append(permission_finding)
        score += permission_finding.score_impact
    if transaction.status == "failed":
        findings.append(RiskFinding(code="transaction_failed", title="Transaction failed", severity="info", kind="verified", explanation="The transaction metadata reports execution failure. This describes transaction status and is not, by itself, evidence of malicious intent.", evidence=["Transaction metadata contains a non-null execution error."], score_impact=0))
    incomplete = is_incomplete(transaction)
    if incomplete:
        findings.append(RiskFinding(code="insufficient_data", title="Insufficient transaction data", severity="info", kind="unavailable", explanation="The available transaction response is incomplete, so the score should not be interpreted as evidence that the transaction is safe.", evidence=incomplete_evidence(transaction), score_impact=0))
        warnings.append("Risk analysis is incomplete because required transaction data is unavailable.")
    score = min(score, scoring.maximum_score)
    return RiskAnalysis(score=score, category="insufficient_data" if incomplete else risk_category(score), analysis_status="incomplete" if incomplete else "complete", findings=findings, warnings=deduplicate(warnings))


def all_instructions(instructions: Iterable[ParsedInstruction], inner_groups: Iterable) -> list[ParsedInstruction]:
    result = list(instructions)
    for group in inner_groups:
        result.extend(group.instructions)
    return result


def unfamiliar_program_findings(instructions: Iterable[ParsedInstruction], inner_groups: Iterable, *, score_impact: int) -> list[RiskFinding]:
    program_ids = {instruction.program_id for instruction in all_instructions(instructions, inner_groups) if instruction.program_id and instruction.program_id not in KNOWN_PROGRAM_IDS}
    return [RiskFinding(code="unfamiliar_program", title="Unfamiliar program interaction", severity="medium", kind="potential", explanation="This program is not in the local recognized-program list. That is a review signal, not a claim that the program is malicious.", evidence=[f"Transaction instruction references unrecognized program {program_id}."], score_impact=score_impact, program_id=program_id) for program_id in sorted(program_ids)]


def parsed_instruction_type(instruction: ParsedInstruction) -> str | None:
    return instruction.parsed.get("type") if isinstance(instruction.parsed, dict) and isinstance(instruction.parsed.get("type"), str) else None


def is_token_instruction(instruction: ParsedInstruction) -> bool:
    return (instruction.program or "").lower() in TOKEN_PROGRAM_NAMES or instruction.program_id in {"TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA", "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb"}


def find_token_operation(instructions: Iterable[ParsedInstruction], inner_groups: Iterable, operation_types: set[str], *, code: str, title: str, explanation: str, evidence_label: str, score_impact: int) -> RiskFinding | None:
    for instruction in all_instructions(instructions, inner_groups):
        parsed_type = parsed_instruction_type(instruction)
        if parsed_type in operation_types and is_token_instruction(instruction):
            info = instruction.parsed.get("info", {}) if isinstance(instruction.parsed, dict) else {}
            account = info.get("account") if isinstance(info, dict) and isinstance(info.get("account"), str) else None
            evidence = [f"{evidence_label}: {parsed_type}."]
            if instruction.program_id:
                evidence.append(f"Program ID: {instruction.program_id}.")
            return RiskFinding(code=code, title=title, severity="high" if score_impact >= 30 else "medium", kind="verified", explanation=explanation, evidence=evidence, score_impact=score_impact, program_id=instruction.program_id, account=account)
    return None


def find_permission_change(instructions: Iterable[ParsedInstruction], inner_groups: Iterable, *, score_impact: int) -> RiskFinding | None:
    for instruction in all_instructions(instructions, inner_groups):
        parsed_type = parsed_instruction_type(instruction)
        if parsed_type in PERMISSION_CHANGE_TYPES and not is_token_instruction(instruction):
            evidence = [f"Parsed system permission operation: {parsed_type}."]
            if instruction.program_id:
                evidence.append(f"Program ID: {instruction.program_id}.")
            return RiskFinding(code="unusual_permission_change", title="Unusual account permission change", severity="medium", kind="verified", explanation="A parsed system instruction changes account ownership, allocation, or nonce authority.", evidence=evidence, score_impact=score_impact, program_id=instruction.program_id)
    return None


def is_incomplete(transaction: TransactionResponse) -> bool:
    return transaction.status == "unknown" or not transaction.account_keys or not transaction.instructions or any("metadata is unavailable" in warning.lower() for warning in transaction.warnings)


def incomplete_evidence(transaction: TransactionResponse) -> list[str]:
    evidence = [warning for warning in transaction.warnings if "unavailable" in warning.lower()]
    return evidence or ["The transaction did not contain enough normalized account or instruction data."]


def risk_category(score: int) -> str:
    if score < 20: return "low"
    if score < 50: return "medium"
    if score < 75: return "high"
    return "critical"


def deduplicate(values: Iterable[str]) -> list[str]:
    return list(dict.fromkeys(values))
