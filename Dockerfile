# MTDNN Toxicity Predictor — offline, inference-only, GPU (CPU fallback)
#
# Build (from the repository root, linux/amd64):
#   docker buildx build --platform linux/amd64 \
#     -t cbibioinfolab/toxicity-prediction:mtdnn-1.0.0 --load .
#
# Run (T2 batch, no network):
#   docker run --rm --gpus all --network none \
#     -v $PWD/in:/data/input:ro -v $PWD/out:/data/output \
#     -e INPUT_PATH=/data/input/molecules.csv \
#     cbibioinfolab/toxicity-prediction:mtdnn-1.0.0
#
# Everything the container needs at run time (code, Python packages, model
# weights, SE encoder) is inside the image; it never downloads anything.

FROM python:3.10-slim@sha256:c1aaf3d03e14944a039a1647e0b3f6f34c6bee517bac6ff380215ee099c4e808

ARG UID=10001
ARG GID=10001

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/opt/app/src \
    CUBLAS_WORKSPACE_CONFIG=:4096:8 \
    NVIDIA_VISIBLE_DEVICES=all \
    NVIDIA_DRIVER_CAPABILITIES=compute,utility \
    MODEL_DIR=/opt/app/models \
    OUTPUT_DIR=/data/output \
    DEVICE=auto \
    SEED=42 \
    CHUNK_SIZE=1000 \
    OUTPUT_FORMAT=csv \
    PORT=8000

WORKDIR /opt/app

# RDKit wheels need these X libs for their drawing module, even headless.
RUN apt-get update \
 && apt-get install -y --no-install-recommends libxrender1 libxext6 \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.lock .
RUN pip install --require-hashes --no-deps -r requirements.lock

RUN groupadd -g ${GID} app && useradd -u ${UID} -g ${GID} -M -s /usr/sbin/nologin app \
 && mkdir -p /data/input /data/output && chown -R app:app /data

COPY src/ ./src/
COPY models/ ./models/
COPY tool.yaml README.md LICENSE NOTICE ./

USER app

# Pass PIP_NO_INDEX so any accidental runtime pip call cannot reach the network.
ENV PIP_NO_INDEX=1

EXPOSE 8000
HEALTHCHECK NONE

ENTRYPOINT ["python", "-m", "mtdnn_tox"]
CMD ["batch"]
