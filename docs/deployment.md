# 설치·배포 정의서 — ToxKG-GPS Toxicity Predictor 1.0.0

## 1. 배포 구성물

| 구성물 | 위치 | 설명 |
|---|---|---|
| 컨테이너 이미지 | `cbibioinfolab/toxicity-prediction:toxkg-gps-1.0.0` | linux/amd64, 비루트(UID 10001 `app`), 8.9 GB. 코드·의존성·가중치 포함, 실행 중 네트워크 불필요 |
| 이미지 정의 | `/Dockerfile` | 학습 이미지(`toxkg-train`)와 같은 베이스(CUDA 11.8 + cuDNN 8, Ubuntu 22.04), digest·apt 버전 고정 |
| 의존성 정의 | `/requirements.in` | 직접 의존성: torch 2.1.0+cu118, torch_geometric 2.5.3, torch-scatter·torch-sparse·torch-cluster·torch-spline-conv(pt21cu118), rdkit 2026.3.2, numpy 1.26.4, fastapi, pydantic, uvicorn |
| 버전 제약 | `/constraints.txt` | 학습 이미지의 `pip freeze`(학습 전용 시각화 패키지 제외) — 하위 의존성까지 학습 환경과 같은 버전 |
| 의존성 잠금 | `/requirements.lock` | `pip-compile --generate-hashes` 결과. 50개 패키지의 버전과 SHA-256 고정 |
| 배포 매니페스트 | `/docker-compose.yml` | batch 작업(`network_mode: none`) + serve 서비스(작업 API, 루프백 바인딩) |
| 가중치 | `/models/toxkggps_pretrained.pt`(git 제외) + `toxkggps_pretrained_config.json` + `SHA256SUMS` | 빌드 시 `/opt/app/models`로 복사, 시작 시 체크섬 검증 |

### 1.1 가중치 파일

`.pt`는 소스 저장소에 넣지 않는다. 빌드 전에 아래 경로에 배치한다. 배포된 이미지에는
포함되어 있다.

| 파일 | 크기 (bytes) | git | 내용 |
|---|--:|---|---|
| `models/toxkggps_pretrained.pt` | 2,540,928 | 제외 | `GPSBench`의 PyTorch `state_dict`(매개변수 630,263개). trainset holdout **seed 0** 실행(5개 seed 중 val macro AUROC 최고, 학습에 쓰지 않은 test에서도 최고) |
| `models/toxkggps_pretrained_config.json` | 17,250 | 포함 | `in_dim` 12, `hidden` 128, `heads` 4, `layers` 3, `dropout` 0.1, `tasks`(631개 이름, 출력 순서) |

구조(`GPSBench`): 노드 투영 12 → 128, 결합 투영 6 → 128; GPS 블록 3개(각각 GINEConv 국소
메시지 전달(2층 MLP) + LayerNorm, 분자별 다중 헤드 자기 주의(4 헤드), 피드포워드
128 → 256 → 128(GELU) + LayerNorm); 전역 평균 풀링; LayerNorm + 선형 출력 → 631 로짓.
분자 그래프만 쓰며 지식그래프 데이터는 쓰지 않는다.

## 2. 빌드 (인터넷이 되는 빌드 서버)

```bash
git clone -b toxkg-gps https://github.com/cbi-bioinfo/all-in-one-platform.git
cd all-in-one-platform
# 1.1절 models/toxkggps_pretrained.pt 를 배치한 뒤 검증
(cd models && sha256sum -c SHA256SUMS)

docker buildx build --platform linux/amd64 \
  -t cbibioinfolab/toxicity-prediction:toxkg-gps-1.0.0 --load .
```

빌드 과정과 재현 조건:

1. 베이스 `nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04@sha256:85fb7ac694079fff1061a0140fd5b5a641997880e12112d92589c3bbb1e8b7ca`
2. apt 패키지 버전 고정: `python3.10=3.10.12-1~22.04.18`, `python3-pip=22.0.2+dfsg-1ubuntu0.7`,
   `libxrender1=1:0.9.10-1build4`, `libxext6=2:1.3.4-1build1`
3. `pip install --require-hashes --no-deps -r requirements.lock` — torch는 PyTorch cu118
   인덱스(`download.pytorch.org/whl/cu118`), PyG 확장은 PyG 휠 저장소
   (`data.pyg.org/whl/torch-2.1.0+cu118.html`), 나머지는 PyPI에서 받는다. 빌드 서버는 이
   세 주소에 접근할 수 있어야 한다. 해시가 다른 파일은 설치되지 않는다.
4. 비루트 사용자 `app`(UID/GID 10001) 생성, 소스·가중치 복사, `PIP_NO_INDEX=1` 설정.
   설치된 패키지 파일은 수정하지 않는다.

의존성을 바꿀 때만 잠금 파일을 다시 만든다:

```bash
pip-compile --generate-hashes --allow-unsafe --strip-extras \
  -c constraints.txt -o requirements.lock requirements.in
```

## 3. 오프라인 설치

```bash
# 인터넷 PC
docker pull cbibioinfolab/toxicity-prediction:toxkg-gps-1.0.0
docker save cbibioinfolab/toxicity-prediction:toxkg-gps-1.0.0 | gzip > toxkg-gps-1.0.0.tar.gz
sha256sum toxkg-gps-1.0.0.tar.gz > toxkg-gps-1.0.0.tar.gz.sha256

# 분석 서버 (오프라인)
sha256sum -c toxkg-gps-1.0.0.tar.gz.sha256
docker load < toxkg-gps-1.0.0.tar.gz
docker run --rm --network none cbibioinfolab/toxicity-prediction:toxkg-gps-1.0.0 version
```

GPU는 선택 사항이다. GPU를 쓰려면 NVIDIA 드라이버(CUDA 11.8 지원, 520 이상)와 NVIDIA
Container Toolkit이 필요하다. GPU 없이도 약 60–80 분자/초로 처리한다(GPU 약 350 분자/초, 서버 부하에 따라 다름).
GPU가 없는 호스트에서 매니페스트를 쓸 때는 `docker-compose.yml`의 GPU `reservations`
블록을 지운다.

## 4. 실행

```bash
mkdir -p input output && chmod 777 output
cp molecules.csv input/

# 단독 실행 (GPU 없으면 --gpus all 생략)
docker run --rm --gpus all --network none \
  -v "$PWD/input:/data/input:ro" -v "$PWD/output:/data/output" \
  -e INPUT_PATH=/data/input/molecules.csv \
  cbibioinfolab/toxicity-prediction:toxkg-gps-1.0.0

# 매니페스트 사용
INPUT_FILE=molecules.csv docker compose run --rm toxkggps-batch
docker compose --profile serve up -d toxkggps-serve     # HTTP 작업 API (사용법: user_manual 5절)
```

## 5. 보안·네트워크

* 비루트 사용자로 실행되며 실행 중 외부로 접속하지 않는다. batch 모드는 `--network none`
  (매니페스트 `network_mode: none`)으로 네트워크 인터페이스를 없앤다. 자체 시험은 모두
  `--network none`으로 수행했다(serve 사례는 컨테이너 내부 루프백 호출).
* serve 모드는 포트 노출 때문에 네트워크가 필요하다. 매니페스트는 127.0.0.1에만
  바인딩한다. 인증 기능이 없으므로 외부 노출 시 상위 게이트웨이에서 접근을 통제한다.
* `PIP_NO_INDEX=1`로 실행 중 패키지 내려받기를 막는다.
* 시작할 때 가중치와 설정 파일의 SHA-256을 `models/SHA256SUMS`와 비교하고, 다르면
  `E-MODEL-002`로 종료한다.

## 6. 설치 확인

```bash
docker run --rm --network none cbibioinfolab/toxicity-prediction:toxkg-gps-1.0.0 version
# → tox-toxkggps 1.0.0
python3 tests/run_tests.py --image cbibioinfolab/toxicity-prediction:toxkg-gps-1.0.0
# → 24/24 passed (골든 7건 + 보조 17건)
```
