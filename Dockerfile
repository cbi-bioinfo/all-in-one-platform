# SSL-GCN Toxicity Predictor — offline, inference-only, GPU (CPU fallback)
#
# Build (from the repository root, linux/amd64):
#   docker buildx build --platform linux/amd64 \
#     -t cbibioinfolab/toxicity-prediction:ssl-gcn-1.0.0 --load .
#
# Run (T2 batch, no network):
#   docker run --rm --gpus all --network none \
#     -v $PWD/in:/data/input:ro -v $PWD/out:/data/output \
#     -e INPUT_PATH=/data/input/molecules.csv \
#     cbibioinfolab/toxicity-prediction:ssl-gcn-1.0.0
#
# Same base image, Python, PyTorch/DGL/RDKit versions as the training image.
# Everything the container needs at run time is inside the image.

FROM nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04@sha256:85fb7ac694079fff1061a0140fd5b5a641997880e12112d92589c3bbb1e8b7ca

ARG UID=10001
ARG GID=10001

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/opt/app/src \
    DGLBACKEND=pytorch \
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
      python3.10=3.10.12-1~22.04.18 \
      python3-pip=22.0.2+dfsg-1ubuntu0.7 \
      libxrender1=1:0.9.10-1build4 \
      libxext6=2:1.3.4-1build1 \
 && ln -sf /usr/bin/python3.10 /usr/bin/python \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.lock .
RUN python -m pip install --require-hashes --no-deps -r requirements.lock

# dgl.graphbolt (DGL's out-of-core data loader) is imported by `import dgl` but
# its C++ library cannot be loaded with this torch build. SSL-GCN never uses
# graphbolt, so — exactly as in the training image — its package init is
# replaced by an empty stub. Nothing else in DGL is modified.
RUN printf '# graphbolt stub - not used by SSL-GCN inference (see Dockerfile)\n' \
      > /usr/local/lib/python3.10/dist-packages/dgl/graphbolt/__init__.py

RUN groupadd -g ${GID} app && useradd -u ${UID} -g ${GID} -M -s /usr/sbin/nologin app \
 && mkdir -p /data/input /data/output && chown -R app:app /data

COPY src/ ./src/
COPY models/ ./models/
COPY tool.yaml README.md ./

USER app

# Any accidental runtime pip call cannot reach the network.
ENV PIP_NO_INDEX=1

EXPOSE 8000
HEALTHCHECK NONE

ENTRYPOINT ["python", "-m", "sslgcn_tox"]
CMD ["batch"]
