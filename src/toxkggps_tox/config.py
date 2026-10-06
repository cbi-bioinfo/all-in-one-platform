"""Runtime configuration — every path and knob comes from an environment variable."""
import os
from dataclasses import dataclass
from pathlib import Path


def _bool(name: str, default: str) -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Config:
    input_path: Path | None
    output_dir: Path
    output_format: str
    model_dir: Path
    model_path: Path
    model_config: Path
    checkpoint_dir: Path
    resume: bool
    device: str
    seed: int
    chunk_size: int
    max_chunks_per_run: int
    standardize: bool
    max_smiles_length: int
    max_request_items: int
    jobs_dir: Path
    job_max_upload_mb: int
    verify_checksum: bool
    host: str
    port: int
    log_level: str

    @classmethod
    def from_env(cls) -> "Config":
        model_dir = Path(os.getenv("MODEL_DIR", "/opt/app/models"))
        output_dir = Path(os.getenv("OUTPUT_DIR", "/data/output"))
        input_path = os.getenv("INPUT_PATH")
        return cls(
            input_path=Path(input_path) if input_path else None,
            output_dir=output_dir,
            output_format=os.getenv("OUTPUT_FORMAT", "csv").strip().lower(),
            model_dir=model_dir,
            model_path=Path(os.getenv("MODEL_PATH", str(model_dir / "toxkggps_pretrained.pt"))),
            model_config=Path(os.getenv("MODEL_CONFIG", str(model_dir / "toxkggps_pretrained_config.json"))),
            checkpoint_dir=Path(os.getenv("CHECKPOINT_DIR", str(output_dir / ".checkpoint"))),
            resume=_bool("RESUME", "1"),
            device=os.getenv("DEVICE", "auto").strip().lower(),
            seed=int(os.getenv("SEED", "42")),
            chunk_size=int(os.getenv("CHUNK_SIZE", "1000")),
            max_chunks_per_run=int(os.getenv("MAX_CHUNKS_PER_RUN", "0")),
            standardize=_bool("STANDARDIZE", "0"),
            max_smiles_length=int(os.getenv("MAX_SMILES_LENGTH", "1000")),
            max_request_items=int(os.getenv("MAX_REQUEST_ITEMS", "100")),
            jobs_dir=Path(os.getenv("JOBS_DIR", str(output_dir / "jobs"))),
            job_max_upload_mb=int(os.getenv("JOB_MAX_UPLOAD_MB", "1024")),
            verify_checksum=_bool("VERIFY_CHECKSUM", "1"),
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8000")),
            log_level=os.getenv("LOG_LEVEL", "INFO").upper(),
        )
