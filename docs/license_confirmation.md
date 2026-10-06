# 라이선스 확인서 — GROVER Toxicity Predictor 1.0.0

확인일: 2026-10-06 · 대상: 브랜치 `grover`, 이미지 `cbibioinfolab/toxicity-prediction:grover-1.0.0`

## 1. 요약

| 구분 | 결론 |
|---|---|
| 업스트림 모델 코드 | **MIT** — tencent-ailab/grover, Copyright (c) 2021 Tencent AI Lab. 원문(chemprop MIT 고지 포함)을 루트 `LICENSE`에 그대로 수록(업스트림 `LICENSE`와 바이트 단위 동일, 이미지 `/opt/app/LICENSE`). 같은 내용의 `src/grover/LICENSE` 사본은 중복이라 두지 않음 |
| 본 저장소 코드(`src/grover_tox/`, `tests/`) | 업스트림과 같은 MIT로 배포(루트 `LICENSE`) |
| 모델 가중치 | 업스트림 MIT 공개 가중치(`grover_base.pt`)에서 미세조정한 본 과제 산출물 — MIT |
| Python 의존성 42종 | 허용형(BSD/MIT/Apache/PSF), MPL-2.0 1종(tqdm, 수정 없이 사용), NVIDIA CUDA 재배포 구성요소 |
| 베이스 이미지 | `nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04` — NVIDIA Deep Learning Container License |
| 학습 데이터 | 미포함. Tox21·ToxCast 공공 데이터, ClinTox 명시적 라이선스 미확인 |
| GPL/AGPL | 없음 |

## 2. 업스트림 코드 수록 내역 (`src/grover/`)

출처: https://github.com/tencent-ailab/grover, 확인 시점 커밋 `40b6d97098e4508687912f3c05eca369fc2c6213`.
`grover/` 패키지의 `data`, `model`, `util` 모듈만 수록했다(학습 스크립트·예제 데이터 제외).
MIT는 수정을 허용하며, 원본과 다른 파일은 다음과 같다.

| 파일 | 변경 | 사유 |
|---|---|---|
| `grover/__init__.py`, `grover/model/__init__.py`, `grover/util/__init__.py` | 새 파일(빈 패키지 표시) | 패키지 import |
| `grover/util/utils.py` | `# PATCH` 주석 7곳: RDKit이 거부한 분자(None) 처리, 최신 numpy·torch 호환(`weights_only=False` 등), 학습 스케줄 경계 처리 | 최신 RDKit/torch 호환 |
| `grover/util/scheduler.py` | `# PATCH` 1곳: warmup 경계 처리 | 짧은 학습 실행 안정성 |

추론 코드(`src/grover_tox/engine.py`)는 업스트림 `BatchMolGraph`와 같은 그래프를 만들되 패딩
폭을 고정하는 함수를 새로 작성했다(업스트림 파일은 수정하지 않음).

## 3. 컨테이너 포함 소프트웨어

베이스 이미지 digest `sha256:85fb7ac694079fff1061a0140fd5b5a641997880e12112d92589c3bbb1e8b7ca`
(CUDA 11.8 런타임·cuDNN 8, `/NGC-DL-CONTAINER-LICENSE`). apt: `python3.10`(PSF-2.0),
`python3-pip`(MIT), `libxrender1`·`libxext6`(MIT/X11).

Python 패키지(`requirements.lock`, 이미지에서 `pip-licenses`와 메타데이터로 추출):

| 패키지 | 버전 | 라이선스 |
|---|---|---|
| torch | 2.2.1+cu118 | BSD-3-Clause |
| triton | 2.2.0 | MIT |
| rdkit | 2026.3.6 | BSD-3-Clause |
| numpy / scipy / scikit-learn | 1.26.4 / 1.15.3 / 1.7.2 | BSD-3-Clause |
| networkx, sympy, mpmath, joblib, threadpoolctl, cloudpickle, fsspec, jinja2, markupsafe, click, idna | — | BSD 계열 |
| fastapi, pydantic, pydantic-core, anyio, annotated-types, exceptiongroup, h11, filelock | — | MIT |
| starlette / uvicorn | 0.27.0 / 0.24.0 | BSD-3-Clause |
| sniffio | 1.3.1 | Apache-2.0 또는 MIT |
| pillow | 12.3.0 | MIT-CMU |
| typing-extensions | 4.16.0 | PSF-2.0 |
| **tqdm** | 4.70.0 | **MPL-2.0 및 MIT** (수정 없음) |
| nvidia-cublas, cuda-cupti, cuda-nvrtc, cuda-runtime, cudnn, cufft, curand, cusolver, cusparse, nccl, nvtx (`-cu11`) | 11.x / 8.7 | NVIDIA 소프트웨어 라이선스(독점) — PyTorch 공식 휠 의존성 |

**확인 필요:** NVIDIA CUDA·cuDNN은 오픈소스가 아니며 NVIDIA 조건으로 재배포된다.

## 4. 데이터

학습 데이터는 저장소·이미지에 없다(`docs/reference_data.md`). Tox21·ToxCast는 미국 연방정부 생산
데이터(공공 영역으로 간주). ClinTox는 명시적 데이터 라이선스를 찾지 못했으며 데이터 자체는
재배포하지 않는다. 시험 입력은 화학구조 SMILES(라벨 없음)만 포함한다.

본 확인서는 2026-10-06 기준 메타데이터와 업스트림 저장소에 근거하며 법률 자문이 아니다.
