# 라이선스 확인서 — SE-MTDNN Toxicity Predictor 1.0.0

확인일: 2026-10-06 · 대상: 저장소 브랜치 `mtdnn`, 이미지 `pzkeung/bio-synergy-platform:mtdnn-1.0.0`

## 1. 요약

| 구분 | 결론 |
|---|---|
| 본 저장소 코드 (`src/mtdnn_tox/`, `tests/`) | Apache-2.0 (`LICENSE`) |
| 포함 제3자 코드 (`src/moses/`) | MIT — 고지문 포함, 수정 없음 |
| 모델 가중치 — SE 인코더 | Apache-2.0 (원 논문 저장소) — 고지문 포함, 수정 없음 |
| 모델 가중치 — MTDNN | 본 과제에서 원 논문 코드(Apache-2.0)로 학습 → Apache-2.0으로 배포 |
| Python 의존성 44종 | 허용형(BSD/MIT/Apache/PSF/MPL-2.0 이중) 및 NVIDIA CUDA 재배포 라이브러리 — 아래 3절 |
| 학습 데이터 | 패키지에 미포함. Tox21·ToxCast 공공 데이터, ClinTox 명시적 라이선스 미확인 — 아래 4절 |
| 카피레프트(GPL/AGPL) 구성요소 | 없음 |

## 2. 소스 코드와 가중치

| 구성요소 | 경로 | 출처 | 라이선스 | 의무 이행 |
|---|---|---|---|---|
| 추론 패키지 | `src/mtdnn_tox/` | 본 과제 작성. `MTDNN` 클래스 구조는 원 논문 저장소 구조를 따름 | Apache-2.0 | `LICENSE` |
| MOSES | `src/moses/` | https://github.com/molecularsets/moses (© 2018 Insilico Medicine) — IBM/multitask-toxicity `SE_featurization/moses/` 경유 | MIT | `src/moses/LICENSE` 고지문 유지, 수정 없음 |
| SE 인코더 가중치 | `models/se_encoder/` | https://github.com/IBM/multitask-toxicity `SE_featurization/` | Apache-2.0 | `models/se_encoder/LICENSE` 사본 포함, 수정 없음 |
| MTDNN 가중치 | `models/mtdnn_trainset_seed0.pt` | 본 과제 학습 산출물 | Apache-2.0 | — |

## 3. 컨테이너 포함 소프트웨어

베이스 이미지: `python:3.10-slim` (Debian, digest
`sha256:c1aaf3d03e14944a039a1647e0b3f6f34c6bee517bac6ff380215ee099c4e808`) —
Python(PSF-2.0) 및 Debian 패키지(각 패키지 라이선스, `/usr/share/doc/*/copyright`).
추가 OS 패키지: `libxrender1`, `libxext6` (MIT/X11).

Python 패키지 (`requirements.lock`, 이미지에서 `pip-licenses`와 패키지 메타데이터로 추출):

| 패키지 | 버전 | 라이선스 |
|---|---|---|
| torch | 2.0.1 | BSD-3-Clause |
| triton | 2.0.0 | MIT |
| numpy | 1.24.3 | BSD-3-Clause |
| pandas | 2.1.3 | BSD-3-Clause |
| rdkit | 2023.9.1 | BSD-3-Clause |
| fastapi | 0.104.1 | MIT |
| starlette | 0.27.0 | BSD-3-Clause |
| pydantic / pydantic-core | 2.5.0 / 2.14.1 | MIT |
| uvicorn | 0.24.0 | BSD-3-Clause |
| tqdm | 4.66.1 | MIT 및 MPL-2.0 |
| anyio, annotated-types, exceptiongroup, filelock, h11, pytz, six | — | MIT |
| sniffio | 1.3.1 | Apache-2.0 또는 MIT |
| python-dateutil | 2.9.0.post0 | Apache-2.0 및 BSD-3-Clause |
| jinja2, markupsafe, click, idna, networkx, sympy, mpmath | — | BSD |
| packaging | 26.3 | Apache-2.0 또는 BSD-2-Clause |
| pillow | 12.3.0 | MIT-CMU (HPND) |
| typing-extensions | 4.16.0 | PSF-2.0 |
| tzdata | 2026.5 | Apache-2.0 |
| cmake, lit (triton 의존성) | 4.4.4, 23.1.2 | Apache-2.0 / BSD |
| nvidia-cublas, cuda-cupti, cuda-nvrtc, cuda-runtime, cudnn, cufft, curand, cusolver, cusparse, nccl, nvtx (`-cu11`) | 11.x / 8.5 | NVIDIA 소프트웨어 라이선스(독점) — PyTorch 공식 휠이 의존하는 CUDA 런타임 재배포 구성요소 |

**확인 필요 사항:** NVIDIA CUDA·cuDNN 라이브러리는 오픈소스가 아니며 NVIDIA
라이선스 조건에 따라 재배포된다. PyTorch 공식 배포 휠과 같은 방식으로 포함했다.
배포처에서 독점 구성요소 포함을 제한하면 별도 협의가 필요하다.

## 4. 데이터

학습 데이터는 저장소와 이미지에 들어 있지 않다(`docs/reference_data.md`).

| 데이터 | 이용 조건 | 판단 |
|---|---|---|
| Tox21 (NIH NCATS/EPA/NTP) | 미국 연방정부 생산 데이터 | 학습 이용 가능, 공공 영역으로 간주 |
| ToxCast (US EPA) | 미국 연방정부 생산 데이터 | 학습 이용 가능, 공공 영역으로 간주 |
| ClinTox (Gayvert et al. 2016, MoleculeNet 재배포) | 명시적 데이터 라이선스 표기를 찾지 못함 | 학술 공개 데이터로 학습에 이용. **데이터 자체를 재배포하지 않음.** 상업적 이용 시 원저자 확인 권장 |
| 시험 입력 SMILES (`tests/`) | 위 데이터에서 고른 화학구조(라벨 없음) | 화학구조 표기 자체는 저작물성이 낮음 |

## 5. 기타

* 상표: "Tox21", "ToxCast", "MoleculeNet"은 출처 표기 목적으로만 사용했다.
* 본 확인서는 2026-10-06 기준 각 구성요소 메타데이터와 원 저장소 LICENSE 파일에
  근거한다. 법률 자문이 아니다.
