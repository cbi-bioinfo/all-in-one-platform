"""Entry point: python -m chemprop_tox [batch|serve|openapi|version]

batch    (default) process INPUT_PATH -> OUTPUT_DIR and exit       [T2]
serve    start the HTTP API on HOST:PORT: job API (submit/status/result) and
         /predict (see /api/openapi.yaml)
openapi  print the OpenAPI document generated from the code (JSON)
version  print the tool version
"""
import json
import logging
import sys

from . import TOOL_ID, __version__
from .config import Config
from .errors import ToxError


def main(argv: list[str]) -> int:
    mode = argv[0] if argv else "batch"
    try:
        cfg = Config.from_env()
    except ValueError as e:
        print(f"E-SYS-004: Invalid configuration value — {e}", file=sys.stderr)
        return 4
    logging.basicConfig(level=cfg.log_level, stream=sys.stderr,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    log = logging.getLogger("chemprop_tox")

    try:
        if mode == "batch":
            from .batch import run
            return run(cfg)
        if mode == "serve":
            import uvicorn
            from .server import create_app
            uvicorn.run(create_app(cfg), host=cfg.host, port=cfg.port, log_level=cfg.log_level.lower())
            return 0
        if mode == "openapi":
            from .server import create_app
            print(json.dumps(create_app(cfg, predictor=object()).openapi(), indent=2))
            return 0
        if mode == "version":
            print(f"{TOOL_ID} {__version__}")
            return 0
        print(__doc__, file=sys.stderr)
        return 4
    except ToxError as e:
        log.error("%s", e)
        return e.exit_code or 4
    except Exception:
        log.exception("E-SYS-003: Unexpected internal error")
        return 4


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
