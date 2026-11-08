# SolanaGuard AI

Understand Before You Sign.

SolanaGuard AI will retrieve real Solana transaction data, identify potential risks with transparent deterministic rules, and explain the results in beginner-friendly language.

## Phase 4 status

Phase 4 adds a backend-only Backboard AI explanation service and a responsive analysis dashboard. The deterministic risk engine remains authoritative. Wallet connection, signing, and execution are intentionally not implemented yet.

## Requirements

- Node.js 24 (Node.js 20.18 or newer is supported by the Solana development guidance)
- npm
- Python 3.12
- Python `venv` support

Rust, Anchor, Surfpool, and Solana JavaScript packages are not required for this phase.

## Setup

From the repository root:

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
npm --prefix frontend install
```

The Python virtual environment is ignored by Git. Never commit `.env` files or API credentials.

The backend reads `SOLANA_RPC_URL` from `backend/.env`. It defaults to the official Devnet endpoint, `https://api.devnet.solana.com`, when the variable is absent. For local development, the public endpoint is rate-limited; a private Devnet RPC URL may be configured later without changing application code.

Backboard configuration is backend-only:

```dotenv
BACKBOARD_API_KEY=your_backboard_api_key
BACKBOARD_BASE_URL=https://app.backboard.io/api
```

The frontend never receives or imports `BACKBOARD_API_KEY`. Without a key, transaction retrieval and deterministic analysis still work and the API reports the AI explanation as unavailable.

## Run the backend

```bash
backend/.venv/bin/python -m uvicorn app.main:app --app-dir backend --env-file backend/.env --reload --host 127.0.0.1 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

Expected response:

```json
{"status":"ok","service":"solanaguard-api"}
```

## Run the frontend

In a second terminal:

```bash
npm --prefix frontend run dev
```

Open the URL printed by Vite, normally `http://localhost:5173`.

## Analyze transaction risk

```bash
curl --fail --silent --show-error \\
  -X POST http://127.0.0.1:8000/api/analyze \\
  -H 'Content-Type: application/json' \\
  -d '{"signature":"<DEVNET_SIGNATURE>"}' | jq
```

The response contains normalized transaction facts, the deterministic risk score/category/findings, and an `ai_explanation` object. The AI explanation is optional and cannot change the deterministic result. Unknown programs are review signals, not malicious classifications.

## Run backend tests

```bash
backend/.venv/bin/python -m pytest backend/app/tests -q
```

The tests use labelled synthetic RPC fixtures and mocked HTTP calls. They do not present fixture data as real blockchain data. Never place the Backboard key in `frontend/.env.local` or commit `backend/.env`.

## Security boundaries

- The frontend contains only public configuration such as the backend URL.
- Backboard credentials belong only in the backend environment and are never exposed to the frontend.
- The application will never request seed phrases or private keys, sign transactions automatically, or claim that a transaction is guaranteed safe.
