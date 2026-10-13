# Kinetic GFR Dynamic Calculator

A kinetic estimated glomerular filtration rate (KeGFR) calculator for changing serum creatinine, implementing the algebraic equation proposed by Chen (2013). Includes a dependency-free browser calculator, Python CLI and batch processor, and a FastAPI endpoint.

**Scope:** Educational and research calculations. KeGFR is not measured GFR, an AKI stage, or an independent drug-dosing/treatment recommendation. Review clinical assumptions and context.

## Calculate in a browser

Open `web/index.html` in a modern browser. No server, installation, Pyodide, external JavaScript, or internet connection is required. The page supports mg/dL and µmol/L creatinine values and exports the current result as CSV. A GitHub Pages deployment workflow is included, but no public deployment is claimed until the Pages workflow and live application are verified.

## Model

```text
MeanSCr = (SCr1 + SCr2) / 2
KeGFR = (SteadySCr × BaselineGFR / MeanSCr)
       × [1 − 24 × (SCr2 − SCr1) / (hours × max_rise_per_day)]
```

The baseline GFR (or creatinine clearance) must correspond to the entered *steady-state* creatinine. Earlier/later creatinine values must be chronologically ordered. The maximum anuric rise defaults to an illustrative **1.5 mg/dL/day**, not a patient-specific measured rate. All creatinine inputs use the selected unit (mg/dL or µmol/L); the maximum rise input remains in mg/dL/day. An implausible negative kinetic correction is rejected.

**Units:** Output has the same normalization as the supplied baseline clearance: mL/min or mL/min/1.73 m². Indexed eGFR is not interchangeable with absolute clearance for dosing. The estimate assumes relatively stable creatinine production and distribution volume; significant volume changes can make it misleading.

**Reference:** Chen S. Retooling the creatinine clearance equation to estimate kinetic GFR when the plasma creatinine is changing acutely. *J Am Soc Nephrol*. 2013;24(6):877–888. [PMID: 23704286](https://pubmed.ncbi.nlm.nih.gov/23704286/).

## Python CLI

Requires Python 3.10 or newer.

```bash
python -m pip install -e .
kinetic-gfr single --steady-state-creatinine 1 --baseline-gfr 90 \
  --creatinine-1 1.8 --creatinine-2 2.4 --hours 24
# KeGFR: 25.71 in the same clearance units as baseline_gfr
kinetic-gfr batch -i sample.csv -o results.csv
```

The core `kinetic_gfr.py` module itself needs only the Python standard library. CSV columns required: `steady_state_creatinine,baseline_gfr,creatinine_1,creatinine_2,hours`. Optional: `max_creatinine_rise_per_day,unit`. Invalid rows fail with the row number before output is written. Never use the same file for input and output.

## API and legacy tooling

```bash
python cli.py serve --host 127.0.0.1 --port 8000
# POST http://127.0.0.1:8000/api/kinetic-gfr
# GET  http://127.0.0.1:8000/docs
```

Sample request:

```json
{"steady_state_creatinine":1,"baseline_gfr":90,"creatinine_1":1.8,"creatinine_2":2.4,"hours":24}
```

The `agents/`, `enrichment.py`, and `cli.py audit/chat/batch` components are retained for compatibility. They implement demonstration-only generic thresholds and a mock conversational responder; **they do not perform clinical GFR interpretation or establish CAP/CLSI/ISO validation**. The HMAC audit log is process-local and should not be considered a production-grade security or medical record system. The `AUDIT_SECRET_KEY` variable is required by Docker Compose.

## Privacy and security

The static application runs locally in the browser. It does not transmit or persist inputs and uses no analytics, cookies, or remote dependencies. Do not enter patient identifiers. The server-based legacy module uses a limited regex identifier filter; **it is not a complete de-identification system or HIPAA compliance guarantee**. Keep any server deployment behind appropriate authentication and network restrictions; legacy endpoints are not authenticated.

## Development and verification

```bash
python -m pip install -e ".[dev]"
python -m pytest -q
node --test tests/test_web.cjs
python -m compileall -q kinetic_gfr.py cli.py agents tests
```

CI tests Python 3.10–3.12, checks dependencies, exercises the API, and verifies browser formula parity. GitHub Pages publishes the `web/` directory on merges to `master` when Pages is configured for GitHub Actions. The browser math is plain JavaScript, so Pyodide is unnecessary.

## License

[MIT](LICENSE).
