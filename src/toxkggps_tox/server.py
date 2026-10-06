"""HTTP mode (`serve`). No authentication or user management.

Service:
  GET  /healthz                 liveness (answers during model loading)
  GET  /readyz                  readiness (503 until the model is loaded)
  GET  /info                    tool id, version, model and settings
  GET  /schema                  accepted inputs, result columns, task list, error codes

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
import threading
from typing import Literal

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel, Field, ValidationError

from . import TOOL_ID, TOOL_NAME, __version__
from .engine import THRESHOLD, Predictor
from .errors import ERRORS, WARNINGS, ToxError
from .inputs import records_from_smiles
from .jobs import JobManager
from .service import run_records, to_json_record

log = logging.getLogger("toxkggps_tox")


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
    status: str = Field(..., description="'ok' while the process is alive")
    version: str


class ReadyResponse(BaseModel):
    status: Literal["ready", "loading", "failed"]
    device: str | None
    n_tasks: int | None
    error: ErrorBody | None = Field(..., description="Model load error when status is 'failed'")


class InfoResponse(BaseModel):
    tool_id: str
    name: str
    version: str
    deployment_type: str
    model: str
    model_sha256: str | None = Field(..., description="SHA-256 of the ToxKG-GPS weights (null until ready)")
    device: str | None = Field(..., description="Inference device (null until ready)")
    n_tasks: int | None = Field(..., description="Number of predicted tasks (null until ready)")
    threshold: float
    seed: int
    standardize: bool
    max_request_items: int
    max_smiles_length: int

    model_config = {"protected_namespaces": ()}  # allow the model_* field names


class SchemaResponse(BaseModel):
    input: dict = Field(..., description="Accepted file formats, constraints and JSON request schemas")
    output: dict = Field(..., description="Result columns, task list (output order) and JSON record schema")
    error_codes: dict[str, str]
    warning_codes: dict[str, str]


_FILE_FORMATS = {
    "csv": "Header row required; 'smiles' or 'canonical_smiles' column (case-insensitive); "
           "optional 'id'/'mol_id'/'name'/'compound_id' column",
    "txt": "One 'SMILES [ID]' per line, whitespace-separated, blank lines ignored",
    "sdf": "Multi-molecule SDF; molecule name (_Name) is the ID",
    "mol": "Single-molecule MOL file; file name is the ID",
}
_COLUMNS = [
    {"name": "index", "type": "integer", "description": "Input order (0-based)"},
    {"name": "id", "type": "string", "description": "Input ID, or mol_<index>"},
    {"name": "input_smiles", "type": "string", "description": "SMILES as given (SDF/MOL: converted by RDKit)"},
    {"name": "canonical_smiles", "type": "string", "description": "RDKit canonical SMILES used for prediction"},
    {"name": "status", "type": "string", "values": ["ok", "error"]},
    {"name": "error_code", "type": "string"},
    {"name": "error_message", "type": "string"},
    {"name": "warnings", "type": "string", "description": "Warning codes separated by ';'"},
    {"name": "<task>_prob", "type": "number", "unit": "probability (0-1)", "description": "One per task, 8 decimals"},
    {"name": "<task>_label", "type": "integer", "values": [0, 1], "description": "1 if <task>_prob >= threshold"},
]


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
                  description="ToxKG-GPS multi-task toxicity prediction (631 tasks).")
    state = {"predictor": predictor, "error": None}
    loaded = threading.Event()
    if predictor is not None:
        loaded.set()

    def load():
        try:
            state["predictor"] = Predictor(cfg)
        except ToxError as e:
            state["error"] = e
            log.error("%s", e)
        except Exception as e:
            log.exception("E-MODEL-001: model load failed")
            state["error"] = ToxError("E-MODEL-001", f"{type(e).__name__}: {e}")
        loaded.set()

    def get_predictor(wait: bool = False) -> Predictor:
        """The loaded model. Requests get 503 E-SYS-005 while it is loading;
        the job worker (wait=True) blocks until loading has finished."""
        if not loaded.is_set():
            if not wait:
                raise ToxError("E-SYS-005")
            loaded.wait()
        if state["error"] is not None:
            raise state["error"]
        return state["predictor"]

    jobs = JobManager(cfg, lambda: get_predictor(wait=True))

    @app.on_event("startup")
    def _start():
        # The model (~35 s) loads in the background so /healthz answers at once
        # and /readyz reports progress; queued jobs wait for it.
        if not loaded.is_set():
            threading.Thread(target=load, name="model-loader", daemon=True).start()
        jobs.start()

    @app.exception_handler(ToxError)
    async def _tox_error(_: Request, e: ToxError):
        return _error(e)

    @app.exception_handler(RequestValidationError)
    async def _schema_error(_: Request, e: RequestValidationError):
        detail = "; ".join(f"{'.'.join(map(str, x['loc']))}: {x['msg']}" for x in e.errors())
        return _error(ToxError("E-INPUT-011", detail))

    @app.get("/healthz", response_model=HealthResponse, tags=["service"], summary="Liveness",
             description="200 while the process is running, also during model loading.")
    def healthz():
        return {"status": "ok", "version": __version__}

    @app.get("/readyz", response_model=ReadyResponse, tags=["service"], summary="Readiness",
             description="200 once the model is loaded and requests can be served; "
                         "503 while loading (`loading`) or after a load error (`failed`).",
             responses={503: {"model": ReadyResponse}})
    def readyz():
        if not loaded.is_set():
            return JSONResponse(status_code=503, content={"status": "loading", "device": None,
                                                          "n_tasks": None, "error": None})
        if state["error"] is not None:
            return JSONResponse(status_code=503, content={"status": "failed", "device": None,
                                                          "n_tasks": None, "error": state["error"].to_dict()})
        p = state["predictor"]
        return {"status": "ready", "device": str(p.device), "n_tasks": len(p.tasks), "error": None}

    @app.get("/info", response_model=InfoResponse, tags=["service"], summary="Tool information")
    def info():
        p = state["predictor"] if loaded.is_set() else None
        return {"tool_id": TOOL_ID, "name": TOOL_NAME, "version": __version__, "deployment_type": "T2",
                "model": "GPS graph transformer (GINE + multi-head attention), one multi-task network (631 tasks)",
                "model_sha256": getattr(p, "model_sha256", None),
                "device": str(p.device) if p is not None else None,
                "n_tasks": len(p.tasks) if p is not None else None,
                "threshold": THRESHOLD, "seed": cfg.seed, "standardize": cfg.standardize,
                "max_request_items": cfg.max_request_items, "max_smiles_length": cfg.max_smiles_length}

    @app.get("/schema", response_model=SchemaResponse, tags=["service"], summary="Input/output schema",
             description="Accepted inputs and the structure of results, including the 631 task names "
                         "in output order. 503 until the model is loaded.",
             responses={503: {"model": ErrorResponse}})
    def schema():
        p = get_predictor()
        return {
            "input": {
                "file_formats": _FILE_FORMATS,
                "encoding": "UTF-8",
                "max_smiles_length": cfg.max_smiles_length,
                "predict_request": PredictRequest.model_json_schema(),
                "predict_max_items": cfg.max_request_items,
                "job_request": JobRequest.model_json_schema(),
                "job_query": {"input_format": list(_FILE_FORMATS), "output_format": ["csv", "json"]},
            },
            "output": {
                "threshold": THRESHOLD,
                "csv_columns": _COLUMNS,
                "tasks": p.tasks,
                "prediction_record": PredictionRecord.model_json_schema(),
            },
            "error_codes": {code: msg for code, (_, _, msg) in ERRORS.items()},
            "warning_codes": WARNINGS,
        }

    @app.post("/jobs", response_model=JobStatus, status_code=202, tags=["jobs"],
              summary="Submit a batch job",
              description="Queue a batch prediction job and return at once with its `job_id`. "
                          "Poll `GET /jobs/{job_id}` until `state` is `completed` or `failed`, "
                          "then download `GET /jobs/{job_id}/result`.",
              openapi_extra={"requestBody": _JOB_REQUEST_BODY},
              responses={413: {"model": ErrorResponse}, 422: {"model": ErrorResponse},
                         500: {"model": ErrorResponse}})
    async def submit_job(request: Request,
                         input_format: Literal["csv", "txt", "sdf", "mol"] = Query(
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

    @app.post("/predict", response_model=PredictResponse, tags=["predict"], summary="Synchronous prediction",
              description="Predict 1..MAX_REQUEST_ITEMS SMILES in one request. Use the job API for more.",
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
