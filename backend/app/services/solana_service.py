import os
from typing import Any

import httpx


DEVNET_RPC_URL = "https://api.devnet.solana.com"
BASE58_ALPHABET = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"


class TransactionServiceError(Exception):
    def __init__(self, code: str, message: str, status_code: int) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


def validate_signature(signature: str) -> None:
    if not signature or not 32 <= len(signature) <= 88:
        raise TransactionServiceError("invalid_signature", "The transaction signature format is invalid.", 422)
    if any(character.encode() not in BASE58_ALPHABET for character in signature):
        raise TransactionServiceError("invalid_signature", "The transaction signature must use base58 characters.", 422)
    value = 0
    for character in signature.encode():
        value = value * 58 + BASE58_ALPHABET.index(character)
    decoded = value.to_bytes((value.bit_length() + 7) // 8, "big") if value else b""
    decoded = b"\x00" * (len(signature) - len(signature.lstrip("1"))) + decoded
    if len(decoded) != 64:
        raise TransactionServiceError("invalid_signature", "The transaction signature must decode to 64 bytes.", 422)


class SolanaService:
    def __init__(self, rpc_url: str | None = None, timeout_seconds: float = 10.0, client: httpx.AsyncClient | None = None) -> None:
        self.rpc_url = rpc_url or os.getenv("SOLANA_RPC_URL") or DEVNET_RPC_URL
        self.timeout = httpx.Timeout(timeout_seconds)
        self.client = client

    async def get_transaction(self, signature: str) -> dict[str, Any]:
        validate_signature(signature)
        request = {"jsonrpc": "2.0", "id": 1, "method": "getTransaction", "params": [signature, {"encoding": "jsonParsed", "commitment": "confirmed", "maxSupportedTransactionVersion": 1}]}
        if self.client is not None:
            return await self._request(self.client, request)
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            return await self._request(client, request)

    async def _request(self, client: httpx.AsyncClient, request: dict[str, Any]) -> dict[str, Any]:
        try:
            response = await client.post(self.rpc_url, json=request)
            response.raise_for_status()
        except httpx.TimeoutException as error:
            raise TransactionServiceError("rpc_timeout", "The Solana Devnet RPC request timed out.", 504) from error
        except httpx.HTTPError as error:
            raise TransactionServiceError("rpc_unavailable", "The Solana Devnet RPC endpoint is unavailable.", 503) from error
        try:
            payload = response.json()
        except ValueError as error:
            raise TransactionServiceError("malformed_rpc_response", "The Solana RPC returned invalid JSON.", 502) from error
        if not isinstance(payload, dict) or payload.get("jsonrpc") != "2.0":
            raise TransactionServiceError("malformed_rpc_response", "The Solana RPC returned an unexpected response.", 502)
        rpc_error = payload.get("error")
        if rpc_error is not None:
            message = rpc_error.get("message", "The Solana RPC returned an error.") if isinstance(rpc_error, dict) else str(rpc_error)
            code = rpc_error.get("code") if isinstance(rpc_error, dict) else None
            if code == -32015 or "unsupported transaction version" in message.lower():
                raise TransactionServiceError("unsupported_transaction_version", "The RPC endpoint does not support the requested transaction version.", 502)
            raise TransactionServiceError("rpc_error", message, 502)
        if "result" not in payload:
            raise TransactionServiceError("malformed_rpc_response", "The Solana RPC response did not contain a result.", 502)
        if payload["result"] is None:
            raise TransactionServiceError("transaction_not_found", "No confirmed transaction was found for this signature on Devnet.", 404)
        if not isinstance(payload["result"], dict):
            raise TransactionServiceError("malformed_rpc_response", "The Solana RPC returned an unexpected transaction shape.", 502)
        return payload["result"]
