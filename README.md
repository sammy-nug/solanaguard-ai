# SolanaGuard AI

> Understand before you sign.

SolanaGuard AI is a read-only Solana transaction security assistant. It retrieves real Devnet transaction data, explains what the transaction appears to do, scores transparent security signals, and uses Backboard AI to make the findings easier to understand.

[GitHub Repository](https://github.com/sammy-nug/solanaguard-ai)

## What It Does

- Accepts a Solana transaction signature.
- Retrieves the confirmed transaction from Solana Devnet.
- Preserves parsed and undecoded instructions.
- Extracts accounts, programs, status, fees, balance changes, and warnings.
- Applies deterministic, evidence-backed risk rules.
- Generates an optional plain-language explanation through Backboard AI.
- Clearly separates blockchain facts, rule-based findings, and AI commentary.

This is advisory analysis, not a guarantee that a transaction is safe.

## Architecture

```text
React + Vite frontend
        |
        | POST /api/analyze
        v
FastAPI API
  |             |
  v             v
Solana RPC   Risk engine
(Devnet)     (deterministic)
                 |
                 v
           Backboard AI
        (explanation only)
```

The AI never controls the numerical risk score or category. If Backboard is unavailable, the deterministic analysis is still returned.

## Technology Stack

- **Frontend:** React, TypeScript, Vite, CSS
- **Backend:** Python, FastAPI, Pydantic, Uvicorn
- **Blockchain:** Solana Devnet JSON-RPC
- **RPC client:** Python `httpx`
- **AI:** Backboard API via `POST /threads/messages`
- **Testing:** pytest, pytest-asyncio, mocked HTTP transports
- **Configuration:** backend and frontend environment files

The project does not use Rust, Anchor, wallet adapters, or Solana JavaScript SDKs. Wallet connection and transaction signing are intentionally outside the current read-only workflow.

## Requirements

- Node.js 24
- npm
- Python 3.12
- Python virtual environment support

## Setup

From the repository root:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
npm --prefix frontend install
```

The `.env` files, virtual environment, dependencies, and build output are excluded from Git. Never commit API keys.

### Backend Configuration

`backend/.env`:

```dotenv
APP_ENV=development
FRONTEND_ORIGIN=http://localhost:5173
SOLANA_RPC_URL=https://api.devnet.solana.com
BACKBOARD_API_KEY=your_backboard_api_key
BACKBOARD_BASE_URL=https://app.backboard.io/api
```

`SOLANA_RPC_URL` defaults to the official Devnet endpoint when omitted. `BACKBOARD_API_KEY` is used only by the backend and is never exposed to the frontend.

## Run Locally

Start the backend:

```bash
backend/.venv/bin/python -m uvicorn app.main:app \
  --app-dir backend \
  --env-file backend/.env \
  --reload \
  --host 127.0.0.1 \
  --port 8000
```

Start the frontend in a second terminal:

```bash
npm --prefix frontend run dev
```

Open the Vite URL, normally `http://localhost:5173`.

Check the backend:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok","service":"solanaguard-api"}
```

## API

### `GET /api/transaction/{signature}`

Retrieves and parses a confirmed Devnet transaction.

```bash
curl --fail --silent --show-error \
  http://127.0.0.1:8000/api/transaction/<DEVNET_SIGNATURE> | jq
```

The RPC request uses `jsonParsed` encoding, `confirmed` commitment, and `maxSupportedTransactionVersion: 1`. Unavailable or undecoded information is reported through `warnings` instead of being invented.

### `POST /api/analyze`

Retrieves a transaction, runs the deterministic risk engine, and optionally requests a Backboard explanation.

```bash
curl --fail --silent --show-error \
  -X POST http://127.0.0.1:8000/api/analyze \
  -H 'Content-Type: application/json' \
  -d '{"signature":"<DEVNET_SIGNATURE>"}' | jq
```

The response contains:

- `transaction`: normalized facts retrieved from Devnet.
- `analysis`: deterministic score, category, findings, and warnings.
- `ai_explanation`: available Backboard explanation or an explicit unavailable status.

Example response shape:

```json
{
  "transaction": {
    "signature": "<DEVNET_SIGNATURE>",
    "network": "devnet",
    "status": "confirmed",
    "slot": 123,
    "fee": 5000,
    "warnings": []
  },
  "analysis": {
    "score": 15,
    "category": "low",
    "analysis_status": "complete",
    "findings": [],
    "warnings": []
  },
  "ai_explanation": {
    "available": false,
    "status": "unavailable",
    "error": "Backboard AI is unavailable because BACKBOARD_API_KEY is not configured."
  }
}
```

Invalid signatures return HTTP 422. Unknown transactions return HTTP 404. RPC timeouts return HTTP 504. Backboard failures do not fail the deterministic analysis.

## Deterministic Risk Model

The risk engine uses transparent heuristic signals:

| Signal | Score |
| --- | ---: |
| Unfamiliar program interaction | +15 |
| Token authority change | +30 |
| Token delegation or approval | +25 |
| Explicit system account permission change | +15 |

Scores are capped at 100:

- **Low:** 0–19
- **Medium:** 20–49
- **High:** 50–74
- **Critical:** 75–100

Repeated instances of the same indicator are deduplicated. Failed transactions are reported separately and do not automatically receive a maliciousness score. Incomplete transaction data produces `insufficient_data` rather than implying safety.

An unfamiliar program is a review signal, not proof of malicious behavior. Every finding includes evidence from the normalized transaction.

## Backboard AI

The backend calls Backboard with:

- `POST /threads/messages`
- `X-API-Key` authentication
- Non-streaming output
- JSON output mode
- Memory disabled

Backboard receives the transaction facts and deterministic findings as untrusted data. Its role is limited to explaining the existing analysis in plain language. It cannot change the score, category, or evidence, and unsupported finding codes are discarded.

## Testing

Run the backend tests:

```bash
PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/app/tests -q
```

Build the frontend:

```bash
npm --prefix frontend run build
```

Tests use labelled synthetic transaction fixtures and mocked RPC/Backboard HTTP calls. No test fixture is presented as real blockchain data, and no real API key is required.

## Security Boundaries

- No private keys or seed phrases are requested or stored.
- No transaction is signed or executed.
- Backboard credentials remain on the backend.
- On-chain data, logs, memos, token names, and program metadata are treated as untrusted input.
- AI output is never treated as authoritative security evidence.
- The application never claims that a transaction is guaranteed safe.

## Repository Structure

```text
backend/
  app/
    routes/
    schemas/
    services/
    tests/
    main.py
  .env.example
  requirements.txt
frontend/
  src/
    components/
    hooks/
    pages/
    services/
    App.tsx
    main.tsx
  .env.example
  package.json
.gitignore
README.md
```
