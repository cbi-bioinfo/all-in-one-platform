"""HTTP mode (`serve`). No authentication or user management.

T2 job interface (any input size, runs in the background):
  POST /jobs                    submit an input file (or a JSON SMILES list) -> 202 + job_id
  GET  /jobs/{job_id}           job state and progress
  GET  /jobs/{job_id}/result    predictions file once the job is completed

POST /predict is the synchronous shortcut for 1..MAX_REQUEST_ITEMS SMILES.
Per-molecule failures are returned inside a 200 response; the request is
rejected with 422 only when every molecule fails, using the first failure's
error code.
"""
import csv
import io
import json
import logging
from typing import Literal

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field, ValidationError

from . import TOOL_ID, TOOL_NAME, __version__
from .engine import THRESHOLD, Predictor
from .errors import ToxError
from .inputs import records_from_smiles
from .jobs import JobManager
from .service import run_records, to_json_record

log = logging.getLogger("mtdnn_tox")


class PredictRequest(BaseModel):
    smiles: list[str] = Field(..., description="SMILES strings to predict (1..MAX_REQUEST_ITEMS)")
    ids: list[str] | None = Field(None, description="Optional identifiers, same order as `smiles`")

    model_config = {"json_schema_extra": {"example": {"smiles": ["CC(=O)Nc1ccc(O)cc1"], "ids": ["acetaminophen"]}}}


class ErrorBody(BaseModel):
    code: str
    message: str
    detail: str | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class TaskPrediction(BaseModel):
    probability: float = Field(..., description="Predicted probability of the toxic/active class, 0–1")
    label: int = Field(..., description="1 if probability >= 0.5 else 0")


class PredictionRecord(BaseModel):
    index: int
    id: str
    input_smiles: str | None
    canonical_smiles: str | None
    status: str = Field(..., description="'ok' or 'error'")
    error: ErrorBody | None
    warnings: list[str]
    predictions: dict[str, TaskPrediction] | None


class PredictResponse(BaseModel):
    tool_id: str
    version: str
    n_items: int
    n_ok: int
    n_error: int
    results: list[PredictionRecord]


class JobRequest(BaseModel):
    smiles: list[str] = Field(..., description="SMILES strings to predict (no item limit)")
    ids: list[str] | None = Field(None, description="Optional identifiers, same order as `smiles`")


class JobStatus(BaseModel):
    job_id: str
    state: Literal["queued", "running", "completed", "failed"]
    input_format: str
    output_format: str
    submitted_at: str
    started_at: str | None
    finished_at: str | None
    elapsed_sec: float | None
    n_total: int | None = Field(..., description="Molecules in the input (known once the job has started)")
    n_processed: int
    progress_percent: float
    chunks: int | None
    chunks_completed: int
    error: ErrorBody | None = Field(..., description="Job-level error when state is 'failed'")
    summary: dict | None = Field(..., description="run_summary.json of the finished run (same as batch mode)")


class HealthResponse(BaseModel):
    status: str
    version: str
    device: str
    n_tasks: int


class InfoResponse(BaseModel):
    tool_id: str
    name: str
    version: str
    threshold: float
    seed: int
    max_request_items: int
    standardize: bool
    tasks: list[str]


def _error(e: ToxError) -> JSONResponse:
    return JSONResponse(status_code=e.http_status, content={"error": e.to_dict()})


def _smiles_to_csv(body: bytes) -> bytes:
    try:
        req = JobRequest.model_validate(json.loads(body))
    except (ValueError, ValidationError) as e:
        raise ToxError("E-INPUT-011", str(e).splitlines()[0])
    if not req.smiles:
        raise ToxError("E-INPUT-006", "'smiles' is an empty list")
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(["id", "smiles"])
    for i, s in enumerate(req.smiles):
        w.writerow([req.ids[i] if req.ids and i < len(req.ids) else "", s])
    return buf.getvalue().encode()


_FILE_BODY = {"schema": {"type": "string", "format": "binary"}}
_JOB_REQUEST_BODY = {
    "required": True,
    "description": "Input file content in the format given by `input_format` "
                   "(same formats as batch mode), or a JSON object with a SMILES list.",
    "content": {
        "application/json": {"schema": {"$ref": "#/components/schemas/JobRequest"}},
        "text/csv": _FILE_BODY,
        "text/plain": _FILE_BODY,
        "chemical/x-daylight-smiles": _FILE_BODY,
        "chemical/x-mdl-sdfile": _FILE_BODY,
        "chemical/x-mdl-molfile": _FILE_BODY,
        "application/octet-stream": _FILE_BODY,
    },
}
_RESULT_CONTENT = {
    "text/csv": {"schema": {"type": "string"}, "example": "index,id,input_smiles,canonical_smiles,status,..."},
    "application/json": {"schema": {"type": "array", "items": {"$ref": "#/components/schemas/PredictionRecord"}}},
}


def create_app(cfg, predictor: Predictor | None = None) -> FastAPI:
    app = FastAPI(title=TOOL_NAME, version=__version__,
                  description="MTDNN multi-task toxicity prediction (631 tasks).")
    state = {"predictor": predictor}

    def get_predictor() -> Predictor:
        if state["predictor"] is None:
            state["predictor"] = Predictor(cfg)
        return state["predictor"]

    jobs = JobManager(cfg, get_predictor)

    @app.on_event("startup")
    def _load():
        get_predictor()
        jobs.start()

    @app.exception_handler(ToxError)
    async def _tox_error(_: Request, e: ToxError):
        return _error(e)

    @app.exception_handler(RequestValidationError)
    async def _schema_error(_: Request, e: RequestValidationError):
        detail = "; ".join(f"{'.'.join(map(str, x['loc']))}: {x['msg']}" for x in e.errors())
        return _error(ToxError("E-INPUT-011", detail))

    @app.get("/health", response_model=HealthResponse)
    def health():
        p = get_predictor()
        return {"status": "ok", "version": __version__, "device": str(p.device), "n_tasks": len(p.tasks)}

    @app.get("/info", response_model=InfoResponse)
    def info():
        p = get_predictor()
        return {"tool_id": TOOL_ID, "name": TOOL_NAME, "version": __version__, "threshold": THRESHOLD,
                "seed": cfg.seed, "max_request_items": cfg.max_request_items,
                "standardize": cfg.standardize, "tasks": p.tasks}

    @app.post("/jobs", response_model=JobStatus, status_code=202, tags=["jobs"],
              summary="Submit a batch job",
              description="Queue a batch prediction job and return at once with its `job_id`. "
                          "Poll `GET /jobs/{job_id}` until `state` is `completed` or `failed`, "
                          "then download `GET /jobs/{job_id}/result`.",
              openapi_extra={"requestBody": _JOB_REQUEST_BODY},
              responses={413: {"model": ErrorResponse}, 422: {"model": ErrorResponse},
                         500: {"model": ErrorResponse}})
    async def submit_job(request: Request,
                         input_format: Literal["csv", "smi", "txt", "sdf", "mol"] = Query(
                             "csv", description="Format of a file body (ignored for application/json)"),
                         output_format: Literal["csv", "json"] = Query("csv", description="Result file format")):
        limit = cfg.job_max_upload_mb * 1024 * 1024
        if int(request.headers.get("content-length") or 0) > limit:
            raise ToxError("E-INPUT-012", f"> {cfg.job_max_upload_mb} MB")
        body = await request.body()
        if len(body) > limit:
            raise ToxError("E-INPUT-012", f"> {cfg.job_max_upload_mb} MB")
        if request.headers.get("content-type", "").split(";")[0].strip() == "application/json":
            body, input_format = _smiles_to_csv(body), "csv"
        job = jobs.submit(body, input_format, output_format)
        return JSONResponse(status_code=202, content=job, headers={"Location": f"/jobs/{job['job_id']}"})

    @app.get("/jobs/{job_id}", response_model=JobStatus, tags=["jobs"], summary="Job status",
             responses={404: {"model": ErrorResponse}, 422: {"model": ErrorResponse}})
    def job_status(job_id: str):
        return jobs.get(job_id)

    @app.get("/jobs/{job_id}/result", tags=["jobs"], summary="Job result",
             description="Predictions file of a completed job (same content as batch-mode "
                         "`predictions.csv` / `predictions.json`). 409 while the job is queued, running or failed.",
             response_class=FileResponse,
             responses={200: {"content": _RESULT_CONTENT},
                        404: {"model": ErrorResponse}, 409: {"model": ErrorResponse},
                        422: {"model": ErrorResponse}})
    def job_result(job_id: str):
        path, fmt = jobs.result_path(job_id)
        return FileResponse(path, media_type="text/csv" if fmt == "csv" else "application/json",
                            filename=f"predictions_{job_id}.{fmt}")

    @app.post("/predict", response_model=PredictResponse,
              responses={413: {"model": ErrorResponse}, 422: {"model": ErrorResponse},
                         500: {"model": ErrorResponse}, 503: {"model": ErrorResponse}})
    def predict(req: PredictRequest):
        n = len(req.smiles)
        if n == 0:
            raise ToxError("E-INPUT-006", "'smiles' is an empty list")
        if n > cfg.max_request_items:
            raise ToxError("E-INPUT-003", f"{n} > {cfg.max_request_items}")
        p = get_predictor()
        results = [to_json_record(r, p.tasks) for r in run_records(p, records_from_smiles(req.smiles, req.ids), cfg)]
        n_err = sum(r["status"] == "error" for r in results)
        if n_err == n:
            first = results[0]["error"]
            status = 422 if first["code"].startswith("E-INPUT") else 500
            return JSONResponse(status_code=status, content={"error": first})
        return {"tool_id": TOOL_ID, "version": __version__, "n_items": n,
                "n_ok": n - n_err, "n_error": n_err, "results": results}

    return app
