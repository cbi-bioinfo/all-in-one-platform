# 사용자 매뉴얼 — MTDNN Toxicity Predictor 1.0.0

화합물 구조(SMILES 등)를 입력하면 631개 독성 태스크(Tox21 12, ClinTox 2,
ToxCast 617)의 양성 확률을 계산하는 오프라인 배치 분석 도구다(탑재 유형 T2).
인터넷 연결, 로그인, 별도 설치 없이 Docker만으로 실행된다.

## 1. 준비

| 항목 | 요구 사항 |
|---|---|
| OS / 아키텍처 | Linux x86_64 (linux/amd64) |
| Docker | 20.10 이상 |
| GPU (권장) | NVIDIA GPU 1장, VRAM 6 GB 이상, 드라이버 515 이상, NVIDIA Container Toolkit |
| 메모리 | 8 GiB 이상 (권장 12 GiB) |
| 디스크 | 이미지 6.5 GB |

GPU가 없어도 CPU로 실행되지만 약 100배 느리다(0.7 분자/초).

### 1.1 이미지 반입 (오프라인 환경)

인터넷이 되는 PC에서:

```bash
docker pull cbibioinfolab/toxicity-prediction:mtdnn-1.0.0
docker save cbibioinfolab/toxicity-prediction:mtdnn-1.0.0 | gzip > mtdnn-1.0.0.tar.gz
```

분석 서버에서:

```bash
docker load < mtdnn-1.0.0.tar.gz
docker run --rm --network none cbibioinfolab/toxicity-prediction:mtdnn-1.0.0 version
# → tox-mtdnn 1.0.0
```

## 2. 배치 실행 (기본 모드)

```bash
mkdir -p input output
cp molecules.csv input/
chmod 777 output        # 컨테이너는 비루트 사용자(UID 10001)로 실행된다

docker run --rm --gpus all --network none \
  -v "$PWD/input:/data/input:ro" \
  -v "$PWD/output:/data/output" \
  -e INPUT_PATH=/data/input/molecules.csv \
  cbibioinfolab/toxicity-prediction:mtdnn-1.0.0
```

출력 디렉터리 권한을 바꾸기 어렵다면 `--user "$(id -u):$(id -g)"`를 추가해
호스트 사용자로 실행해도 된다.

### 2.1 입력 형식

| 확장자 | 형식 |
|---|---|
| `.csv` | 헤더 행 필수. `smiles`(또는 `canonical_smiles`) 열 필수(대소문자 무관). `id`, `mol_id`, `name`, `compound_id` 중 하나가 있으면 ID로 사용 |
| `.txt` | 한 줄에 `SMILES [ID]` (공백 구분, 빈 줄 무시). 표준 SMILES 목록(`.smi`) 파일은 확장자만 `.txt`로 바꿔 쓴다 |
| `.sdf` | 다중 분자. 분자 이름(첫 줄)을 ID로 사용 |
| `.mol` | 단일 분자. 파일 이름을 ID로 사용 |

파일은 UTF-8이어야 한다. 분자 수 제한은 없다(SMILES 1개당 최대 1,000자).

### 2.2 환경 변수

| 변수 | 기본값 | 설명 |
|---|---|---|
| `INPUT_PATH` | (필수) | 입력 파일 경로 (컨테이너 내부) |
| `OUTPUT_DIR` | `/data/output` | 결과 저장 경로 |
| `OUTPUT_FORMAT` | `csv` | `csv` 또는 `json` |
| `DEVICE` | `auto` | `auto`(GPU 있으면 GPU), `cuda`, `cpu` |
| `CHUNK_SIZE` | `1000` | 체크포인트 저장 단위(분자 수) |
| `RESUME` | `1` | 이전 체크포인트에서 이어서 실행 |
| `MAX_CHUNKS_PER_RUN` | `0` | 1회 실행당 최대 청크 수(0=제한 없음) |
| `CHECKPOINT_DIR` | `$OUTPUT_DIR/.checkpoint` | 체크포인트 저장 경로 |
| `STANDARDIZE` | `0` | `1`이면 염·용매 제거 + 전하 중화 후 예측 (3.4절, `docs/model_card.md` 5절 참고) |
| `SEED` | `42` | 난수 시드 |
| `MAX_SMILES_LENGTH` | `1000` | SMILES 최대 길이 |
| `MODEL_DIR` | `/opt/app/models` | 가중치 디렉터리 (`SHA256SUMS` 포함) |
| `MODEL_PATH` | `$MODEL_DIR/mtdnn_pretrained.pt` | MTDNN 체크포인트 |
| `SE_ENCODER_DIR` | `$MODEL_DIR/se_encoder` | SE 인코더 파일 |
| `VERIFY_CHECKSUM` | `1` | 시작 시 가중치 SHA-256 검증 |
| `JOBS_DIR` | `$OUTPUT_DIR/jobs` | serve 모드 작업 API의 입력·결과·체크포인트 저장 경로 |
| `JOB_MAX_UPLOAD_MB` | `1024` | `POST /jobs` 본문 최대 크기(MB) |
| `MAX_REQUEST_ITEMS` | `100` | `POST /predict` 요청당 최대 분자 수 |
| `LOG_LEVEL` | `INFO` | `DEBUG`/`INFO`/`WARNING`/`ERROR` |

다른 가중치를 쓰려면 디렉터리를 마운트하고 `MODEL_DIR`만 바꾼다
(`-v /path/models:/models:ro -e MODEL_DIR=/models`). 이때 디렉터리에
`SHA256SUMS`가 있어야 한다.

### 2.3 진행률 로그와 수행 시간

로그는 표준 오류(stderr)로 출력된다.

```
INFO mtdnn_tox: tox-mtdnn 1.0.0 — batch run started at 2026-10-06T01:25:00+09:00
INFO mtdnn_tox: Input: /data/input/molecules.csv — 10000 molecules in 10 chunk(s) of 1000
INFO mtdnn_tox: Verifying model checksums ...
INFO mtdnn_tox: Model loaded: 631 tasks, device=cuda
INFO mtdnn_tox: [progress] 1000/10000 (10.0%) chunk 1/10 elapsed=00:00:49 eta=00:02:06 rate=70.1 mol/s
...
INFO mtdnn_tox: Finished at ... — elapsed 00:03:02; 9998 ok, 2 error(s); output: /data/output/predictions.csv
```

시작·종료 시각, 소요 시간, 처리량은 `run_summary.json`에도 기록된다.

### 2.4 중단과 재시작

결과는 `CHUNK_SIZE` 단위로 `CHECKPOINT_DIR`에 저장된다. 작업이 중단되면
**같은 명령을 다시 실행**한다. 완료된 청크는 건너뛰고 로그에
`Resuming: k/n chunk(s) already finished`가 출력된다. 입력 파일이나 설정이
바뀌었으면 체크포인트를 버리고 처음부터 실행한다.

작업을 여러 번에 나눠 돌리려면 `MAX_CHUNKS_PER_RUN`을 지정한다. 지정한 청크
수를 처리하면 종료 코드 5로 멈추고(`run_summary.json`의 `status: partial`),
다시 실행하면 이어서 처리한다.

### 2.5 종료 코드

| 코드 | 의미 |
|---|---|
| 0 | 완료. 분자 단위 오류는 결과 파일의 `status`/`error_code`에 기록 |
| 2 | 입력 오류 (`E-INPUT-*`) — 파일 없음, 형식 오류, smiles 열 없음, 빈 입력 |
| 3 | 모델 오류 (`E-MODEL-*`) — 가중치 누락, 체크섬 불일치 |
| 4 | 시스템·설정 오류 (`E-SYS-*`) |
| 5 | `MAX_CHUNKS_PER_RUN` 도달로 일시 중단 — 같은 명령으로 재시작 |

## 3. 결과 해석

### 3.1 출력 파일

| 파일 | 내용 |
|---|---|
| `predictions.csv` (또는 `.json`) | 입력 순서대로 분자당 1행 |
| `run_summary.json` | `status`, 건수(`n_total`, `n_ok`, `n_error`, `n_with_warnings`), 시작/종료 시각, `elapsed_sec`, 처리량, 장치, 시드, 모델 SHA-256 |

### 3.2 `predictions.csv` 열

| 열 | 설명 |
|---|---|
| `index` | 입력 순서 (0부터) |
| `id` | 입력 ID, 없으면 `mol_<index>` |
| `input_smiles` | 입력 SMILES (SDF/MOL은 RDKit이 변환한 SMILES) |
| `canonical_smiles` | 예측에 실제로 사용한 RDKit canonical SMILES |
| `status` | `ok` 또는 `error` |
| `error_code`, `error_message` | 오류 코드와 설명 (RDKit 원문 메시지 포함) |
| `warnings` | 경고 코드 (`;` 구분) |
| `<태스크>_prob` | 해당 태스크 양성(독성·활성) 확률, 0–1, 소수점 8자리 |
| `<태스크>_label` | `_prob` ≥ 0.5 이면 1, 아니면 0 |

태스크 631개의 열 순서는 모델 출력 순서와 같다(Tox21 12개 → ClinTox 2개 →
ToxCast 617개). 태스크 목록은 출력 헤더나 serve 모드의 `GET /schema`로 확인한다.

### 3.3 확률을 읽는 방법

* 확률은 **해당 분석(assay)에서 양성으로 나올 가능성**이다. Tox21·ToxCast는
  in vitro 분석, ClinTox의 `CT_TOX`는 임상시험 독성 실패, `FDA_APPROVED`는
  FDA 승인 여부(독성이 아님)다.
* 0.5 임계값의 민감도는 약 0.25로 낮다. 양성을 놓치기 쉬우므로 **확률값으로
  순위를 매겨** 상위 화합물을 우선 검토하는 용도가 적합하다.
* 개별 태스크는 학습 양성 수가 적은 경우가 많아 신뢰도가 다르다. 성능과 한계는
  `docs/model_card.md`를 참고한다.

### 3.4 경고 코드

경고가 있어도 예측은 수행된다.

| 코드 | 의미 | 조치 |
|---|---|---|
| `W-STD-001` | 여러 조각(염·용매·혼합물)이 있음 | 학습 데이터도 염을 포함해 학습했으므로 그대로 예측. 모체만 보고 싶으면 `STANDARDIZE=1` |
| `W-STD-002` | 전하를 띤 원자가 있음(이온화 형태) | 위와 같음 |
| `W-STD-003` | `STANDARDIZE=1`로 구조가 바뀜(최대 조각만 남김·중화) | `canonical_smiles`에서 바뀐 구조 확인 |
| `W-ENC-001` | SE 인코더가 SMILES 일부를 인식하지 못함 — `.`, `/`, `\`, 일부 금속 원소는 무시되고 `@` 등은 `<unk>`로 처리 | 입체 표기 유무만으로 확률이 크게 달라질 수 있음. 해석에 주의 |

### 3.5 오류 코드

| 코드 | HTTP | 범위 | 의미 |
|---|---|---|---|
| `E-INPUT-001` | 422 | 작업 | 입력 파일이 없거나 읽을 수 없음(UTF-8 아님 포함) |
| `E-INPUT-002` | 422 | 분자 | RDKit이 SMILES를 해석하지 못함 — 문법 오류(고리 미종결, 괄호 불일치), 원자가 초과(예: 전하 표기 없는 4급 암모늄) 등. RDKit 원문 메시지가 함께 기록됨 |
| `E-INPUT-003` | 413 | 요청 | serve 요청 1건당 분자 수가 `MAX_REQUEST_ITEMS`(100) 초과 |
| `E-INPUT-004` | 422 | 작업 | 지원하지 않는 파일 확장자 |
| `E-INPUT-005` | 422 | 작업 | CSV에 `smiles` 열이 없음 |
| `E-INPUT-006` | 422 | 작업 | 입력에 분자가 없음 |
| `E-INPUT-007` | 422 | 분자 | 빈 SMILES |
| `E-INPUT-008` | 422 | 분자 | SDF/MOL 레코드를 읽을 수 없음 |
| `E-INPUT-009` | 422 | 분자 | `STANDARDIZE=1` 처리 후 남은 분자가 없음 |
| `E-INPUT-010` | 422 | 분자 | SMILES가 `MAX_SMILES_LENGTH`보다 김 |
| `E-INPUT-011` | 422 | 요청 | serve 요청 본문·쿼리가 API 스키마와 맞지 않음 |
| `E-INPUT-012` | 413 | 요청 | `POST /jobs` 본문이 `JOB_MAX_UPLOAD_MB` 초과 |
| `E-JOB-001` | 404 | 요청 | 없는 `job_id` |
| `E-JOB-002` | 409 | 요청 | 작업이 완료되지 않아 결과가 없음(`queued`/`running`/`failed`) |
| `E-MODEL-001` | 503 | 작업 | 가중치·SE 인코더 파일 누락 또는 로드 실패 |
| `E-MODEL-002` | 503 | 작업 | 가중치 SHA-256이 `SHA256SUMS`와 다름 |
| `E-MODEL-003` | 500 | 분자 | SE 인코더가 사용할 수 있는 토큰이 없음 |
| `E-SYS-001` | 500 | 작업 | 출력 디렉터리에 쓸 수 없음 |
| `E-SYS-002` | 500 | 작업 | `DEVICE=cuda`인데 GPU가 보이지 않음 |
| `E-SYS-003` | 500 | 작업 | 예기치 않은 내부 오류 |
| `E-SYS-004` | 400 | 작업 | 환경 변수 값이 잘못됨 |
| `E-SYS-005` | 503 | 요청 | serve 모드에서 모델 로딩 중 (`GET /readyz`가 200이 된 뒤 재시도) |

**분자** 범위 오류는 해당 행만 `status=error`로 표시하고 나머지는 계속 예측한다.
**작업** 범위 오류는 실행을 멈추고 종료 코드 2–4를 반환한다.

### 3.6 raw SMILES 처리 예

| 입력 | 처리 결과 |
|---|---|
| `CCCOc1nn(C(=O)[N-]S(...)...)c(=O)n1C.[Na+]` (나트륨 염) | 그대로 예측, `W-STD-001;W-STD-002;W-ENC-001` |
| `...c1ccc(N(=O)=O)cc1` (니트로기를 전하 분리 없이 표기) | RDKit이 `[N+](=O)[O-]`로 자동 정규화 → 올바른 표기와 같은 예측 |
| `CN(C)(CCOc1ccccc1)Cc1cccs1.I` (4급 암모늄의 `+` 누락) | `E-INPUT-002`: `Explicit valence for atom # 1 N, 4, is greater than permitted` |
| `O=C1C2CC=CCC2C(=O)NSC(Cl)(Cl)Cl` (고리 번호 1 미종결) | `E-INPUT-002`: `SMILES Parse Error: unclosed ring ...` |
| 빈 칸 | `E-INPUT-007` |

## 4. serve 모드 (HTTP API)

명세: `api/openapi.yaml` (OpenAPI 3.0.3).

| 엔드포인트 | 용도 |
|---|---|
| `GET /healthz` | 생존 확인 — 프로세스가 떠 있으면 200 (모델 로딩 중에도) |
| `GET /readyz` | 준비 확인 — 모델 로드가 끝나면 200 `ready`, 로딩 중 503 `loading`, 로드 실패 503 `failed` |
| `GET /info` | 도구 id·버전·모델 SHA-256·장치·임계값·시드 등 설정 |
| `GET /schema` | 입력 형식, 결과 열 정의, 태스크 631개 목록(출력 순서), 오류·경고 코드 |
| `POST /predict` | 소량(1–`MAX_REQUEST_ITEMS`건) 동기 예측 |
| `POST /jobs` | 작업 제출 (T2) — 건수 제한 없음, 백그라운드 실행 |
| `GET /jobs/{job_id}` | 작업 상태·진행률 조회 |
| `GET /jobs/{job_id}/result` | 작업 결과 파일 조회 |

```bash
mkdir -p output && chmod 777 output
docker run -d --name mtdnn --gpus all -p 127.0.0.1:8000:8000 \
  -v "$PWD/output:/data/output" \
  cbibioinfolab/toxicity-prediction:mtdnn-1.0.0 serve
curl -s localhost:8000/healthz    # 바로 200
curl -s localhost:8000/readyz     # 모델 로드(약 35초) 후 200
```

모델은 서버 시작 후 백그라운드에서 읽는다. 로딩 중 `/predict`·`/schema`는
`503 E-SYS-005`를 반환하고, 그 사이 제출한 작업은 대기열에서 로드 완료를 기다린다.

### 4.1 작업 API (제출 → 상태 → 결과)

```bash
# ① 제출: 파일 본문 그대로 전송 (input_format: csv|txt|sdf|mol, output_format: csv|json)
curl -s -X POST 'localhost:8000/jobs?input_format=csv&output_format=csv' \
  -H 'Content-Type: text/csv' --data-binary @molecules.csv
# → 202 {"job_id": "3f2a...", "state": "queued", ...}   (Location: /jobs/3f2a...)

#    또는 JSON SMILES 목록
curl -s -X POST localhost:8000/jobs -H 'Content-Type: application/json' \
  -d '{"smiles": ["CC(=O)Nc1ccc(O)cc1", "c1ccccc1"], "ids": ["acetaminophen", "benzene"]}'

# ② 상태: state = queued → running → completed | failed
curl -s localhost:8000/jobs/3f2a...
# → {"state": "running", "n_total": 10000, "n_processed": 3000, "progress_percent": 30.0,
#    "chunks": 10, "chunks_completed": 3, "started_at": ..., "error": null, "summary": null, ...}

# ③ 결과: completed 이후 predictions 파일 (batch 모드 결과와 같은 형식)
curl -s -o predictions.csv localhost:8000/jobs/3f2a.../result
```

* 작업은 제출 순서대로 하나씩 실행되며 batch 모드와 같은 코드(청크 단위
  체크포인트)로 처리된다. 결과는 batch 결과와 같다(시험 사례 S9).
* 완료 전 결과를 요청하면 `409 E-JOB-002`, 없는 `job_id`는 `404 E-JOB-001`.
* 입력 내용 오류(예: smiles 열 없음)는 작업이 `failed`가 되고 `error`에 코드가
  담긴다(시험 사례 S10). 분자 단위 오류는 결과 파일의 해당 행에 기록된다.
* 작업 상태·결과는 `JOBS_DIR`(기본 `/data/output/jobs/<job_id>/`)에 저장된다.
  위 예처럼 `/data/output`을 마운트하면 서버를 재시작해도 남아 있고, 실행 중이던
  작업은 재시작 시 다시 대기열에 올라 완료된 청크 다음부터 이어서 처리된다.
  끝난 작업 디렉터리는 자동으로 지우지 않는다.

### 4.2 동기 예측 (`POST /predict`)

```bash
curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' \
  -d '{"smiles": ["CC(=O)Nc1ccc(O)cc1"], "ids": ["acetaminophen"]}'
```

* 요청당 1–100개. 101개 이상은 `413 E-INPUT-003` — 많은 분자는 작업 API를 쓴다.
* 일부 분자만 실패하면 `200`과 함께 해당 항목에 `status: error`가 담긴다.
  모든 분자가 실패하면 첫 오류 코드로 `422`(입력 오류) 또는 `500`을 반환한다.

### 4.3 보안

* **인증 기능이 없다.** 신뢰된 내부망에서만 쓰고, 위 예처럼 `127.0.0.1`에만
  바인딩한다. 컨테이너 코드는 외부로 접속하지 않는다.

## 5. 재현성

* 시드 42 고정, 결정적 연산, float64 추론. 같은 입력·이미지·시드면 결과가 같다.
* 허용 오차: 확률 절대오차 1×10⁻⁶ 이내, 문자열·라벨 완전 일치.
* 실측: GPU 2회 반복, GPU와 CPU 사이 최대 차이 0(출력 8자리 기준).
* 자체 시험: `python3 tests/run_tests.py --image cbibioinfolab/toxicity-prediction:mtdnn-1.0.0`
  (결과서 `docs/selftest_report.md`).
