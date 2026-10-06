# 사용자 매뉴얼 — FP-GNN Toxicity Predictor 1.0.0

이 도구는 화합물 구조를 입력받아 **631개 독성 태스크**(Tox21 12, ClinTox 2, ToxCast 617)의
양성 확률을 계산한다. 모델은 FP-GNN으로, 분자 지문(MACCS·ErG·PubChem)과 원자 그래프 주의망을
함께 쓰는 다중작업 신경망이다. 입력 파일을 한 번 처리하고 종료하는 배치 분석형(T2) 도구이며,
선택적으로 HTTP API로 띄울 수 있다. 실행 중 인터넷에 접속하지 않고, 로그인 기능이 없다.

## 1. 실행 환경

| 항목 | 요구 사항 | 근거 |
|---|---|---|
| OS / 아키텍처 | Linux x86_64 (linux/amd64) | 이미지 빌드 플랫폼 |
| Docker | 20.10 이상 | |
| GPU (선택) | NVIDIA GPU, 드라이버 520 이상(CUDA 11.8), NVIDIA Container Toolkit | 이미지에 CUDA 11.8 런타임 포함 |
| GPU 메모리 | 1 GB 이상 | 최대 280 MiB 실측(`nvidia-smi`, CUDA 컨텍스트 포함) |
| 메모리 | 2 GiB 이상 | 10,974분자 실행 시 최대 0.80 GiB 실측 |
| 디스크 | 이미지 8.7 GB | |

처리 속도(실측): GPU(GTX 1080 Ti) 약 61 분자/초(10,974분자). CPU는 서버의 다른 작업 부하에 따라
3–47 분자/초로 크게 달라진다. 처리 시간의 약 절반은
CPU에서 계산하는 분자 지문이라 GPU가 빨라져도 처리량이 크게 늘지 않는다. 모델 로드는 약 1초다.

### 1.1 이미지 반입 (오프라인 환경)

인터넷이 되는 PC:

```bash
docker pull cbibioinfolab/toxicity-prediction:fp-gnn-1.0.0
docker save cbibioinfolab/toxicity-prediction:fp-gnn-1.0.0 | gzip > fp-gnn-1.0.0.tar.gz
```

분석 서버:

```bash
docker load < fp-gnn-1.0.0.tar.gz
docker run --rm --network none cbibioinfolab/toxicity-prediction:fp-gnn-1.0.0 version
# → tox-fpgnn 1.0.0
```

## 2. 배치 실행 (기본)

```bash
mkdir -p input output
cp molecules.csv input/
chmod 777 output            # 컨테이너는 UID 10001(app)로 실행된다

docker run --rm --gpus all --network none \
  -v "$PWD/input:/data/input:ro" \
  -v "$PWD/output:/data/output" \
  -e INPUT_PATH=/data/input/molecules.csv \
  cbibioinfolab/toxicity-prediction:fp-gnn-1.0.0
```

GPU가 없으면 `--gpus all`을 빼고 실행한다(자동으로 CPU 사용, 경고 1줄 출력). 출력 디렉터리
권한을 바꾸기 어려우면 `--user "$(id -u):$(id -g)"`를 붙인다.

### 2.1 입력 파일

| 확장자 | 형식 | 분자 ID |
|---|---|---|
| `.csv` | 헤더 행 필수. `smiles` 또는 `canonical_smiles` 열 필수(대소문자 무관) | `id`, `mol_id`, `name`, `compound_id` 중 처음 발견된 열. 없으면 `mol_<순번>` |
| `.txt` | 한 줄에 `SMILES [ID]` (공백 구분, 빈 줄 무시). 표준 SMILES 목록(`.smi`) 파일은 확장자만 `.txt`로 바꿔 쓴다 | 둘째 칸, 없으면 `mol_<순번>` |
| `.sdf` | 다중 분자 SDF | 분자 이름(첫 줄) |
| `.mol` | 단일 분자 | 파일 이름 |

인코딩은 UTF-8. 분자 수 제한은 없고, SMILES 1개는 최대 1,000자(`MAX_SMILES_LENGTH`).
SDF/MOL은 RDKit으로 읽어 SMILES로 바꾼 뒤 SMILES와 같은 방식으로 처리한다.

### 2.2 환경 변수

| 변수 | 기본값 | 설명 |
|---|---|---|
| `INPUT_PATH` | (batch 필수) | 입력 파일 경로(컨테이너 내부) |
| `OUTPUT_DIR` | `/data/output` | 결과 저장 경로 |
| `OUTPUT_FORMAT` | `csv` | `csv` 또는 `json` |
| `DEVICE` | `auto` | `auto`(GPU가 보이면 GPU), `cuda`(GPU 필수), `cpu` |
| `CHUNK_SIZE` | `1000` | 체크포인트 단위(분자 수) |
| `RESUME` | `1` | 이전 체크포인트에서 이어서 실행 |
| `MAX_CHUNKS_PER_RUN` | `0` | 1회 실행에서 처리할 최대 청크 수(0 = 제한 없음) |
| `CHECKPOINT_DIR` | `$OUTPUT_DIR/.checkpoint` | 체크포인트 저장 경로 |
| `STANDARDIZE` | `0` | `1`이면 최대 유기 조각만 남기고 전하를 중화한 뒤 예측(학습 조건과 다름, 4.2절) |
| `MAX_SMILES_LENGTH` | `1000` | SMILES 최대 길이 |
| `SEED` | `42` | 난수 시드 |
| `MODEL_DIR` | `/opt/app/models` | 가중치 디렉터리(`SHA256SUMS` 포함) |
| `MODEL_PATH` | `$MODEL_DIR/fpgnn_pretrained.pt` | 모델 체크포인트 |
| `MODEL_CONFIG` | `$MODEL_DIR/fpgnn_pretrained_config.json` | 모델 구조 설정과 태스크 목록 |
| `VERIFY_CHECKSUM` | `1` | 시작할 때 체크포인트·설정 파일 SHA-256 검증 |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `HOST`, `PORT` | `0.0.0.0`, `8000` | serve 모드 바인딩 주소·포트 |
| `MAX_REQUEST_ITEMS` | `100` | `POST /predict` 요청 1건당 최대 분자 수 |
| `JOBS_DIR` | `$OUTPUT_DIR/jobs` | serve 모드 작업 API의 입력·결과·체크포인트 저장 경로 |
| `JOB_MAX_UPLOAD_MB` | `1024` | `POST /jobs` 본문 최대 크기(MB) |

### 2.3 진행률·수행 시간 로그

로그는 표준 오류로 나온다. 실제 실행 로그(trainset 10,974분자, GTX 1080 Ti, 앞부분 생략):

```
INFO fpgnn_tox: [progress] 10000/10974 (91.1%) chunk 10/11 elapsed=00:02:32 eta=00:00:14 rate=66.6 mol/s
INFO fpgnn_tox: [progress] 10974/10974 (100.0%) chunk 11/11 elapsed=00:02:47 eta=00:00:00 rate=66.4 mol/s
INFO fpgnn_tox: Finished at 2026-10-06T00:03:57+00:00 — elapsed 00:03:02; 10966 ok, 8 error(s); output: /data/output/predictions.csv
```

청크마다 `[progress]` 줄이 하나씩 나온다. 마지막 `[progress]`와 `Finished` 사이에는 청크 결과를
합쳐 결과 파일을 쓰는 시간이 들어간다. 위 실행에서 오류 8건은 RDKit 2026.3.6이 원자가 초과로
거부하는 `[AlH3]` 알루미늄 착물이다(4.5절).

### 2.4 중단과 재시작

처리 결과는 `CHUNK_SIZE` 단위로 `CHECKPOINT_DIR`에 저장된다. 중단되면 **같은 명령을 다시 실행**
한다. 완료된 청크는 건너뛰고 `Resuming: k/n chunk(s) already finished`가 출력된다. 입력 파일,
청크 크기, 표준화 설정, 가중치 중 하나라도 바뀌면 체크포인트를 버리고 처음부터 실행한다. 정상
종료 후에는 체크포인트 파일을 지운다.

`MAX_CHUNKS_PER_RUN`을 주면 그 수만큼 처리하고 종료 코드 5로 멈춘다(`run_summary.json`의
`status`가 `partial`). 같은 명령으로 이어서 실행한다. 같은 `OUTPUT_DIR`(또는 `CHECKPOINT_DIR`)로
두 작업을 동시에 실행하지 않는다.

### 2.5 종료 코드

| 코드 | 의미 |
|---|---|
| 0 | 완료. 분자 단위 오류는 결과 파일의 `status`/`error_code`에 기록 |
| 2 | 입력 오류(`E-INPUT-*`): 파일 없음, 지원하지 않는 형식, smiles 열 없음, 빈 입력 |
| 3 | 모델 오류(`E-MODEL-*`): 체크포인트·설정 누락·로드 실패, 체크섬 불일치 |
| 4 | 시스템·설정 오류(`E-SYS-*`) |
| 5 | `MAX_CHUNKS_PER_RUN` 도달로 일시 중단 |

## 3. 출력

### 3.1 파일

| 파일 | 내용 |
|---|---|
| `predictions.csv` (또는 `.json`) | 입력 순서대로 분자당 1행 |
| `run_summary.json` | `status`, `n_total`, `n_ok`, `n_error`, `n_with_warnings`, 시작/종료 시각, `elapsed_sec`, 처리량(결과 파일 쓰기 포함), 장치, 시드, `model_sha256`, `n_tasks`(631) |

### 3.2 `predictions.csv` 열

| 열 | 자료형 | 설명 |
|---|---|---|
| `index` | 정수 | 입력 순서(0부터) |
| `id` | 문자열 | 분자 ID |
| `input_smiles` | 문자열 | 입력 SMILES(SDF/MOL은 RDKit이 변환한 SMILES) |
| `canonical_smiles` | 문자열 | RDKit canonical SMILES(표시용) |
| `status` | `ok`/`error` | 처리 결과 |
| `error_code`, `error_message` | 문자열 | 오류 코드와 설명(RDKit 원문 메시지 포함) |
| `warnings` | 문자열 | 경고 코드, `;`로 구분 |
| `<태스크>_prob` | 실수 0–1 | 해당 태스크 양성(독성·활성) 확률, 소수점 8자리 |
| `<태스크>_label` | 0/1 | `_prob` ≥ 0.5이면 1 |

태스크 열 순서는 `models/fpgnn_pretrained_config.json`의 `tasks` 순서(Tox21 12개 → ClinTox
2개 → ToxCast 617개, serve 모드 `GET /schema`의 `output.tasks`)와 같고 631개가 모두 출력된다.

## 4. 결과 해석

### 4.1 확률과 라벨

* 확률은 해당 분석(assay)에서 양성일 가능성에 대한 모델 점수다. Tox21·ToxCast는 in vitro
  분석, ClinTox의 `CT_TOX`는 임상시험 독성 실패, `FDA_APPROVED`는 FDA 승인 여부(독성 아님)다.
* **확률은 순위 매기기에 쓴다.** 0.5 기준 민감도는 전체 0.26, Tox21 0.40이다. 순위 성능(AUROC)은
  Tox21 0.80, ClinTox 0.77, ToxCast 0.71이다.
* 다중작업 모델이라 학습 라벨이 적은 태스크도 확률이 출력되지만 그 신뢰도는 낮다(`docs/model_card.md`).

### 4.2 경고 코드

경고가 있어도 예측은 수행된다.

| 코드 | 조건 | 해석 |
|---|---|---|
| `W-STD-001` | 분자가 둘 이상의 조각(염, 용매, 혼합물) | trainset도 염을 포함한 채 학습했으므로 기본 설정은 그대로 예측한다. 모체만 보려면 `STANDARDIZE=1` — 예측이 바뀐다(시험 사례 S6: 최대 0.28) |
| `W-STD-002` | 전하를 띤 원자가 있음(이온화 형태) | 위와 같음 |
| `W-STD-003` | `STANDARDIZE=1`로 구조가 바뀜 | `canonical_smiles`에 바뀐 구조가 표시됨 |
| `W-FEAT-001` | 원자 특징 중 하나 이상이 원-핫 범주 밖이라 '기타' 칸으로 인코딩됨 | 아래 참고 |
| `W-FEAT-002` | 결합이 하나도 없는 원자가 있음(예: 염의 Na⁺, K⁺, I⁻) | 아래 참고 |

`W-FEAT-001` 조건 — 원자번호 > 100, 총 결합 수(수소 포함) > 5, 형식 전하가 −2..+2 밖, 키랄 태그
값 > 3, 총 수소 수 > 4, 혼성이 SP·SP2·SP3·SP3D·SP3D2가 아님. 실제로는 혼성이 'S'로 정해지는
단원자 이온(Na⁺ 등)과 명시적 수소(`[2H]`), 일부 금속(Pt 등)에서 생긴다. seed0 test 506분자 중
23분자, trainset 10,974분자 중 516분자에서 발생했다.

`W-FEAT-002` — 그래프 주의는 결합으로 연결된 이웃 원자 사이에서만 계산되고 원자 자신은 포함하지
않는다. 결합이 없는 원자는 이웃이 없어 분자 안의 모든 원자에 균등하게 주의가 퍼진다(학습 때와 같은
계산이며 오류가 아니다). seed0 test 중 69분자, trainset 중 1,359분자에서 발생했다.

### 4.3 이 모델의 특징 표현에서 오는 성질

* **입체 정보:** 원자 특징에 RDKit 키랄 태그가 들어간다. 같은 골격이라도 R/S 또는 입체 표기 유무에
  따라 예측이 소폭 달라진다(시험 사례 B2: 최대 0.0025).
* **금속 착물 표기:** 같은 착물을 배위결합(`[NH3]->[Pt]`)으로 쓰는지 단일결합(`N[Pt]`)으로 쓰는지에
  따라 수소 수·결합 수가 달라져 예측이 크게 바뀔 수 있다(시험 사례 S10: 최대 0.34).
* **분자 지문:** MACCS 167비트, ErG 441값(fuzzIncrement 0.3, 경로 1–21), PubChem 881비트를 쓴다.
  PubChem 지문은 수소를 명시적으로 붙인 분자에 SMARTS 패턴을 적용해 계산한다.

### 4.4 오류 코드

| 코드 | HTTP | 범위 | 의미 |
|---|---|---|---|
| `E-INPUT-001` | 422 | 작업 | 입력 파일이 없거나 읽을 수 없음(UTF-8 아님 포함), `INPUT_PATH` 미지정 |
| `E-INPUT-002` | 422 | 분자 | RDKit이 SMILES를 해석하지 못함(문법 오류, 원자가 초과 등). RDKit 원문 메시지 포함 |
| `E-INPUT-003` | 413 | 요청 | serve 요청 1건의 분자 수가 `MAX_REQUEST_ITEMS` 초과 |
| `E-INPUT-004` | 422 | 작업 | 지원하지 않는 확장자 |
| `E-INPUT-005` | 422 | 작업 | CSV에 `smiles`/`canonical_smiles` 열이 없음 |
| `E-INPUT-006` | 422 | 작업·요청 | 분자가 하나도 없음 |
| `E-INPUT-007` | 422 | 분자 | 빈 SMILES 또는 원자가 없는 SMILES |
| `E-INPUT-008` | 422 | 분자 | SDF/MOL 레코드를 읽을 수 없음 |
| `E-INPUT-009` | 422 | 분자 | `STANDARDIZE=1` 처리 후 남은 분자가 없음 |
| `E-INPUT-010` | 422 | 분자 | SMILES가 `MAX_SMILES_LENGTH`보다 김 |
| `E-INPUT-011` | 422 | 요청 | serve 요청 본문·쿼리가 API 스키마와 맞지 않음 |
| `E-INPUT-012` | 413 | 요청 | `POST /jobs` 본문이 `JOB_MAX_UPLOAD_MB` 초과 |
| `E-JOB-001` | 404 | 요청 | 없는 `job_id` |
| `E-JOB-002` | 409 | 요청 | 작업이 완료되지 않아 결과가 없음(`queued`/`running`/`failed`) |
| `E-MODEL-001` | 503 | 작업 | 체크포인트·설정 파일 누락 또는 로드 실패 |
| `E-MODEL-002` | 503 | 작업 | `SHA256SUMS`가 없거나 해시가 다름 |
| `E-MODEL-003` | 500 | 분자 | 분자를 특징으로 바꿀 수 없음(방어용 검사) |
| `E-SYS-001` | 500 | 작업 | 출력 디렉터리에 쓸 수 없음 |
| `E-SYS-002` | 500 | 작업 | `DEVICE=cuda`인데 GPU가 보이지 않음 |
| `E-SYS-003` | 500 | 작업 | 예기치 않은 내부 오류(로그에 상세 출력) |
| `E-SYS-004` | 400 | 작업 | 환경 변수 값이 잘못됨(`DEVICE`, `OUTPUT_FORMAT`, `CHUNK_SIZE` 등) |
| `E-SYS-005` | 503 | 요청 | serve 모드에서 모델 로딩 중 (`GET /readyz`가 200이 된 뒤 재시도) |

'분자' 범위 오류는 해당 행만 `status=error`가 되고 나머지는 계속 예측한다. '작업' 범위 오류는
실행을 멈추고 종료 코드 2–4를 낸다.

### 4.5 raw SMILES 처리 예 (본 이미지에서 확인한 결과)

| 입력 | 결과 | 시험 사례 |
|---|---|---|
| 나트륨 염 `CCCOc1nn(C(=O)[N-]S(...)...)c(=O)n1C.[Na+]` | 그대로 예측, `W-STD-001;W-STD-002;W-FEAT-001;W-FEAT-002` | N3 |
| 니트로기를 전하 분리 없이 쓴 `...N(=O)=O` | RDKit이 `[N+](=O)[O-]`로 정규화, 올바른 표기와 같은 예측 | S8 |
| 4급 암모늄의 `+` 누락 `CN(C)(CCOc1ccccc1)Cc1cccs1.I` | `E-INPUT-002`: `Explicit valence for atom # 1 N, 4, is greater than permitted` | E2 |
| 고리 번호 미종결 `O=C1C2CC=CCC2C(=O)NSC(Cl)(Cl)Cl` | `E-INPUT-002`: `SMILES Parse Error: unclosed ring ...` | E1 |
| 알루미늄 착물 `CC(=O)O[AlH3](O)O` | `E-INPUT-002`: `Explicit valence for atom # 4 Al, 6, is greater than permitted` | S9 |
| 시스플라틴 `N->[Pt](<-N)(Cl)Cl` / `N[Pt](N)(Cl)Cl` | 둘 다 예측, `W-FEAT-001`, 확률 차이 최대 0.34 | S10 |
| 무기염 `[I-].[K+]` | 예측, `W-STD-001;W-STD-002;W-FEAT-001;W-FEAT-002` | S11 |
| 빈 SMILES | `E-INPUT-007` | S7 |

## 5. serve 모드 (HTTP API)

명세: `api/openapi.yaml` (OpenAPI 3.0.3).

| 엔드포인트 | 용도 |
|---|---|
| `GET /healthz` | 생존 확인 — 프로세스가 떠 있으면 200 (모델 로딩 중에도) |
| `GET /readyz` | 준비 확인 — 모델 로드가 끝나면 200 `ready`, 로딩 중 503 `loading`, 로드 실패 503 `failed` |
| `GET /info` | 도구 id·버전·가중치 SHA-256·장치·임계값·시드 등 설정 |
| `GET /schema` | 입력 형식, 결과 열 정의, 태스크 631개 목록(출력 순서), 오류·경고 코드 |
| `POST /predict` | 소량(1–`MAX_REQUEST_ITEMS`건) 동기 예측 |
| `POST /jobs` | 작업 제출 (T2) — 건수 제한 없음, 백그라운드 실행 |
| `GET /jobs/{job_id}` | 작업 상태·진행률 조회 |
| `GET /jobs/{job_id}/result` | 작업 결과 파일 조회 |

```bash
mkdir -p output && chmod 777 output
docker run -d --name fpgnn --gpus all -p 127.0.0.1:8000:8000 \
  -v "$PWD/output:/data/output" \
  cbibioinfolab/toxicity-prediction:fp-gnn-1.0.0 serve
curl -s localhost:8000/healthz    # 바로 200
curl -s localhost:8000/readyz     # 모델 로드(약 1초) 후 200
```

모델은 서버 시작 후 백그라운드에서 읽는다. 로딩 중 `/predict`·`/schema`는
`503 E-SYS-005`를 반환하고, 그 사이 제출한 작업은 대기열에서 로드 완료를 기다린다.

### 5.1 작업 API (제출 → 상태 → 결과)

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
  체크포인트)로 처리된다. 결과는 batch 결과와 같다(시험 사례 S12).
* 완료 전 결과를 요청하면 `409 E-JOB-002`, 없는 `job_id`는 `404 E-JOB-001`.
* 입력 내용 오류(예: smiles 열 없음)는 작업이 `failed`가 되고 `error`에 코드가
  담긴다(시험 사례 S13). 분자 단위 오류는 결과 파일의 해당 행에 기록된다.
* 작업 상태·결과는 `JOBS_DIR`(기본 `/data/output/jobs/<job_id>/`)에 저장된다.
  위 예처럼 `/data/output`을 마운트하면 서버를 재시작해도 남아 있고, 실행 중이던
  작업은 재시작 시 다시 대기열에 올라 완료된 청크 다음부터 이어서 처리된다.
  끝난 작업 디렉터리는 자동으로 지우지 않는다.

### 5.2 동기 예측 (`POST /predict`)

```bash
curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' \
  -d '{"smiles": ["CC(=O)Nc1ccc(O)cc1"], "ids": ["acetaminophen"]}'
```

* 요청 1건에 1–100개. 101개 이상이면 `413 E-INPUT-003`(많은 분자는 작업 API 사용),
  빈 목록이면 `422 E-INPUT-006`.
* 일부 분자만 실패하면 `200`이고 해당 항목의 `status`가 `error`다. 모든 분자가
  실패하면 첫 번째 오류 코드로 `422`(입력 오류) 또는 `500`을 반환한다.

### 5.3 보안

* **인증이 없다.** 신뢰된 내부망에서만 쓰고 위 예처럼 `127.0.0.1`에만 바인딩한다.
  컨테이너 코드는 외부로 접속하지 않는다.

## 6. 재현성

* 시드 42 고정, 결정적 연산, float64 추론. 같은 입력·이미지면 결과가 같다.
* 허용 오차: 확률 절대오차 1×10⁻⁶ 이내, 문자열·라벨·코드는 완전 일치.
* 실측 결과와 자체 시험: `docs/selftest_report.md`.
  재실행: `python3 tests/run_tests.py --image cbibioinfolab/toxicity-prediction:fp-gnn-1.0.0`.
