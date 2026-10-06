# 사용자 매뉴얼 — SSL-GCN Toxicity Predictor 1.0.0

이 도구는 화합물 구조를 입력받아 **601개 독성 태스크**(Tox21 12, ClinTox 2,
ToxCast 587)마다 별도로 학습된 그래프 합성곱 신경망(GCN)으로 양성 확률을 계산한다.
입력 파일을 한 번 처리하고 종료하는 배치 분석형(T2) 도구이며, 선택적으로 HTTP
API로도 띄울 수 있다. 실행 중 인터넷에 접속하지 않고, 로그인 기능이 없다.

## 1. 실행 환경

| 항목 | 요구 사항 | 근거 |
|---|---|---|
| OS / 아키텍처 | Linux x86_64 (linux/amd64) | 이미지 빌드 플랫폼 |
| Docker | 20.10 이상 | |
| GPU (권장) | NVIDIA GPU 1장, NVIDIA 드라이버 520 이상(CUDA 11.8), NVIDIA Container Toolkit | 이미지에 CUDA 11.8 런타임·cuDNN 8 포함 |
| GPU 메모리 | 2 GB 이상 | 506분자 실행 시 최대 0.7 GB 실측 |
| 메모리 | 4 GiB 이상 | 최대 1.0 GiB 실측 (GPU 실행, CPU 실행은 1.9 GiB) |
| 디스크 | 이미지 11.4 GB | |

GPU가 없으면 CPU로 자동 전환하지만 **느리다**(GPU 약 48 분자/초, CPU 약 0.6–0.7 분자/초 — 1만 분자 기준 GPU 약 4.5분, CPU 약 4–4.5시간).
대량 처리는 GPU 환경에서 한다.

### 1.1 이미지 반입 (오프라인 환경)

인터넷이 되는 PC:

```bash
docker pull cbibioinfolab/toxicity-prediction:ssl-gcn-1.0.0
docker save cbibioinfolab/toxicity-prediction:ssl-gcn-1.0.0 | gzip > ssl-gcn-1.0.0.tar.gz
```

분석 서버:

```bash
docker load < ssl-gcn-1.0.0.tar.gz
docker run --rm --network none cbibioinfolab/toxicity-prediction:ssl-gcn-1.0.0 version
# → tox-sslgcn 1.0.0
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
  cbibioinfolab/toxicity-prediction:ssl-gcn-1.0.0
```

출력 디렉터리 권한을 바꾸기 어려우면 `--user "$(id -u):$(id -g)"`를 붙여 호스트
사용자로 실행한다. 시작할 때 가중치 체크섬 검증과 모델 601개 구성에 약 1분(실측 55초)이 걸린다.

### 2.1 입력 파일

| 확장자 | 형식 | 분자 ID |
|---|---|---|
| `.csv` | 헤더 행 필수. `smiles` 또는 `canonical_smiles` 열 필수(대소문자 무관) | `id`, `mol_id`, `name`, `compound_id` 중 처음 발견된 열. 없으면 `mol_<순번>` |
| `.txt` | 한 줄에 `SMILES [ID]` (공백 구분, 빈 줄 무시). 표준 SMILES 목록(`.smi`) 파일은 확장자만 `.txt`로 바꿔 쓴다 | 둘째 칸, 없으면 `mol_<순번>` |
| `.sdf` | 다중 분자 SDF | 분자 이름(첫 줄) |
| `.mol` | 단일 분자 | 파일 이름 |

* 인코딩은 UTF-8. 분자 수 제한은 없고, SMILES 1개는 최대 1,000자(`MAX_SMILES_LENGTH`).
* SDF/MOL은 RDKit으로 읽어 SMILES로 바꾼 뒤 SMILES 입력과 같은 방식으로 처리한다.
* **권장 입력 형태:** 모델은 RDKit canonical SMILES로 학습되었다. 같은 분자라도
  원자를 대괄호로 쓰는지에 따라 특징이 달라지므로(4.3절), 가능하면 RDKit
  canonical SMILES를 입력한다.

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
| `MODEL_DIR` | `/opt/app/models` | 가중치 디렉터리 (`SHA256SUMS` 포함) |
| `MODEL_PATH` | `$MODEL_DIR/sslgcn_pretrained.pt` | 601개 태스크 모델 묶음 |
| `VERIFY_CHECKSUM` | `1` | 시작할 때 가중치 SHA-256 검증 |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `HOST`, `PORT` | `0.0.0.0`, `8000` | serve 모드 바인딩 주소·포트 |
| `MAX_REQUEST_ITEMS` | `100` | `POST /predict` 요청 1건당 최대 분자 수 |
| `JOBS_DIR` | `$OUTPUT_DIR/jobs` | serve 모드 작업 API의 입력·결과·체크포인트 저장 경로 |
| `JOB_MAX_UPLOAD_MB` | `1024` | `POST /jobs` 본문 최대 크기(MB) |

다른 가중치를 쓰려면 디렉터리를 마운트하고 `MODEL_DIR`을 바꾼다
(`-v /path/models:/models:ro -e MODEL_DIR=/models`). 이때 디렉터리에 `SHA256SUMS`가
있어야 한다.

### 2.3 진행률·수행 시간 로그

로그는 표준 오류로 나온다. 형식 예(506분자, RTX 2080 Ti에서의 실측 속도 기준):

```
INFO sslgcn_tox: tox-sslgcn 1.0.0 — batch run started at <시작 시각>
INFO sslgcn_tox: Input: /data/input/test.csv — 506 molecules in 1 chunk(s) of 1000
INFO sslgcn_tox: Verifying model checksums ...
INFO sslgcn_tox: Model loaded: 601 task models, device=cuda
INFO sslgcn_tox: [progress] 506/506 (100.0%) chunk 1/1 elapsed=00:01:07 eta=00:00:00 rate=50.3 mol/s
INFO sslgcn_tox: Finished at <종료 시각> — elapsed 00:01:07; 506 ok, 0 error(s); output: /data/output/predictions.csv
```

청크마다 `[progress]` 줄이 하나씩 나온다. 시작·종료 시각과 소요 시간은
`run_summary.json`에도 기록된다.

### 2.4 중단과 재시작

처리 결과는 `CHUNK_SIZE` 단위로 `CHECKPOINT_DIR`에 저장된다. 중단되면 **같은 명령을
다시 실행**한다. 완료된 청크는 건너뛰고 `Resuming: k/n chunk(s) already finished`가
출력된다. 입력 파일, 청크 크기, 표준화 설정, 가중치 중 하나라도 바뀌면 체크포인트를
버리고 처음부터 실행한다. 정상 종료 후에는 체크포인트 파일을 지운다.

`MAX_CHUNKS_PER_RUN`을 주면 그 수만큼 처리하고 종료 코드 5로 멈춘다
(`run_summary.json`의 `status`가 `partial`). 같은 명령으로 이어서 실행한다.

같은 `OUTPUT_DIR`(또는 `CHECKPOINT_DIR`)로 두 작업을 동시에 실행하지 않는다.

### 2.5 종료 코드

| 코드 | 의미 |
|---|---|
| 0 | 완료. 분자 단위 오류는 결과 파일의 `status`/`error_code`에 기록 |
| 2 | 입력 오류(`E-INPUT-*`): 파일 없음, 지원하지 않는 형식, smiles 열 없음, 빈 입력 |
| 3 | 모델 오류(`E-MODEL-*`): 가중치 누락·로드 실패, 체크섬 불일치 |
| 4 | 시스템·설정 오류(`E-SYS-*`) |
| 5 | `MAX_CHUNKS_PER_RUN` 도달로 일시 중단 |

## 3. 출력

### 3.1 파일

| 파일 | 내용 |
|---|---|
| `predictions.csv` (또는 `.json`) | 입력 순서대로 분자당 1행 |
| `run_summary.json` | `status`, `n_total`, `n_ok`, `n_error`, `n_with_warnings`, 시작/종료 시각, `elapsed_sec`, 처리량, 장치, 시드, `model_sha256`(= `sslgcn_pretrained.pt`의 SHA-256), `n_tasks`(601) |

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

태스크 열 순서는 trainset 열 순서와 같다(serve 모드 `GET /schema`의 `output.tasks`).
trainset의 631개 태스크 중 30개(`GET /schema`의 `output.tasks_without_model`)는 학습 때
검증 분할에서 지표를 계산할 수 없어 모델이 없으며 출력하지 않는다.

## 4. 결과 해석

### 4.1 확률과 라벨

* 확률은 해당 분석(assay)에서 양성일 가능성에 대한 모델 점수다. Tox21·ToxCast는
  in vitro 분석이고, ClinTox의 `CT_TOX`는 임상시험 독성 실패, `FDA_APPROVED`는 FDA
  승인 여부(독성 아님)다.
* **확률은 순위 매기기에 쓴다.** 이 모델은 과신 경향이 있어 test 출력 확률의 25%가
  정확히 0 또는 1이다. 값의 크기를 보정된 위험도로 읽지 않는다.
* **`_label`은 참고용이다.** 0.5 기준으로 Tox21 태스크의 민감도는 0.02, ClinTox 두
  태스크는 0(모든 분자를 음성 판정)이다. 반면 같은 태스크의 AUROC는 Tox21 0.76,
  ClinTox 0.74로 순위 정보는 쓸 만하다.
* 태스크마다 학습 데이터 양과 성능이 크게 다르다(`docs/model_card.md`).

### 4.2 경고 코드

경고가 있어도 예측은 수행된다.

| 코드 | 조건 | 해석 |
|---|---|---|
| `W-STD-001` | 분자가 둘 이상의 조각으로 되어 있음(염, 용매, 혼합물) | trainset도 염을 포함한 채 학습했으므로 기본 설정은 그대로 예측한다. 모체만 보려면 `STANDARDIZE=1`(단, 예측이 크게 바뀔 수 있음 — 시험 사례 S6에서 최대 0.99) |
| `W-STD-002` | 전하를 띤 원자가 있음(이온화 형태) | 위와 같음 |
| `W-STD-003` | `STANDARDIZE=1`로 구조가 바뀜 | `canonical_smiles`에 바뀐 구조가 표시됨 |
| `W-FEAT-001` | 원자 특징 일부가 인코딩 범위 밖이라 0으로 인코딩됨 | 아래 참고 |

`W-FEAT-001` 조건: 원소가 다음 43개 밖(C, N, O, S, F, Si, P, Cl, Br, Mg, Na, Ca, Fe,
As, Al, I, B, V, K, Tl, Yb, Sb, Sn, Ag, Pd, Co, Se, Ti, Zn, H, Li, Ge, Cu, Au, Ni, Cd,
In, Mn, Zr, Cr, Pt, Hg, Pb)이거나, 원자의 결합 수 > 10, 암묵 원자가 > 6, 수소 수 > 4,
혼성이 SP·SP2·SP3·SP3D·SP3D2가 아닌 경우(예: 고립된 Na⁺ 같은 단원자 이온).
seed0 test 506분자 중 23분자에서 발생했고 모두 염·이온을 포함한 다중 조각 분자였다.

### 4.3 SMILES 표기에 따른 차이

이 모델의 원자 특징에는 키랄성(R/S)이 없다. 하지만 RDKit은 대괄호로 쓴 원자
(`[C@H]`, `[CH2]` 등)의 수소를 '명시적'으로 처리하므로 '암묵 원자가' 특징이 0이
된다. 그래서 같은 분자라도 입체 표기를 지운 `C(O)`와 `[C@H](O)`의 예측이 다를 수
있다(시험 사례 B2: 확률 차이 최대 0.91). 학습 데이터는 RDKit canonical SMILES였으므로
입력도 RDKit canonical 형태로 맞추는 것이 학습 조건에 가장 가깝다.

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
| `E-MODEL-001` | 503 | 작업 | 가중치 파일 누락·로드 실패 |
| `E-MODEL-002` | 503 | 작업 | `SHA256SUMS`가 없거나 가중치 해시가 다름 |
| `E-MODEL-003` | 500 | 분자 | 분자를 그래프로 바꿀 수 없음(방어용 검사) |
| `E-SYS-001` | 500 | 작업 | 출력 디렉터리에 쓸 수 없음 |
| `E-SYS-002` | 500 | 작업 | `DEVICE=cuda`인데 GPU가 보이지 않음 |
| `E-SYS-003` | 500 | 작업 | 예기치 않은 내부 오류(로그에 상세 출력) |
| `E-SYS-004` | 400 | 작업 | 환경 변수 값이 잘못됨(`DEVICE`, `OUTPUT_FORMAT`, `CHUNK_SIZE` 등) |
| `E-SYS-005` | 503 | 요청 | serve 모드에서 모델 로딩 중 (`GET /readyz`가 200이 된 뒤 재시도) |

'분자' 범위 오류는 해당 행만 `status=error`가 되고 나머지 분자는 계속 예측한다.
'작업' 범위 오류는 실행을 멈추고 종료 코드 2–4를 낸다.

### 4.5 raw SMILES 처리 예 (본 이미지에서 확인한 결과)

| 입력 | 결과 | 시험 사례 |
|---|---|---|
| 나트륨 염 `CCCOc1nn(C(=O)[N-]S(...)...)c(=O)n1C.[Na+]` | 그대로 예측, `W-STD-001;W-STD-002;W-FEAT-001` | N3 |
| 니트로기를 전하 분리 없이 쓴 `...N(=O)=O` | RDKit이 `[N+](=O)[O-]`로 정규화, 올바른 표기와 같은 예측 | S8 |
| 4급 암모늄의 `+` 누락 `CN(C)(CCOc1ccccc1)Cc1cccs1.I` | `E-INPUT-002`: `Explicit valence for atom # 1 N, 4, is greater than permitted` | E2 |
| 고리 번호 미종결 `O=C1C2CC=CCC2C(=O)NSC(Cl)(Cl)Cl` | `E-INPUT-002`: `SMILES Parse Error: unclosed ring ...` | E1 |
| 알루미늄 착물 `CC(=O)O[AlH3](O)O` | `E-INPUT-002`: `Explicit valence for atom # 4 Al, 6, is greater than permitted` (구버전 RDKit에서는 허용되던 표기) | S9 |
| 빈 SMILES | `E-INPUT-007` | S7 |

## 5. serve 모드 (HTTP API)

명세: `api/openapi.yaml` (OpenAPI 3.0.3).

| 엔드포인트 | 용도 |
|---|---|
| `GET /healthz` | 생존 확인 — 프로세스가 떠 있으면 200 (모델 로딩 중에도) |
| `GET /readyz` | 준비 확인 — 모델 로드가 끝나면 200 `ready`, 로딩 중 503 `loading`, 로드 실패 503 `failed` |
| `GET /info` | 도구 id·버전·가중치 SHA-256·장치·임계값·시드 등 설정 |
| `GET /schema` | 입력 형식, 결과 열 정의, 태스크 601개 목록(출력 순서)과 모델 없는 30개 태스크, 오류·경고 코드 |
| `POST /predict` | 소량(1–`MAX_REQUEST_ITEMS`건) 동기 예측 |
| `POST /jobs` | 작업 제출 (T2) — 건수 제한 없음, 백그라운드 실행 |
| `GET /jobs/{job_id}` | 작업 상태·진행률 조회 |
| `GET /jobs/{job_id}/result` | 작업 결과 파일 조회 |

```bash
mkdir -p output && chmod 777 output
docker run -d --name sslgcn --gpus all -p 127.0.0.1:8000:8000 \
  -v "$PWD/output:/data/output" \
  cbibioinfolab/toxicity-prediction:ssl-gcn-1.0.0 serve
curl -s localhost:8000/healthz    # 바로 200
curl -s localhost:8000/readyz     # 모델 로드(약 1분) 후 200
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
  체크포인트)로 처리된다. 결과는 batch 결과와 같다(시험 사례 S10).
* 완료 전 결과를 요청하면 `409 E-JOB-002`, 없는 `job_id`는 `404 E-JOB-001`.
* 입력 내용 오류(예: smiles 열 없음)는 작업이 `failed`가 되고 `error`에 코드가
  담긴다(시험 사례 S11). 분자 단위 오류는 결과 파일의 해당 행에 기록된다.
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
  재실행: `python3 tests/run_tests.py --image cbibioinfolab/toxicity-prediction:ssl-gcn-1.0.0`.
