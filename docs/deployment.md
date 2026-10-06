# 설치·배포 정의서 — GROVER Toxicity Predictor 1.0.0

## 1. 배포 구성물

| 구성물 | 위치 | 설명 |
|---|---|---|
| 컨테이너 이미지 | `cbibioinfolab/toxicity-prediction:grover-1.0.0` | linux/amd64, 9.9 GB, 비루트(UID 10001), 코드·의존성·체크포인트 포함 |
| 이미지 정의 | `/Dockerfile` | 학습 이미지와 같은 베이스(CUDA 11.8 + cuDNN 8, Ubuntu 22.04), digest·apt 버전 고정 |
| 직접 의존성 | `/requirements.in` | torch 2.2.1+cu118, rdkit 2026.3.6, numpy, scipy, scikit-learn, tqdm(업스트림 코드가 import), fastapi, pydantic, uvicorn |
| 버전 제약 | `/constraints.txt` | 학습 이미지(`grover-train`)의 `pip freeze` |
| 잠금 파일 | `/requirements.lock` | `pip-compile --generate-hashes`, 42개 패키지 버전·해시 고정 |
| 배포 매니페스트 | `/docker-compose.yml` | batch(`network_mode: none`) + serve(작업 API, 루프백) |
| 가중치 | `/models/grover_pretrained.pt`(git 제외) + `grover_pretrained_config.json` + `SHA256SUMS` | 빌드 시 `/opt/app/models`로 복사, 시작 시 검증 |

### 1.1 가중치 파일

`.pt`는 용량 때문에 소스 저장소에 넣지 않는다. 빌드 전에 아래 경로에 배치한다.
배포된 이미지에는 포함되어 있다.

| 파일 | 크기 (bytes) | git | 내용 |
|---|--:|---|---|
| `models/grover_pretrained.pt` | 195,924,310 | 제외 | GROVER 미세조정 체크포인트: `{'args', 'state_dict', 'data_scaler': None, 'features_scaler': None}`, 매개변수 48,963,696개. 업스트림 GROVER-base(`grover_base.pt`)에서 trainset holdout **seed 2** 학습 분할로 미세조정 |
| `models/grover_pretrained_config.json` | 17,538 | 포함 | 태스크 목록(631개, 출력 순서)과 구조 요약 |

사전학습 인코더 가중치가 체크포인트에 들어 있으므로 추론에 `grover_base.pt`는 필요 없고
배포하지 않는다. 구조(체크포인트 `args` 기준): `dualtrans` 백본, hidden 800, 메시지 전달
깊이 6, 4-헤드 다중 헤드 주의 블록 1개, PReLU, 원자·결합 두 관점 임베딩(`both`), 읽기 헤드
2개(평균 풀링 → FFN 800 → 200 → 631), sigmoid 후 두 출력 평균.

## 2. 빌드 (인터넷 가능한 빌드 서버)

```bash
git clone -b grover https://github.com/cbi-bioinfo/all-in-one-platform.git && cd all-in-one-platform
# 1.1절 models/grover_pretrained.pt 배치 후
(cd models && sha256sum -c SHA256SUMS)
docker buildx build --platform linux/amd64 \
  -t cbibioinfolab/toxicity-prediction:grover-1.0.0 --load .
```

1. 베이스 `nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04@sha256:85fb7ac6…b7ca`
2. apt 고정 설치: `python3.10=3.10.12-1~22.04.18`, `python3-pip=22.0.2+dfsg-1ubuntu0.7`,
   `libxrender1=1:0.9.10-1build4`, `libxext6=2:1.3.4-1build1`
3. `pip install --require-hashes --no-deps -r requirements.lock` — torch는 PyTorch cu118
   인덱스, 나머지는 PyPI. 해시가 다르면 설치되지 않는다.
4. 비루트 사용자 생성, `src/`·`models/`·`tool.yaml`·`README.md`·`LICENSE` 복사, `PIP_NO_INDEX=1`.

의존성 변경 시: `pip-compile --generate-hashes --allow-unsafe --strip-extras -c constraints.txt -o requirements.lock requirements.in`

## 3. 오프라인 설치

```bash
docker save cbibioinfolab/toxicity-prediction:grover-1.0.0 | gzip > grover-1.0.0.tar.gz
sha256sum grover-1.0.0.tar.gz > grover-1.0.0.tar.gz.sha256
# 분석 서버
sha256sum -c grover-1.0.0.tar.gz.sha256 && docker load < grover-1.0.0.tar.gz
docker run --rm --network none cbibioinfolab/toxicity-prediction:grover-1.0.0 version
```

GPU 사용 시 NVIDIA 드라이버(520 이상)와 NVIDIA Container Toolkit 필요. GPU가 없으면 CPU로
동작하지만 약 20–30배 느리다(1.0–1.7 분자/초, 서버 부하에 따라 다름).

## 4. 실행

```bash
mkdir -p input output && chmod 777 output && cp molecules.csv input/
docker run --rm --gpus all --network none \
  -v "$PWD/input:/data/input:ro" -v "$PWD/output:/data/output" \
  -e INPUT_PATH=/data/input/molecules.csv cbibioinfolab/toxicity-prediction:grover-1.0.0
# 또는
INPUT_FILE=molecules.csv docker compose run --rm grover-batch
docker compose --profile serve up -d grover-serve     # HTTP 작업 API (사용법: user_manual 5절)
```

## 5. 보안·네트워크

* 비루트 실행, 실행 중 외부 접속 없음. batch는 `--network none`. 자체 시험은 모두 `--network none`.
* serve는 루프백에만 바인딩. 인증이 없으므로 외부 노출 시 상위 게이트웨이에서 통제.
* 시작 시 체크포인트·설정 SHA-256 검증, 불일치 시 `E-MODEL-002`.

## 6. 설치 확인

```bash
python3 tests/run_tests.py --image cbibioinfolab/toxicity-prediction:grover-1.0.0   # 26/26 (골든 7건 + 보조 19건)
```
