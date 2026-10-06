# Chemprop Toxicity Predictor — offline, inference-only, GPU (CPU fallback)
#
# Build (from the repository root, linux/amd64):
#   docker buildx build --platform linux/amd64 \
#     -t pzkeung/bio-synergy-platform:chemprop-1.0.0 -t pzkeung/bio-synergy-platform:chemprop --load .
#
# Run (T2 batch, no network):
#   docker run --rm --gpus all --network none \
#     -v $PWD/in:/data/input:ro -v $PWD/out:/data/output \
#     -e INPUT_PATH=/data/input/molecules.csv \
#     pzkeung/bio-synergy-platform:chemprop-1.0.0
#
# Same base image (CUDA 12.6 / Ubuntu 24.04 / Python 3.12), PyTorch, RDKit and
# chemprop source as the training image (chemprop-train). chemprop 2.3.1 is
# vendored in src/chemprop (MIT) and imported via PYTHONPATH. Everything
# needed at run time is inside the image.

FROM nvidia/cuda:12.6.3-cudnn-runtime-ubuntu24.04@sha256:8aef630a54bc5c5146ae5ce68e6af5caa3df0fb690bb91544175c91f307e4356

ARG UID=10001
ARG GID=10001

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_BREAK_SYSTEM_PACKAGES=1 \
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

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      python3=3.12.3-0ubuntu2.1 \
      python3-pip=24.0+dfsg-1ubuntu1.3 \
      libxrender1=1:0.9.10-1.1build1 \
      libxext6=2:1.3.4-1build2 \
      libglib2.0-0t64=2.80.0-6ubuntu3.9 \
      libgomp1=14.2.0-4ubuntu2~24.04.1 \
 && ln -sf /usr/bin/python3 /usr/bin/python \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.lock .
RUN python -m pip install --require-hashes --no-deps -r requirements.lock

RUN userdel -r ubuntu 2>/dev/null || true; \
    groupadd -g ${GID} app && useradd -u ${UID} -g ${GID} -M -s /usr/sbin/nologin app \
 && mkdir -p /data/input /data/output && chown -R app:app /data

COPY src/ ./src/
COPY models/ ./models/
COPY tool.yaml README.md LICENSE ./

USER app

# Any accidental runtime pip call cannot reach the network.
ENV PIP_NO_INDEX=1

EXPOSE 8000
HEALTHCHECK NONE

ENTRYPOINT ["python", "-m", "chemprop_tox"]
CMD ["batch"]
