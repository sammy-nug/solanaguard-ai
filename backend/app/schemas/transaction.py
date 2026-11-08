from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class AccountKey(BaseModel):
    model_config = ConfigDict(extra="allow")

    pubkey: str
    signer: bool | None = None
    writable: bool | None = None
    source: str | None = None


class ParsedInstruction(BaseModel):
    model_config = ConfigDict(extra="allow")

    instruction_type: Literal["parsed", "unparsed"]
    program_id: str | None = None
    program: str | None = None
    parsed: Any | None = None
    data: str | None = None
    accounts: list[Any] | None = None
    raw: dict[str, Any]


class InnerInstructionGroup(BaseModel):
    index: int | None = None
    instructions: list[ParsedInstruction]


class SolBalanceChange(BaseModel):
    account: str
    before: int
    after: int
    delta: int


class TokenBalanceChange(BaseModel):
    account_index: int
    mint: str | None = None
    owner: str | None = None
    before_amount: str | None = None
    after_amount: str | None = None
    decimals: int | None = None


class BalanceChanges(BaseModel):
    sol: list[SolBalanceChange] = Field(default_factory=list)
    tokens: list[TokenBalanceChange] = Field(default_factory=list)


class TransactionResponse(BaseModel):
    signature: str
    network: Literal["devnet"] = "devnet"
    status: Literal["confirmed", "failed", "unknown"]
    slot: int | None = None
    block_time: int | None = None
    fee: int | None = None
    account_keys: list[AccountKey] = Field(default_factory=list)
    instructions: list[ParsedInstruction] = Field(default_factory=list)
    inner_instructions: list[InnerInstructionGroup] = Field(default_factory=list)
    balance_changes: BalanceChanges = Field(default_factory=BalanceChanges)
    warnings: list[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    error: dict[str, str]
