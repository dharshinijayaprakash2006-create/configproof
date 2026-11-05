[![CI](https://github.com/dharshinijayaprakash2006-create/configproof/actions/workflows/ci.yml/badge.svg)](https://github.com/dharshinijayaprakash2006-create/configproof/actions/workflows/ci.yml)

# ConfigProof

**Live:** https://configproof.onrender.com/health · first request after 15 idle minutes takes about a minute (free tier)

ConfigProof - Automated Firmware Configuration Verification for Apache NuttX RTOS.

## Problem

Firmware developers and QA engineers working with Apache NuttX RTOS must manage thousands of configuration options across drivers, boards, power management, and security. Manually checking these settings takes time and can lead to missed dependencies or risky configuration changes. For example, accidentally disabling a watchdog setting may reduce a device's ability to recover from certain software failures. ConfigProof extracts configuration options into structured JSON, validates the extracted data, generates release checklists, and flags potentially risky changes before firmware release.

## Who it is for

- Firmware QA engineers at drone-electronics companies who verify flight-controller configurations before release.
- Embedded software developers building battery-powered devices using Apache NuttX RTOS who need to check configuration dependencies and power-management settings.

## Signature feature

ConfigProof combines structured Kconfig extraction with device-specific release checklists and a pull-request review agent that identifies potentially risky firmware configuration changes and links findings to their source files.

## Hardest problem (my interview story)

The hardest problem is accurately extracting configuration information from a large collection of Kconfig files while preserving each option's name, type, default value, dependencies, help text, and source location. Incorrectly extracted information could produce unreliable checklists or misleading warnings. I will validate the extracted data against 100 manually checked configuration options and aim for at least 95% field-level extraction accuracy.

## Dataset

| Source | Link | Documents | Pages | Licence / terms |
|---|---|---|---|---|
| Apache NuttX RTOS source repository | https://github.com/apache/nuttx | To be measured after cloning and scanning the repository | Not applicable; source code repository | Apache-2.0 for files covered by that licence; verify individual file headers and third-party components |

The dataset includes Kconfig files, board configurations, drivers, and relevant examples from the Apache NuttX repository. The actual number of files processed will be recorded after scanning the repository.

## 10 real questions

See [docs/QUESTIONS.md](docs/QUESTIONS.md).

The questions will cover watchdog configuration, configuration defaults, dependencies, low-power sleep examples, board-specific settings, memory and stack configuration, and potentially risky changes.

## Run it

```bash
git clone https://github.com/apache/nuttx.git
```

Clone the ConfigProof project repository separately, then run the following commands from its root directory.

```bash
python -m venv .venv
```

Activate the environment:

```bash
# Windows Command Prompt
.venv\Scripts\activate.bat

# Windows PowerShell
.venv\Scripts\Activate.ps1

# Linux / macOS
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements-dev.txt
```

Create the environment file:

```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```

Start the API:

```bash
uvicorn app.main:app --reload
```

Check the health endpoint:

```bash
curl http://localhost:8000/health
```

Note: These commands assume the project contains the specified files and endpoint. Adjust them to match the implementation if necessary.

## Live link

https://configproof.onrender.com/health

The app runs on Render's free tier, so the first request after 15 idle minutes takes about a minute. Files written to disk are lost on redeploy.

## Run with Docker

Requires Docker Desktop (Engine running).

```bash
cp .env.example .env        # Windows: Copy-Item .env.example .env
docker compose up --build
```

- API: http://127.0.0.1:8000
- Liveness: `GET /health` (process is up, no database call)
- Readiness: `GET /ready` (checks Postgres, returns 503 if it is down)
- Database: pgvector/pgvector:pg16 on port 5432 (user `app`, password `app`, database `rag`; local development only)

Stop everything with `docker compose down`. Add `-v` to also delete the database volume.

## Ingestion (GenAI 9)

Parsed pages are chunked by heading (max 1,000 characters, 150 overlap), embedded on the CPU with all-MiniLM-L6-v2 (384 dimensions), and stored in Postgres with pgvector and an HNSW cosine index. A SHA-256 content hash with a unique constraint means re-running adds nothing twice.

```bash
docker compose up -d db
python -m tools.preview_chunks data/parsed --n 5
python -m tools.ingest data/parsed --report INGESTION.md
```

Numbers from my runs are in [INGESTION.md](INGESTION.md).
