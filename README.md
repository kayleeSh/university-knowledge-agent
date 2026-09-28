# University Knowledge Agent

A two-week portfolio project for answering questions about public NUS and NTU
course, admissions, and policy information.

## Day 1: ingestion

Create an environment and install the project with its development dependencies:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Edit `data/sources.json` to add public page URLs or local HTML/PDF files. Then
run the ingestion script:

```powershell
python -m app.ingestion.run
```

Cleaned text chunks are written to `data/processed/chunks.json`. The default
splitter uses approximately 2,000 characters per chunk and 200 characters of
overlap (roughly 500/50 tokens for typical English text). No embeddings,
vector database, or paid service is used.

Run the tests with `python -m pytest`.

Start the API skeleton with:

```powershell
uvicorn app.api.main:app --reload
```

The health endpoint is available at `http://127.0.0.1:8000/health`.