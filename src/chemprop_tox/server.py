"""Optional HTTP mode (`serve`). No authentication or user management.

POST /predict accepts 1..MAX_REQUEST_ITEMS SMILES. Per-molecule failures are
returned inside a 200 response; the request is rejected with 422 only when
every molecule fails, using the first failure's error code.
"""
import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from . import TOOL_ID, TOOL_NAME, __version__
from .engine import THRESHOLD, Predictor
from .errors import ToxError
from .inputs import records_from_smiles
from .service import run_records, to_json_record

log = logging.getLogger("chemprop_tox")


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


def create_app(cfg, predictor: Predictor | None = None) -> FastAPI:
    app = FastAPI(title=TOOL_NAME, version=__version__,
                  description="Offline Chemprop D-MPNN multi-task toxicity prediction (631 tasks). No authentication.")
    state = {"predictor": predictor}

    def get_predictor() -> Predictor:
        if state["predictor"] is None:
            state["predictor"] = Predictor(cfg)
        return state["predictor"]

    @app.on_event("startup")
    def _load():
        get_predictor()

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
