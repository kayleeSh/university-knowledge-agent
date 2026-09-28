from fastapi import FastAPI

app = FastAPI(title="University Knowledge Agent")


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}