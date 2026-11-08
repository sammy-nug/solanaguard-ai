from typing import Any

from app.schemas.transaction import AccountKey, BalanceChanges, InnerInstructionGroup, ParsedInstruction, SolBalanceChange, TokenBalanceChange, TransactionResponse


def parse_transaction(signature: str, transaction: dict[str, Any]) -> TransactionResponse:
    warnings: list[str] = []
    raw_transaction = transaction.get("transaction")
    message = raw_transaction.get("message") if isinstance(raw_transaction, dict) else None
    meta = transaction.get("meta")
    if not isinstance(message, dict):
        warnings.append("Transaction message data is unavailable.")
        message = {}
    if not isinstance(meta, dict):
        warnings.append("Transaction metadata is unavailable.")
        meta = {}
    account_keys = parse_account_keys(message.get("accountKeys"), warnings)
    instructions = parse_instructions(message.get("instructions"), warnings)
    inner_instructions = parse_inner_instructions(meta.get("innerInstructions"), warnings)
    balance_changes = parse_balance_changes(account_keys, meta.get("preBalances"), meta.get("postBalances"), meta.get("preTokenBalances"), meta.get("postTokenBalances"), warnings)
    if "err" not in meta:
        status = "unknown"
        warnings.append("Transaction status is unavailable because metadata is missing.")
    else:
        status = "failed" if meta["err"] is not None else "confirmed"
    return TransactionResponse(signature=signature, status=status, slot=transaction.get("slot") if isinstance(transaction.get("slot"), int) else None, block_time=transaction.get("blockTime") if isinstance(transaction.get("blockTime"), int) else None, fee=meta.get("fee") if isinstance(meta.get("fee"), int) else None, account_keys=account_keys, instructions=instructions, inner_instructions=inner_instructions, balance_changes=balance_changes, warnings=warnings)


def parse_account_keys(value: Any, warnings: list[str]) -> list[AccountKey]:
    if value is None:
        warnings.append("Account keys are unavailable.")
        return []
    if not isinstance(value, list):
        warnings.append("Account keys have an unexpected format.")
        return []
    accounts: list[AccountKey] = []
    for item in value:
        if isinstance(item, str):
            accounts.append(AccountKey(pubkey=item))
        elif isinstance(item, dict) and isinstance(item.get("pubkey"), str):
            accounts.append(AccountKey(**item))
        else:
            warnings.append("An account key could not be decoded.")
    return accounts


def parse_instructions(value: Any, warnings: list[str]) -> list[ParsedInstruction]:
    if value is None:
        warnings.append("Outer instructions are unavailable.")
        return []
    if not isinstance(value, list):
        warnings.append("Outer instructions have an unexpected format.")
        return []
    instructions: list[ParsedInstruction] = []
    for item in value:
        if isinstance(item, dict):
            instructions.append(parse_instruction(item, warnings))
        else:
            warnings.append("An outer instruction could not be decoded.")
    return instructions


def parse_inner_instructions(value: Any, warnings: list[str]) -> list[InnerInstructionGroup]:
    if value is None:
        return []
    if not isinstance(value, list):
        warnings.append("Inner instructions have an unexpected format.")
        return []
    groups: list[InnerInstructionGroup] = []
    for group in value:
        if not isinstance(group, dict):
            warnings.append("An inner instruction group could not be decoded.")
            continue
        raw_instructions = group.get("instructions", [])
        if not isinstance(raw_instructions, list):
            warnings.append("An inner instruction group has an unexpected format.")
            continue
        groups.append(InnerInstructionGroup(index=group.get("index") if isinstance(group.get("index"), int) else None, instructions=[parse_instruction(item, warnings) for item in raw_instructions if isinstance(item, dict)]))
    return groups


def parse_instruction(value: dict[str, Any], warnings: list[str]) -> ParsedInstruction:
    parsed = value.get("parsed")
    instruction_type = "parsed" if "parsed" in value else "unparsed"
    if instruction_type == "unparsed":
        warnings.append("An instruction is unparsed; its data was preserved without decoding.")
    return ParsedInstruction(instruction_type=instruction_type, program_id=value.get("programId") if isinstance(value.get("programId"), str) else None, program=value.get("program") if isinstance(value.get("program"), str) else None, parsed=parsed, data=value.get("data") if isinstance(value.get("data"), str) else None, accounts=value.get("accounts") if isinstance(value.get("accounts"), list) else None, raw=value)


def parse_balance_changes(account_keys: list[AccountKey], pre_balances: Any, post_balances: Any, pre_token_balances: Any, post_token_balances: Any, warnings: list[str]) -> BalanceChanges:
    sol_changes: list[SolBalanceChange] = []
    if pre_balances is not None or post_balances is not None:
        if not isinstance(pre_balances, list) or not isinstance(post_balances, list):
            warnings.append("SOL balance changes have an unexpected format.")
        elif len(pre_balances) != len(post_balances) or len(pre_balances) > len(account_keys):
            warnings.append("SOL balance changes could not be aligned with account keys.")
        else:
            for index, (before, after) in enumerate(zip(pre_balances, post_balances)):
                if isinstance(before, int) and isinstance(after, int):
                    sol_changes.append(SolBalanceChange(account=account_keys[index].pubkey, before=before, after=after, delta=after - before))
    else:
        warnings.append("SOL balance changes are unavailable.")
    return BalanceChanges(sol=sol_changes, tokens=parse_token_balance_changes(pre_token_balances, post_token_balances, warnings))


def parse_token_balance_changes(pre: Any, post: Any, warnings: list[str]) -> list[TokenBalanceChange]:
    if pre is None and post is None:
        warnings.append("SPL token balance changes are unavailable.")
        return []
    if not isinstance(pre, list) or not isinstance(post, list):
        warnings.append("SPL token balance changes have an unexpected format.")
        return []
    before_by_index = {item["accountIndex"]: item for item in pre if isinstance(item, dict) and isinstance(item.get("accountIndex"), int)}
    after_by_index = {item["accountIndex"]: item for item in post if isinstance(item, dict) and isinstance(item.get("accountIndex"), int)}
    if len(before_by_index) != len(pre) or len(after_by_index) != len(post):
        warnings.append("A token balance entry could not be aligned with an account index.")
    changes: list[TokenBalanceChange] = []
    for account_index in sorted(set(before_by_index) | set(after_by_index)):
        before = before_by_index.get(account_index, {})
        after = after_by_index.get(account_index, {})
        before_amount = (before.get("uiTokenAmount") or {}).get("amount")
        after_amount = (after.get("uiTokenAmount") or {}).get("amount")
        amount_info = after.get("uiTokenAmount") or before.get("uiTokenAmount") or {}
        changes.append(TokenBalanceChange(account_index=account_index, mint=after.get("mint") or before.get("mint"), owner=after.get("owner") or before.get("owner"), before_amount=before_amount, after_amount=after_amount, decimals=amount_info.get("decimals") if isinstance(amount_info.get("decimals"), int) else None))
    return changes
