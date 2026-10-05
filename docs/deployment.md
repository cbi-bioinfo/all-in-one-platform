# 설치·배포 정의서 — SE-MTDNN Toxicity Predictor 1.0.0

## 1. 배포 구성물

| 구성물 | 위치 | 설명 |
|---|---|---|
| 컨테이너 이미지 | `pzkeung/bio-synergy-platform:mtdnn-1.0.0` (별칭 `:mtdnn`) | linux/amd64, 비루트(UID 10001), 가중치·의존성 포함, 실행 중 네트워크 불필요 |
| 이미지 정의 | `/Dockerfile` | 베이스 이미지 digest 고정, 해시 검증 설치(`--require-hashes`) |
| 의존성 잠금 | `/requirements.lock` (`/requirements.in`에서 `pip-compile --generate-hashes`로 생성) | 전체 의존성 40여 종의 버전·SHA-256 고정 |
| 배포 매니페스트 | `/docker-compose.yml` | batch 작업(`network_mode: none`) + 선택적 serve 서비스 |
| 가중치 | `/models/` + `/models/SHA256SUMS` | 이미지 빌드 시 `/opt/app/models`로 복사, 시작 시 체크섬 검증 |

## 2. 빌드 (인터넷이 되는 빌드 서버)

```bash
git clone -b mtdnn https://github.com/pzkeung/DrugDevPlatform.git
cd DrugDevPlatform
# 가중치 파일을 models/에 배치한 뒤 검증 (저장소에는 체크섬만 있음)
(cd models && sha256sum -c SHA256SUMS)

docker buildx build --platform linux/amd64 \
  -t pzkeung/bio-synergy-platform:mtdnn-1.0.0 \
  -t pzkeung/bio-synergy-platform:mtdnn --load .
```

재현 빌드 조건:
* 베이스 이미지 `python:3.10-slim@sha256:c1aaf3d03e14944a039a1647e0b3f6f34c6bee517bac6ff380215ee099c4e808`
* `pip install --require-hashes --no-deps -r requirements.lock` — 잠금 파일에
  없는 패키지나 해시가 다른 파일은 설치되지 않는다.
* 잠금 파일 재생성(의존성 변경 시에만):
  `pip-compile --generate-hashes --allow-unsafe --strip-extras -o requirements.lock requirements.in`

## 3. 레지스트리 등록

```bash
docker login -u pzkeung
docker push pzkeung/bio-synergy-platform:mtdnn-1.0.0
docker push pzkeung/bio-synergy-platform:mtdnn
docker inspect --format '{{index .RepoDigests 0}}' pzkeung/bio-synergy-platform:mtdnn-1.0.0
```

푸시 후 digest를 `docs/release_info.md`와 `tool.yaml`의 `image.digest`에 기록한다.
`latest` 태그는 사용하지 않는다.

## 4. 오프라인 설치

```bash
# 인터넷 PC
docker pull pzkeung/bio-synergy-platform:mtdnn-1.0.0
docker save pzkeung/bio-synergy-platform:mtdnn-1.0.0 | gzip > mtdnn-1.0.0.tar.gz
sha256sum mtdnn-1.0.0.tar.gz > mtdnn-1.0.0.tar.gz.sha256

# 분석 서버 (오프라인)
sha256sum -c mtdnn-1.0.0.tar.gz.sha256
docker load < mtdnn-1.0.0.tar.gz
docker image inspect --format '{{.Id}}' pzkeung/bio-synergy-platform:mtdnn-1.0.0
```

GPU 사용 시 호스트에 NVIDIA 드라이버(515 이상)와 NVIDIA Container Toolkit이
설치되어 있어야 한다. CUDA 11.7 런타임은 이미지에 포함되어 있다.

## 5. 실행

```bash
mkdir -p input output && chmod 777 output
cp molecules.csv input/

# 단독 실행
docker run --rm --gpus all --network none \
  -v "$PWD/input:/data/input:ro" -v "$PWD/output:/data/output" \
  -e INPUT_PATH=/data/input/molecules.csv \
  pzkeung/bio-synergy-platform:mtdnn-1.0.0

# 매니페스트 사용
INPUT_FILE=molecules.csv docker compose run --rm mtdnn-batch
docker compose --profile serve up -d mtdnn-serve     # 선택: HTTP API
```

## 6. 보안·네트워크

* 컨테이너는 비루트 사용자로 실행되며 실행 중 외부로 접속하지 않는다.
  batch 모드는 `--network none`(매니페스트 `network_mode: none`)으로 네트워크
  인터페이스 자체를 제거한다. 자체 시험은 모두 `--network none` 상태에서 수행했다.
* serve 모드는 포트 노출이 필요해 네트워크를 쓰지만, 코드가 외부로 접속하지 않으며
  매니페스트는 루프백(127.0.0.1)에만 바인딩한다. 인증 기능이 없으므로 외부 노출 시
  상위 게이트웨이에서 접근 통제를 해야 한다.
* 런타임에 `PIP_NO_INDEX=1`로 패키지 내려받기를 막아 둔다.
* 시작 시 가중치 SHA-256을 검증하고, 다르면 `E-MODEL-002`로 종료한다.

## 7. 설치 확인

```bash
docker run --rm --network none pzkeung/bio-synergy-platform:mtdnn-1.0.0 version
python3 tests/run_tests.py --image pzkeung/bio-synergy-platform:mtdnn-1.0.0   # 15건 전부 PASS
```
