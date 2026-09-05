# Kinetic Gfr Dynamic Calculator

> **Domain:** Clinical Decision Support & Biomedical Computing  
> **Reference Guidelines & Standards:** Standard Clinical Formulations & ISO/IEC Quality Frameworks

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## Overview

Kinetic eGFR (KeGFR) for Rapidly Changing Creatinine. Calculates real-time dynamic glomerular filtration during acute kidney injury when steady-state CKD-EPI fails.

- Zero-dependency Python implementation with single and batch evaluation
- FastAPI REST API with OpenAPI 3.1 specification
- HMAC-SHA256 tamper-evident audit trail
- Zero-PHI outbound guard for HIPAA compliance

**Author:** Dr. Abu Suraih Sakhri  
**License:** MIT

---

## Installation

### From Source
```bash
git clone https://github.com/abusuraihsakhri/kinetic-gfr-dynamic-calculator.git
cd kinetic-gfr-dynamic-calculator
pip install -r requirements.txt
```

### Using Docker
```bash
docker build -t kinetic-gfr-dynamic-calculator .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=your-secret-key kinetic-gfr-dynamic-calculator
```

### Using Docker Compose
```bash
AUDIT_SECRET_KEY=your-secret-key docker-compose up
```

---

## Configuration

| Environment Variable | Description | Default |
|:---------------------|:------------|:--------|
| `AUDIT_SECRET_KEY` | Secret key for HMAC-SHA256 audit trail (required in production) | Auto-generated (dev only) |
| `MODEL_PROVIDER` | LLM provider (`mock`, `ollama`, `claude`, `openai`) | `mock` |

> **Security Note:** Always set `AUDIT_SECRET_KEY` in production. The application will warn and use a random key if not set.

---

## Usage

### CLI - Single Evaluation
```bash
python kinetic_gfr.py single --v1 14.5 --v2 4.2 --v3 1.8
```

### CLI - Batch Processing
```bash
python kinetic_gfr.py batch -i sample.csv -o results.csv
```

### Enterprise CLI (Full Feature Set)
```bash
# Run single task audit
python cli.py audit --task-id TASK-001 --primary 28.5 --secondary 14.2

# Batch processing
python cli.py batch -i sample.csv -o results.csv

# Verify audit trail integrity
python cli.py verify-audit

# Launch REST API server
python cli.py serve --host 127.0.0.1 --port 8000
```

### REST API Endpoints

| Method | Endpoint | Description |
|:-------|:---------|:------------|
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |
| POST | `/api/audit` | Process task payload |
| POST | `/api/chat` | Supervisory chat query |
| GET | `/api/audit/logs` | Audit trail with integrity verification |

### Example API Request
```bash
curl -X POST http://localhost:8000/api/audit \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "TASK-001",
    "target_identifier": "SPECIMEN-001",
    "primary_metric": 28.5,
    "secondary_metric": 14.2,
    "status_descriptor": "DISCORDANT_ANOMALY",
    "is_critical_flag": true
  }'
```

---

## Input Data Schema

### CSV Batch Format
```csv
Patient_ID,v1,v2,v3
PT-101,14.5,4.2,1.8
PT-102,8.0,2.1,0.5
PT-103,28.4,12.0,5.5
```

### API Payload
| Field | Type | Required | Description |
|:------|:-----|:---------|:------------|
| `task_id` | string | Yes | Unique task/case identifier |
| `target_identifier` | string | Yes | Entity or specimen target |
| `primary_metric` | float | Yes | Primary measurement value |
| `secondary_metric` | float | No | Secondary kinetic score |
| `status_descriptor` | string | No | Status code (default: NOMINAL) |
| `is_critical_flag` | boolean | No | Emergency escalation flag |

---

## Architecture

### Core Modules
- **`kinetic_gfr.py`** - Core calculation engine with single/batch processing
- **`cli.py`** - Enterprise CLI with audit, chat, batch, and serve commands
- **`agents/`** - Multi-agent orchestration framework:
  - `supervisor.py` - Master orchestrator
  - `workers.py` - Specialized domain workers (QC, Safety, Protocol)
  - `base.py` - Security guards, PHI protection, audit trail
  - `api.py` - FastAPI REST endpoints
  - `models.py` - Pydantic data schemas
  - `llm_factory.py` - LLM provider abstraction
  - `metrics.py` - Prometheus metrics exporter
  - `learning.py` - Bayesian calibration engine
  - `streamer.py` - WebSocket telemetry broadcaster
- **`enrichment.py`** - Extended domain feature engines

### Security Features
- **Zero-PHI Outbound Guard:** Regex-based detection blocking SSNs, MRNs, phone numbers, emails
- **HMAC-SHA256 Audit Trail:** Cryptographically chained, tamper-evident logging
- **Input Validation:** Pydantic schema validation on all API endpoints

---

## Testing

### Run All Tests
```bash
pytest -v
```

### Test Coverage
- `test_kinetic_gfr.py` - Core calculation and batch processing
- `tests/test_kinetic_gfr_dynamic_calculator.py` - Multi-agent system, workers, audit
- `tests/test_enrichment.py` - Enrichment engine suite

### Run Simulator
```bash
python simulator.py 100
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.
