# 설치·배포 정의서 — ToxKG-GPS Toxicity Predictor 1.0.0

## 1. 배포 구성물

| 구성물 | 위치 | 설명 |
|---|---|---|
| 컨테이너 이미지 | `pzkeung/bio-synergy-platform:toxkg-gps-1.0.0` (별칭 `:toxkg-gps`) | linux/amd64, 비루트(UID 10001 `app`), 8.9 GB. 코드·의존성·가중치 포함, 실행 중 네트워크 불필요 |
| 이미지 정의 | `/Dockerfile` | 학습 이미지(`toxkg-train`)와 같은 베이스(CUDA 11.8 + cuDNN 8, Ubuntu 22.04), digest·apt 버전 고정 |
| 의존성 정의 | `/requirements.in` | 직접 의존성: torch 2.1.0+cu118, torch_geometric 2.5.3, torch-scatter·torch-sparse·torch-cluster·torch-spline-conv(pt21cu118), rdkit 2026.3.2, numpy 1.26.4, fastapi, pydantic, uvicorn |
| 버전 제약 | `/constraints.txt` | 학습 이미지의 `pip freeze`(학습 전용 시각화 패키지 제외) — 하위 의존성까지 학습 환경과 같은 버전 |
| 의존성 잠금 | `/requirements.lock` | `pip-compile --generate-hashes` 결과. 50개 패키지의 버전과 SHA-256 고정 |
| 배포 매니페스트 | `/docker-compose.yml` | batch 작업(`network_mode: none`) + 선택적 serve 서비스(루프백 바인딩) |
| 가중치 | `/models/gps_trainset_seed0.pt`(git 제외) + `_config.json` + `SHA256SUMS` | 빌드 시 `/opt/app/models`로 복사, 시작 시 체크섬 검증 |

## 2. 빌드 (인터넷이 되는 빌드 서버)

```bash
git clone -b toxkg-gps https://github.com/pzkeung/DrugDevPlatform.git
cd DrugDevPlatform
# models/gps_trainset_seed0.pt 를 배치한 뒤 검증 (저장소에는 체크섬만 있음)
(cd models && sha256sum -c SHA256SUMS)

docker buildx build --platform linux/amd64 \
  -t pzkeung/bio-synergy-platform:toxkg-gps-1.0.0 \
  -t pzkeung/bio-synergy-platform:toxkg-gps --load .
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

## 3. 레지스트리 등록

```bash
docker login -u pzkeung
docker push pzkeung/bio-synergy-platform:toxkg-gps-1.0.0
docker push pzkeung/bio-synergy-platform:toxkg-gps
docker buildx imagetools inspect pzkeung/bio-synergy-platform:toxkg-gps-1.0.0   # digest 확인
```

push 후 digest를 `docs/release_info.md`와 `tool.yaml`의 `image.digest`에 기록한다.
`latest` 태그는 쓰지 않는다.

## 4. 오프라인 설치

```bash
# 인터넷 PC
docker pull pzkeung/bio-synergy-platform:toxkg-gps-1.0.0
docker save pzkeung/bio-synergy-platform:toxkg-gps-1.0.0 | gzip > toxkg-gps-1.0.0.tar.gz
sha256sum toxkg-gps-1.0.0.tar.gz > toxkg-gps-1.0.0.tar.gz.sha256

# 분석 서버 (오프라인)
sha256sum -c toxkg-gps-1.0.0.tar.gz.sha256
docker load < toxkg-gps-1.0.0.tar.gz
docker run --rm --network none pzkeung/bio-synergy-platform:toxkg-gps-1.0.0 version
```

GPU는 선택 사항이다. GPU를 쓰려면 NVIDIA 드라이버(CUDA 11.8 지원, 520 이상)와 NVIDIA
Container Toolkit이 필요하다. GPU 없이도 약 79 분자/초로 처리한다(GPU 약 366 분자/초).
GPU가 없는 호스트에서 매니페스트를 쓸 때는 `docker-compose.yml`의 GPU `reservations`
블록을 지운다.

## 5. 실행

```bash
mkdir -p input output && chmod 777 output
cp molecules.csv input/

# 단독 실행 (GPU 없으면 --gpus all 생략)
docker run --rm --gpus all --network none \
  -v "$PWD/input:/data/input:ro" -v "$PWD/output:/data/output" \
  -e INPUT_PATH=/data/input/molecules.csv \
  pzkeung/bio-synergy-platform:toxkg-gps-1.0.0

# 매니페스트 사용
INPUT_FILE=molecules.csv docker compose run --rm toxkggps-batch
docker compose --profile serve up -d toxkggps-serve     # 선택: HTTP API
```

## 6. 보안·네트워크

* 비루트 사용자로 실행되며 실행 중 외부로 접속하지 않는다. batch 모드는 `--network none`
  (매니페스트 `network_mode: none`)으로 네트워크 인터페이스를 없앤다. 자체 시험은 모두
  `--network none`으로 수행했다(serve 사례는 컨테이너 내부 루프백 호출).
* serve 모드는 포트 노출 때문에 네트워크가 필요하다. 매니페스트는 127.0.0.1에만
  바인딩한다. 인증 기능이 없으므로 외부 노출 시 상위 게이트웨이에서 접근을 통제한다.
* `PIP_NO_INDEX=1`로 실행 중 패키지 내려받기를 막는다.
* 시작할 때 가중치와 설정 파일의 SHA-256을 `models/SHA256SUMS`와 비교하고, 다르면
  `E-MODEL-002`로 종료한다.

## 7. 설치 확인

```bash
docker run --rm --network none pzkeung/bio-synergy-platform:toxkg-gps-1.0.0 version
# → tox-toxkggps 1.0.0
python3 tests/run_tests.py --image pzkeung/bio-synergy-platform:toxkg-gps-1.0.0
# → 18/18 passed (골든 7건 + 보조 11건)
```
