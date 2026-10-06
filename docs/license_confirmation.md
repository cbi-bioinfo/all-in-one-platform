# 라이선스 확인서 — SSL-GCN Toxicity Predictor 1.0.0

확인일: 2026-10-06 · 대상: 저장소 브랜치 `ssl-gcn`, 이미지 `cbibioinfolab/toxicity-prediction:ssl-gcn-1.0.0`

## 1. 요약

| 구분 | 결론 |
|---|---|
| 본 저장소 코드 (`src/sslgcn_tox/`, `tests/`) | **라이선스 미기재** — 원 저장소에 라이선스가 없어 본 저장소도 라이선스를 붙이지 않음(본 과제 작성) |
| 원 논문 저장소 코드 | **포함하지 않음** (원 저장소에 라이선스 파일 없음 — 2절) |
| 모델 가중치 (601개) | 본 과제에서 학습 — 라이선스 미기재 |
| 모델 구현 라이브러리 | DGL-LifeSci `GCNPredictor` (Apache-2.0), DGL (Apache-2.0) |
| Python 의존성 | 허용형(BSD/MIT/Apache/PSF), 약한 카피레프트 MPL-2.0 2종(certifi, tqdm), NVIDIA CUDA 재배포 구성요소 — 3절 |
| 베이스 이미지 | `nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04` — NVIDIA Deep Learning Container License |
| 학습 데이터 | 패키지에 미포함. Tox21·ToxCast 공공 데이터, ClinTox 명시적 라이선스 미확인 — 4절 |
| GPL/AGPL 구성요소 | 없음 |

## 2. 소스 코드와 가중치

| 구성요소 | 경로 | 출처 | 라이선스 | 비고 |
|---|---|---|---|---|
| 추론 패키지 | `src/sslgcn_tox/` | 본 과제 작성 | 미기재 | 원 저장소 코드를 복사하지 않고 dgllife API로 작성 |
| 모델 구조 | (dgllife 라이브러리) | DGL-LifeSci `GCNPredictor`, `CanonicalAtomFeaturizer`, `mol_to_bigraph` | Apache-2.0 | 이미지의 pip 패키지로 포함 |
| 모델 가중치 | `models/sslgcn_pretrained.pt` | 본 과제 학습 산출물 (trainset holdout seed 0, 601개 태스크 모델 묶음) | 미기재 | 하이퍼파라미터 값은 원 논문의 공개 설정을 따름 |
| 원 논문 저장소 | — | https://github.com/chen709847237/SSL-GCN (2021-07-11 커밋 `b0df79c`) | **라이선스 파일 없음** | 평가 코드만 공개. 본 패키지는 이 저장소의 코드·가중치·데이터를 포함하지 않는다. 학습 루프는 논문의 식과 설명을 바탕으로 플랫폼에서 재구성했다(학습 코드는 제출 범위 밖) |

라이선스 표기가 없는 저장소는 저작권법상 기본적으로 모든 권리가 저작자에게
있으므로 코드 재배포를 피했다. 논문에 기술된 방법과 공개된 하이퍼파라미터 값의
이용은 저작물 복제에 해당하지 않는다고 판단했다.

## 3. 컨테이너 포함 소프트웨어

베이스 이미지: `nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04@sha256:85fb7ac694079fff1061a0140fd5b5a641997880e12112d92589c3bbb1e8b7ca`
— CUDA 런타임·cuDNN 포함, NVIDIA Deep Learning Container License(이미지 내
`/NGC-DL-CONTAINER-LICENSE`)와 CUDA EULA 적용. Ubuntu 22.04 패키지와 추가 OS 패키지
`python3.10`(PSF-2.0), `python3-pip`(MIT), `libxrender1`, `libxext6`(MIT/X11).

Python 패키지 (`requirements.lock`, 이미지에서 `pip-licenses`와 패키지 메타데이터로 추출):

| 패키지 | 버전 | 라이선스 |
|---|---|---|
| torch | 2.1.0+cu118 | BSD-3-Clause (CUDA 런타임 라이브러리 동봉 — NVIDIA 라이선스) |
| triton | 2.1.0 | MIT |
| dgl | 2.1.0+cu118 | Apache-2.0 |
| dgllife | 0.3.2 | Apache-2.0 |
| torchdata | 0.11.0 | BSD-3-Clause |
| rdkit | 2026.3.1 | BSD-3-Clause |
| numpy / scipy / pandas / scikit-learn | 1.26.4 / 1.15.3 / 2.3.3 / 1.7.2 | BSD-3-Clause |
| networkx, sympy, mpmath, hyperopt, joblib, threadpoolctl, cloudpickle, psutil, py4j, fsspec, jinja2, markupsafe, click, idna | — | BSD 계열 |
| fastapi, pydantic, pydantic-core, anyio, annotated-types, exceptiongroup, h11, filelock, future, pytz, six, urllib3, charset-normalizer | — | MIT |
| starlette, uvicorn | 0.27.0, 0.24.0 | BSD-3-Clause |
| requests | 2.33.1 | Apache-2.0 |
| sniffio | 1.3.1 | Apache-2.0 또는 MIT |
| python-dateutil | 2.9.0.post0 | Apache-2.0 및 BSD-3-Clause |
| tzdata | 2026.2 | Apache-2.0 |
| pillow | 12.2.0 | MIT-CMU (HPND) |
| typing-extensions | 4.15.0 | PSF-2.0 |
| **certifi** | 2026.2.25 | **MPL-2.0** (파일 단위 약한 카피레프트, 수정 없이 사용) |
| **tqdm** | 4.67.3 | **MPL-2.0 및 MIT** (수정 없이 사용) |

**설치 후 변경 1건:** `dgl/graphbolt/__init__.py`를 빈 파일로 교체했다(Dockerfile
주석 참조). graphbolt의 C++ 라이브러리가 이 torch 빌드에서 로드되지 않으며 본
모델은 graphbolt를 쓰지 않는다. 학습 이미지와 같은 처리다. DGL은 Apache-2.0으로
수정이 허용된다(변경 사실을 Dockerfile에 명시함).

**확인 필요 사항:** NVIDIA CUDA·cuDNN은 오픈소스가 아니며 NVIDIA 라이선스 조건으로
재배포된다. 배포처에서 독점 구성요소 포함을 제한하면 별도 협의가 필요하다.

## 4. 데이터

학습 데이터는 저장소와 이미지에 들어 있지 않다(`docs/reference_data.md`).

| 데이터 | 이용 조건 | 판단 |
|---|---|---|
| Tox21 (NIH NCATS/EPA/NTP) | 미국 연방정부 생산 데이터 | 학습 이용 가능, 공공 영역으로 간주 |
| ToxCast (US EPA) | 미국 연방정부 생산 데이터 | 학습 이용 가능, 공공 영역으로 간주 |
| ClinTox (Gayvert et al. 2016, MoleculeNet 재배포) | 명시적 데이터 라이선스 표기를 찾지 못함 | 학술 공개 데이터로 학습에 이용. **데이터 자체를 재배포하지 않음.** 상업적 이용 시 원저자 확인 권장 |
| 시험 입력 SMILES (`tests/`) | 위 데이터에서 고른 화학구조(라벨 없음) | 화학구조 표기 자체는 저작물성이 낮음 |

## 5. 기타

* 상표: "Tox21", "ToxCast", "MoleculeNet", "NVIDIA", "CUDA"는 출처 표기 목적으로만 사용했다.
* 본 확인서는 2026-10-06 기준 각 구성요소 메타데이터와 원 저장소 상태에 근거한다.
  법률 자문이 아니다.
