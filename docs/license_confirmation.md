# 라이선스 확인서 — FP-GNN Toxicity Predictor 1.0.0

확인일: 2026-10-06 · 대상: 저장소 브랜치 `fp-gnn`, 이미지 `cbibioinfolab/toxicity-prediction:fp-gnn-1.0.0`

## 1. 요약

| 구분 | 결론 |
|---|---|
| 원 모델 저장소 (idrugLab/FP-GNN) | **라이선스 파일 없음** — 그 코드는 포함하지 않음 (2절) |
| 본 저장소 코드 (`src/fpgnn_tox/`, `tests/`) | **라이선스 미기재** — 원 저장소에 라이선스가 없어 본 저장소도 라이선스를 붙이지 않음(본 과제 작성) |
| 포함 제3자 코드 (`src/pybiomed/PubChemFingerprints.py`) | PyBioMed, **BSD-3-Clause** — 원본 그대로, 라이선스 전문(`src/pybiomed/LICENSE.txt`)과 저작권 고지 유지 |
| 모델 가중치 | 본 과제 학습 산출물 — 라이선스 미기재 |
| Python 의존성 25종 | 허용형(BSD/MIT/Apache/PSF), NVIDIA CUDA 런타임은 torch 휠에 동봉 — 3절 |
| 베이스 이미지 | `nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04` — NVIDIA Deep Learning Container License |
| 학습 데이터 | 패키지에 미포함. Tox21·ToxCast 공공 데이터, ClinTox 명시적 라이선스 미확인 — 4절 |
| GPL/AGPL 구성요소 | 없음 |

## 2. 소스 코드와 가중치

### 2.1 원 모델 저장소에 라이선스가 없다는 근거

* 저장소: https://github.com/idrugLab/FP-GNN, 로컬 사본
  `/home/data/projects/drug_dev_platform/models/fp-gnn/FP-GNN`, 커밋
  `00cbdf20b4aa0125fb690fc3a867c3c65c692fbd` (2023-03-13).
* `git ls-files`와 파일 검색 결과 `LICENSE`·`COPYING`·`NOTICE` 등 라이선스 파일이 없다.
* `Readme.md`에 라이선스·저작권 문구가 없다(환경과 실행 명령만 설명).
* GitHub API(2026-10-06 조회)도 `license: null`이며 최신 커밋이 같은 `00cbdf2`다(이후 변경 없음).
* 플랫폼 내부 문서(`models/tox_pred/fp-gnn/NOTICE.md`)도 같은 결론을 기록하고, 외부 배포 전에
  원저자 확인이 필요하다고 적어 두었다.

따라서 원 저장소의 코드(`fpgnn/` 패키지)는 제출 패키지에 넣지 않았다. 추론 엔진
(`src/fpgnn_tox/engine.py`)은 본 과제에서 새로 작성했으며, 학습된 가중치를 그대로 읽을 수 있도록
신경망의 계층 구성과 매개변수 이름을 맞추고 같은 계산을 하도록 구현했다(모델 카드 4.3절의 일치
검증). 논문에 기술된 방법을 구현하는 것은 원 코드의 복제가 아니라고 판단했다.

### 2.2 PubChem 지문 코드 (PyBioMed)

원 FP-GNN 저장소의 `fpgnn/data/pubchemfp.py`는 파일 머리에 "copyed from PyBioMed"라고 적혀 있다.
본 패키지는 이 사본 대신 **PyBioMed 원본**을 포함한다.

| 항목 | 내용 |
|---|---|
| 출처 | https://github.com/gadsbyfly/PyBioMed, `PyBioMed/PyMolecule/PubChemFingerprints.py`, 커밋 `45440d8a70b2aa2818762ceadb499dd3a1df90bc` |
| 라이선스 | BSD-3-Clause, Copyright (c) 2016-2017 Zhijiang Yao, Jie Dong and Dongsheng Cao (`src/pybiomed/LICENSE.txt`, 파일 머리 고지 유지) |
| 수정 | 없음 (`src/pybiomed/__init__.py`만 새로 추가) |
| 동등성 | trainset 10,966분자에서 FP-GNN 학습 코드의 PubChem 지문과 881비트가 모두 같음, SMARTS 패턴 733개 동일 |

### 2.3 표

| 구성요소 | 경로 | 출처 | 라이선스 |
|---|---|---|---|
| 추론 패키지 | `src/fpgnn_tox/` | 본 과제 작성 | 미기재 |
| PubChem 지문 | `src/pybiomed/` | PyBioMed | BSD-3-Clause |
| 모델 가중치·설정 | `models/` | 본 과제 학습 산출물 (trainset holdout seed 0) | 미기재 |

## 3. 컨테이너 포함 소프트웨어

베이스 이미지: `nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04@sha256:85fb7ac694079fff1061a0140fd5b5a641997880e12112d92589c3bbb1e8b7ca`
— CUDA 런타임·cuDNN 포함, NVIDIA Deep Learning Container License(이미지 내
`/NGC-DL-CONTAINER-LICENSE`)와 CUDA EULA. Ubuntu 22.04 패키지와 추가 OS 패키지 `python3.10`(PSF-2.0),
`python3-pip`(MIT), `libxrender1`, `libxext6`(MIT/X11).

Python 패키지 (`requirements.lock`; 이미지에서 `pip-licenses`와 패키지 메타데이터로 추출):

| 패키지 | 버전 | 라이선스 |
|---|---|---|
| torch | 2.1.0+cu118 | BSD-3-Clause (CUDA 런타임 라이브러리 동봉 — NVIDIA 라이선스) |
| triton | 2.1.0 | MIT |
| rdkit | 2026.3.6 | BSD-3-Clause |
| numpy | 1.26.4 | BSD-3-Clause |
| networkx, sympy, mpmath, jinja2, markupsafe, click, idna, fsspec | — | BSD 계열 |
| fastapi, pydantic, pydantic-core, anyio, annotated-types, exceptiongroup, h11, filelock | — | MIT |
| starlette, uvicorn | 0.27.0, 0.24.0 | BSD-3-Clause |
| sniffio | 1.3.1 | Apache-2.0 또는 MIT |
| pillow | 12.3.0 | MIT-CMU (HPND) |
| typing-extensions | 4.15.0 | PSF-2.0 |

MPL·GPL 계열 패키지는 없다.

**확인 필요 사항:** NVIDIA CUDA·cuDNN은 오픈소스가 아니며 NVIDIA 라이선스 조건으로 재배포된다.
배포처에서 독점 구성요소 포함을 제한하면 별도 협의가 필요하다.

## 4. 데이터

학습 데이터는 저장소와 이미지에 들어 있지 않다(`docs/reference_data.md`).

| 데이터 | 이용 조건 | 판단 |
|---|---|---|
| Tox21 (NIH NCATS/EPA/NTP) | 미국 연방정부 생산 데이터 | 학습 이용 가능, 공공 영역으로 간주 |
| ToxCast (US EPA) | 미국 연방정부 생산 데이터 | 학습 이용 가능, 공공 영역으로 간주 |
| ClinTox (Gayvert et al. 2016, MoleculeNet 재배포) | 명시적 데이터 라이선스 표기를 찾지 못함 | 학술 공개 데이터로 학습에 이용. 데이터 자체를 재배포하지 않음. 상업적 이용 시 원저자 확인 권장 |
| 시험 입력 SMILES (`tests/`) | 위 데이터에서 고른 화학구조(라벨 없음) | 화학구조 표기 자체는 저작물성이 낮음 |

## 5. 남은 확인 사항

* 원 FP-GNN 저장소에 라이선스가 없으므로, 이 모델(가중치 포함)을 외부에 배포하기 전에 원저자
  (idrugLab)에게 이용 조건을 확인할 것을 권한다. 본 패키지는 원 코드를 포함하지 않지만 모델 설계는
  해당 논문에 따른다.
* 본 확인서는 2026-10-06 기준 각 구성요소 메타데이터와 원 저장소 상태에 근거한다. 법률 자문이 아니다.
