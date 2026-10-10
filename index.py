import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"
SRC_DIR = BASE_DIR / "src"

for extra_path in (str(BASE_DIR), str(SRC_DIR)):
    if extra_path not in sys.path:
        sys.path.insert(0, extra_path)

from pipeline import run_analysis, run_execution_only
from schema import Schema

app = FastAPI(title="SQL Query Analyzer and Optimizer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    query: str


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/schema")
def schema_info():
    return Schema().as_dict()


@app.post("/api/analyze")
def analyze(request: AnalyzeRequest):
    return run_analysis(request.query)


@app.post("/api/execute")
def execute(request: AnalyzeRequest):
    return run_execution_only(request.query)


if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    def serve_index():
        return FileResponse(str(FRONTEND_DIR / "index.html"))

    @app.get("/{file_name}")
    def serve_frontend_file(file_name: str):
        candidate = FRONTEND_DIR / file_name
        if candidate.is_file():
            return FileResponse(str(candidate))
        return FileResponse(str(FRONTEND_DIR / "index.html"))
