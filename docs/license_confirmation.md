# 라이선스 확인서 — Chemprop Toxicity Predictor 1.0.0

확인일: 2026-10-06 · 대상: 저장소 브랜치 `chemprop`, 이미지 `cbibioinfolab/toxicity-prediction:chemprop-1.0.0`

## 1. 요약

| 구분 | 결론 |
|---|---|
| 업스트림 모델 코드 | Chemprop 2.3.1 — **MIT** (© 2024 The Chemprop Development Team 외). 원문: 루트 `LICENSE`(업스트림 v2.3.1 `LICENSE.txt`와 바이트 단위 동일, 이미지 `/opt/app/LICENSE`). 같은 내용의 `src/chemprop/LICENSE.txt` 사본은 중복이라 두지 않음 |
| 본 저장소 코드 (`src/chemprop_tox/`, `tests/`) | 업스트림과 같은 MIT 조건으로 함께 배포(저장소 루트 `LICENSE`) |
| 모델 가중치 | 본 과제에서 chemprop으로 학습 — 저장소 `LICENSE`(MIT) 조건으로 함께 배포 |
| Python 의존성 79종 | 허용형(BSD/MIT/Apache/PSF), 약한 카피레프트 MPL-2.0 1종(tqdm, MIT 병기), NVIDIA CUDA 재배포 구성요소 — 3절 |
| 베이스 이미지 | `nvidia/cuda:12.6.3-cudnn-runtime-ubuntu24.04` — NVIDIA Deep Learning Container License |
| 학습 데이터 | 패키지에 미포함. Tox21·ToxCast 공공 데이터, ClinTox 명시적 라이선스 미확인 — 4절 |
| GPL/AGPL 구성요소 | 없음 |

## 2. 소스 코드와 가중치

| 구성요소 | 경로 | 출처 | 라이선스 | 의무 이행 |
|---|---|---|---|---|
| Chemprop 2.3.1 | `src/chemprop/` | https://github.com/chemprop/chemprop (플랫폼 vendored 사본) | MIT | 저작권·허가 고지를 루트 `LICENSE`에 유지 |
| 업스트림 대비 변경 | `src/chemprop/UPSTREAM_pyproject.toml` 주석 | 플랫폼 vendoring 시 변경 | MIT | 의존성 선언 2개 제거(`cuik_molmaker_pin`, `myerson` — 미사용 선택 기능), `cuik_molmaker` 지연 import, 학습 지표 계산의 영(0)-라벨 태스크 예외 처리(`cli/train.py`). 변경 사실이 해당 파일에 주석으로 남아 있다. 추론에 쓰는 특징화·모델 계산은 변경 없음(`src/chemprop/featurizers/molgraph/molecule.py`는 import 방식만 변경) |
| 추론 래퍼 | `src/chemprop_tox/` | 본 과제 작성 | MIT (저장소 `LICENSE`) | — |
| 모델 가중치·설정 | `models/chemprop_pretrained.pt`, `..._config.json` | 본 과제 학습 산출물 (trainset holdout seed 0) | MIT (저장소 `LICENSE`) | — |

## 3. 컨테이너 포함 소프트웨어

베이스 이미지: `nvidia/cuda:12.6.3-cudnn-runtime-ubuntu24.04@sha256:8aef630a54bc5c5146ae5ce68e6af5caa3df0fb690bb91544175c91f307e4356`
— CUDA 런타임·cuDNN 포함, NVIDIA Deep Learning Container License(이미지 내
`/NGC-DL-CONTAINER-LICENSE`)와 CUDA EULA 적용. Ubuntu 24.04 패키지와 추가 OS 패키지
`python3` 3.12(PSF-2.0), `python3-pip`(MIT), `libxrender1`·`libxext6`(MIT/X11),
`libglib2.0-0t64`(LGPL-2.1, 동적 링크), `libgomp1`(GPL-3.0 + GCC Runtime Library
Exception — 런타임 예외로 링크 프로그램에 GPL 의무가 전파되지 않음). `python3-wheel`(MIT)이
함께 설치된다.

Python 패키지 (`requirements.lock`, 이미지에서 `pip-licenses`와 패키지 메타데이터·LICENSE
파일로 확인):

| 패키지 | 버전 | 라이선스 |
|---|---|---|
| torch | 2.6.0+cu126 | BSD-3-Clause |
| triton | 3.2.0 | MIT |
| lightning, pytorch-lightning, lightning-utilities, torchmetrics | 2.6.6, 2.6.6, 0.15.3, 1.9.0 | Apache-2.0 |
| rdkit | 2026.3.6 | BSD-3-Clause |
| numpy / scipy / pandas / scikit-learn | 2.5.3 / 1.18.1 / 3.0.6 / 1.9.1 | BSD-3-Clause (numpy는 0BSD·MIT·Zlib·CC0 구성요소 포함) |
| descriptastorus | 2.8.0 | BSD-3-Clause (© Novartis, 패키지 LICENSE 파일로 확인) |
| mordredcommunity | 2.0.7 | BSD-3-Clause |
| astartes, aimsim-core, padelpy, pandas-flavor, mhfp, ConfigArgParse, rich, markdown-it-py, mdurl, tabulate, narwhals, PyYAML, six, attrs, filelock, h11, anyio, annotated-types, fastapi, pydantic, pydantic-core, setuptools | — | MIT |
| networkx, multiprocess, dill, cloudpickle, joblib, threadpoolctl, psutil, fsspec, idna, click, markupsafe, jinja2, sympy, mpmath, Pygments, starlette, uvicorn | — | BSD 계열 |
| aiohttp | 3.14.3 | Apache-2.0 및 MIT |
| aiosignal, frozenlist, multidict, propcache, yarl, xarray | — | Apache-2.0 |
| aiohappyeyeballs, typing-extensions | 2.7.1, 4.16.0 | PSF-2.0 |
| sniffio | 1.3.1 | MIT 또는 Apache-2.0 |
| packaging | 26.3 | Apache-2.0 또는 BSD-2-Clause |
| python-dateutil | 2.9.0.post0 | Apache-2.0 및 BSD-3-Clause |
| pillow | 12.3.0 | MIT-CMU (HPND) |
| **tqdm** | 4.70.1 | **MPL-2.0 및 MIT** (수정 없이 사용) |
| nvidia-cublas, cuda-cupti, cuda-nvrtc, cuda-runtime, cudnn, cufft, curand, cusolver, cusparse, cusparselt, nccl, nvjitlink (`-cu12`) | 12.x / 9.5 | NVIDIA 독점 소프트웨어 라이선스 — PyTorch 공식 휠이 의존하는 재배포 구성요소 |
| nvidia-nvtx-cu12 | 12.6.77 | Apache-2.0 |

**확인 필요 사항:** NVIDIA CUDA·cuDNN 라이브러리는 오픈소스가 아니며 NVIDIA 라이선스
조건으로 재배포된다. 배포처에서 독점 구성요소 포함을 제한하면 별도 협의가 필요하다.

## 4. 데이터

학습 데이터는 저장소와 이미지에 들어 있지 않다(`docs/reference_data.md`).

| 데이터 | 이용 조건 | 판단 |
|---|---|---|
| Tox21 (NIH NCATS/EPA/NTP) | 미국 연방정부 생산 데이터 | 학습 이용 가능, 공공 영역으로 간주 |
| ToxCast (US EPA) | 미국 연방정부 생산 데이터 | 학습 이용 가능, 공공 영역으로 간주 |
| ClinTox (Gayvert et al. 2016, MoleculeNet 재배포) | 명시적 데이터 라이선스 표기를 찾지 못함 | 학술 공개 데이터로 학습에 이용. **데이터 자체를 재배포하지 않음** |
| 시험 입력 SMILES (`tests/`) | 위 데이터에서 고른 화학구조(라벨 없음)와 직접 작성한 경계 시험 구조 | 화학구조 표기 자체는 저작물성이 낮음 |

## 5. 기타

* 상표: "Chemprop", "Tox21", "ToxCast", "MoleculeNet", "NVIDIA", "CUDA"는 출처 표기
  목적으로만 사용했다.
* 본 확인서는 2026-10-06 기준 각 구성요소 메타데이터와 업스트림 LICENSE 파일에 근거한다.
  법률 자문이 아니다.
