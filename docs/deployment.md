# 설치·배포 정의서 — GROVER Toxicity Predictor 1.0.0

## 1. 배포 구성물

| 구성물 | 위치 | 설명 |
|---|---|---|
| 컨테이너 이미지 | `pzkeung/bio-synergy-platform:grover-1.0.0` (별칭 `:grover`) | linux/amd64, 9.9 GB, 비루트(UID 10001), 코드·의존성·체크포인트 포함 |
| 이미지 정의 | `/Dockerfile` | 학습 이미지와 같은 베이스(CUDA 11.8 + cuDNN 8, Ubuntu 22.04), digest·apt 버전 고정 |
| 직접 의존성 | `/requirements.in` | torch 2.2.1+cu118, rdkit 2026.3.6, numpy, scipy, scikit-learn, tqdm(업스트림 코드가 import), fastapi, pydantic, uvicorn |
| 버전 제약 | `/constraints.txt` | 학습 이미지(`grover-train`)의 `pip freeze` |
| 잠금 파일 | `/requirements.lock` | `pip-compile --generate-hashes`, 42개 패키지 버전·해시 고정 |
| 배포 매니페스트 | `/docker-compose.yml` | batch(`network_mode: none`) + serve(루프백) |
| 가중치 | `/models/*.pt`(git 제외) + config + `SHA256SUMS` | 빌드 시 `/opt/app/models`로 복사, 시작 시 검증 |

## 2. 빌드 (인터넷 가능한 빌드 서버)

```bash
git clone -b grover https://github.com/pzkeung/DrugDevPlatform.git && cd DrugDevPlatform
# models/grover_trainset_seed2.pt 배치 후
(cd models && sha256sum -c SHA256SUMS)
docker buildx build --platform linux/amd64 \
  -t pzkeung/bio-synergy-platform:grover-1.0.0 -t pzkeung/bio-synergy-platform:grover --load .
```

1. 베이스 `nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04@sha256:85fb7ac6…b7ca`
2. apt 고정 설치: `python3.10=3.10.12-1~22.04.18`, `python3-pip=22.0.2+dfsg-1ubuntu0.7`,
   `libxrender1=1:0.9.10-1build4`, `libxext6=2:1.3.4-1build1`
3. `pip install --require-hashes --no-deps -r requirements.lock` — torch는 PyTorch cu118
   인덱스, 나머지는 PyPI. 해시가 다르면 설치되지 않는다.
4. 비루트 사용자 생성, `src/`·`models/`·`tool.yaml`·`README.md`·`LICENSE` 복사, `PIP_NO_INDEX=1`.

의존성 변경 시: `pip-compile --generate-hashes --allow-unsafe --strip-extras -c constraints.txt -o requirements.lock requirements.in`

## 3. 레지스트리 등록

```bash
docker push pzkeung/bio-synergy-platform:grover-1.0.0
docker push pzkeung/bio-synergy-platform:grover
docker buildx imagetools inspect pzkeung/bio-synergy-platform:grover-1.0.0
```

digest는 `docs/release_info.md`와 `tool.yaml`(`image.digest`)에 기록한다. `latest`는 쓰지 않는다.

## 4. 오프라인 설치

```bash
docker save pzkeung/bio-synergy-platform:grover-1.0.0 | gzip > grover-1.0.0.tar.gz
sha256sum grover-1.0.0.tar.gz > grover-1.0.0.tar.gz.sha256
# 분석 서버
sha256sum -c grover-1.0.0.tar.gz.sha256 && docker load < grover-1.0.0.tar.gz
docker run --rm --network none pzkeung/bio-synergy-platform:grover-1.0.0 version
```

GPU 사용 시 NVIDIA 드라이버(520 이상)와 NVIDIA Container Toolkit 필요. GPU가 없으면 CPU로
동작하지만 약 20배 느리다(1.7 분자/초).

## 5. 실행

```bash
mkdir -p input output && chmod 777 output && cp molecules.csv input/
docker run --rm --gpus all --network none \
  -v "$PWD/input:/data/input:ro" -v "$PWD/output:/data/output" \
  -e INPUT_PATH=/data/input/molecules.csv pzkeung/bio-synergy-platform:grover-1.0.0
# 또는
INPUT_FILE=molecules.csv docker compose run --rm grover-batch
docker compose --profile serve up -d grover-serve
```

## 6. 보안·네트워크

* 비루트 실행, 실행 중 외부 접속 없음. batch는 `--network none`. 자체 시험은 모두 `--network none`.
* serve는 루프백에만 바인딩. 인증이 없으므로 외부 노출 시 상위 게이트웨이에서 통제.
* 시작 시 체크포인트·설정 SHA-256 검증, 불일치 시 `E-MODEL-002`.

## 7. 설치 확인

```bash
python3 tests/run_tests.py --image pzkeung/bio-synergy-platform:grover-1.0.0   # 20/20
```
