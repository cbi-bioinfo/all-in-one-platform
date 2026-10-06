# 설치·배포 정의서 — Chemprop Toxicity Predictor 1.0.0

## 1. 배포 구성물

| 구성물 | 위치 | 설명 |
|---|---|---|
| 컨테이너 이미지 | `pzkeung/bio-synergy-platform:chemprop-1.0.0` (별칭 `:chemprop`) | linux/amd64, 비루트(UID 10001 `app`), 9.2 GB. 코드·의존성·가중치 포함, 실행 중 네트워크 불필요 |
| 이미지 정의 | `/Dockerfile` | 학습 이미지와 같은 베이스(CUDA 12.6 + cuDNN, Ubuntu 24.04, Python 3.12), digest·apt 버전 고정 |
| 모델 코드 | `/src/chemprop` | chemprop 2.3.1 소스(MIT), 학습 이미지에 설치된 것과 같은 사본. `PYTHONPATH`로 import |
| 의존성 정의 | `/requirements.in` | torch 2.6.0+cu126, rdkit 2026.3.6, chemprop의 선언 의존성, fastapi·pydantic·uvicorn |
| 버전 제약 | `/constraints.txt` | 학습 이미지(`chemprop-train`)의 `pip freeze` — 학습 환경 패키지 전부 같은 버전으로 고정됨을 확인 |
| 의존성 잠금 | `/requirements.lock` | `pip-compile --generate-hashes` 결과. 79개 패키지의 버전과 SHA-256 고정 |
| 배포 매니페스트 | `/docker-compose.yml` | batch 작업(`network_mode: none`) + 선택적 serve 서비스(루프백 바인딩) |
| 가중치 | `/models/*.pt`(git 제외) + 설정 JSON + `/models/SHA256SUMS` | 빌드 시 `/opt/app/models`로 복사, 시작 시 체크섬 검증 |

## 2. 빌드 (인터넷이 되는 빌드 서버)

```bash
git clone -b chemprop https://github.com/pzkeung/DrugDevPlatform.git
cd DrugDevPlatform
# models/chemprop_trainset_seed0.pt를 배치한 뒤 검증 (저장소에는 체크섬만 있음)
(cd models && sha256sum -c SHA256SUMS)

docker buildx build --platform linux/amd64 \
  -t pzkeung/bio-synergy-platform:chemprop-1.0.0 \
  -t pzkeung/bio-synergy-platform:chemprop --load .
```

빌드 과정과 재현 조건:

1. 베이스 `nvidia/cuda:12.6.3-cudnn-runtime-ubuntu24.04@sha256:8aef630a54bc5c5146ae5ce68e6af5caa3df0fb690bb91544175c91f307e4356`
2. apt 패키지 버전 고정 설치: `python3=3.12.3-0ubuntu2.1`, `python3-pip=24.0+dfsg-1ubuntu1.3`,
   `libxrender1=1:0.9.10-1.1build1`, `libxext6=2:1.3.4-1build2`,
   `libglib2.0-0t64=2.80.0-6ubuntu3.9`, `libgomp1=14.2.0-4ubuntu2~24.04.1`
3. `pip install --require-hashes --no-deps -r requirements.lock` — torch는 PyTorch cu126
   인덱스(`download.pytorch.org/whl/cu126`), 나머지는 PyPI에서 받는다. Ubuntu 24.04 시스템
   Python에 설치하므로 `PIP_BREAK_SYSTEM_PACKAGES=1`을 쓴다(학습 이미지와 같음).
4. Ubuntu 24.04 기본 사용자 `ubuntu`(UID 1000)를 지우고 비루트 사용자 `app`(UID/GID 10001) 생성.
5. 소스·가중치·`LICENSE` 복사, 실행 중 `PIP_NO_INDEX=1`.

의존성을 바꿀 때만 잠금 파일을 다시 만든다(CUDA 휠 해시 계산에 수 GB를 내려받으므로
여유 디스크가 필요하다):

```bash
pip-compile --generate-hashes --allow-unsafe --strip-extras \
  -c constraints.txt -o requirements.lock requirements.in
```

## 3. 오프라인 설치

```bash
# 인터넷 PC
docker pull pzkeung/bio-synergy-platform:chemprop-1.0.0
docker save pzkeung/bio-synergy-platform:chemprop-1.0.0 | gzip > chemprop-1.0.0.tar.gz
sha256sum chemprop-1.0.0.tar.gz > chemprop-1.0.0.tar.gz.sha256

# 분석 서버 (오프라인)
sha256sum -c chemprop-1.0.0.tar.gz.sha256
docker load < chemprop-1.0.0.tar.gz
docker run --rm --network none pzkeung/bio-synergy-platform:chemprop-1.0.0 version
```

GPU를 쓰려면 호스트에 NVIDIA 드라이버(525 이상, CUDA 12 호환)와 NVIDIA Container Toolkit이
있어야 한다. CUDA 런타임은 이미지에 들어 있다. 이 모델은 CPU에서도 GPU와 비슷한 속도로
동작하므로(506분자 실측 GPU 약 249 / CPU 약 237 분자/초) GPU 없는 서버에도 배포할 수 있다.

## 4. 실행

```bash
mkdir -p input output && chmod 777 output
cp molecules.csv input/

# 단독 실행
docker run --rm --gpus all --network none \
  -v "$PWD/input:/data/input:ro" -v "$PWD/output:/data/output" \
  -e INPUT_PATH=/data/input/molecules.csv \
  pzkeung/bio-synergy-platform:chemprop-1.0.0

# 매니페스트 사용
INPUT_FILE=molecules.csv docker compose run --rm chemprop-batch
docker compose --profile serve up -d chemprop-serve     # 선택: HTTP API
```

## 5. 보안·네트워크

* 비루트 사용자로 실행되며 실행 중 외부로 접속하지 않는다. batch 모드는 `--network none`
  (매니페스트 `network_mode: none`)으로 네트워크 인터페이스를 없앤다. 자체 시험은 모두
  `--network none`으로 수행했다(serve 사례는 컨테이너 내부 루프백 호출).
* serve 모드는 포트 노출 때문에 네트워크가 필요하다. 매니페스트는 127.0.0.1에만
  바인딩한다. 인증 기능이 없으므로 외부 노출 시 상위 게이트웨이에서 접근을 통제한다.
* `PIP_NO_INDEX=1`로 실행 중 패키지 내려받기를 막는다.
* 시작할 때 `models/SHA256SUMS`의 체크포인트·설정 파일을 검증하고, 다르면 `E-MODEL-002`로
  종료한다.

## 6. 설치 확인

```bash
docker run --rm --network none pzkeung/bio-synergy-platform:chemprop-1.0.0 version
# → bsp-tox-chemprop 1.0.0
python3 tests/run_tests.py --image pzkeung/bio-synergy-platform:chemprop-1.0.0
# → 19/19 passed (골든 7건 + 보조 12건)
```
