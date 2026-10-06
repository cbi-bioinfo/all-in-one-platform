# 사용자 매뉴얼 — Chemprop Toxicity Predictor 1.0.0

이 도구는 화합물 구조를 입력받아 **631개 독성 태스크**(Tox21 12, ClinTox 2, ToxCast 617)의
양성 확률을 Chemprop 2.3.1 D-MPNN(방향성 메시지 전달 신경망) 모델 하나로 계산한다.
입력 파일을 한 번 처리하고 종료하는 배치 분석형(T2) 도구이며, 선택적으로 HTTP API로도
띄울 수 있다. 실행 중 인터넷에 접속하지 않고, 로그인 기능이 없다.

## 1. 실행 환경

| 항목 | 요구 사항 | 근거 |
|---|---|---|
| OS / 아키텍처 | Linux x86_64 (linux/amd64) | 이미지 빌드 플랫폼 |
| Docker | 20.10 이상 | |
| GPU (선택) | NVIDIA GPU, 드라이버 525 이상, NVIDIA Container Toolkit | 이미지에 CUDA 12.6 런타임 포함. 시험 환경 드라이버 575 |
| GPU 메모리 | 2 GB 이상 | 10,974분자 실행 시 최대 1.6 GB 실측 |
| 메모리 | 2 GiB 이상 | 10,974분자 실행 시 최대 1.1 GiB 실측 |
| 디스크 | 이미지 9.2 GB | |

이 모델은 분자 특징화가 계산의 대부분을 차지해 **CPU로도 GPU와 비슷하게 빠르다**
(506분자 실측: GPU(GTX 1080 Ti) 약 249 분자/초, CPU 약 237 분자/초). GPU가 없는 서버에서도 그대로 쓸 수 있다.

### 1.1 이미지 반입 (오프라인 환경)

인터넷이 되는 PC:

```bash
docker pull pzkeung/bio-synergy-platform:chemprop-1.0.0
docker save pzkeung/bio-synergy-platform:chemprop-1.0.0 | gzip > chemprop-1.0.0.tar.gz
```

분석 서버:

```bash
docker load < chemprop-1.0.0.tar.gz
docker run --rm --network none pzkeung/bio-synergy-platform:chemprop-1.0.0 version
# → tox-chemprop 1.0.0
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
  pzkeung/bio-synergy-platform:chemprop-1.0.0
```

GPU 없이 실행하려면 `--gpus all`을 빼거나 `-e DEVICE=cpu`를 준다(`auto`일 때 GPU가
보이지 않으면 경고 1줄을 출력하고 CPU를 쓴다). 출력 디렉터리 권한을 바꾸기 어려우면
`--user "$(id -u):$(id -g)"`를 붙인다.

### 2.1 입력 파일

| 확장자 | 형식 | 분자 ID |
|---|---|---|
| `.csv` | 헤더 행 필수. `smiles` 또는 `canonical_smiles` 열 필수(대소문자 무관) | `id`, `mol_id`, `name`, `compound_id` 중 처음 발견된 열. 없으면 `mol_<순번>` |
| `.smi`, `.txt` | 한 줄에 `SMILES [ID]` (공백 구분, 빈 줄 무시) | 둘째 칸, 없으면 `mol_<순번>` |
| `.sdf` | 다중 분자 SDF | 분자 이름(첫 줄) |
| `.mol` | 단일 분자 | 파일 이름 |

* 인코딩은 UTF-8. 분자 수 제한은 없고, SMILES 1개는 최대 1,000자(`MAX_SMILES_LENGTH`).
* SDF/MOL은 RDKit으로 읽어 SMILES로 바꾼 뒤 SMILES 입력과 같은 방식으로 처리한다.
* 원본 `chemprop predict`는 해석할 수 없는 SMILES가 하나라도 있으면 작업 전체가 멈추지만,
  이 도구는 해당 분자만 `E-INPUT-002`로 표시하고 나머지를 계속 예측한다.

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
| `MODEL_PATH` | `$MODEL_DIR/chemprop_trainset_seed0.pt` | chemprop 모델 체크포인트 |
| `MODEL_CONFIG` | `$MODEL_DIR/chemprop_trainset_seed0_config.json` | 태스크 이름과 출력 순서 |
| `VERIFY_CHECKSUM` | `1` | 시작할 때 체크포인트·설정 파일의 SHA-256 검증 |
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `HOST`, `PORT` | `0.0.0.0`, `8000` | serve 모드 바인딩 주소·포트 |
| `MAX_REQUEST_ITEMS` | `100` | serve 모드 요청 1건당 최대 분자 수 |

### 2.3 진행률·수행 시간 로그

로그는 표준 오류로 나온다. 실제 실행 로그(trainset 10,974분자, GTX 1080 Ti, 일부 생략):

```
INFO chemprop_tox: [progress] 10000/10974 (91.1%) chunk 10/11 elapsed=00:00:36 eta=00:00:03 rate=316.9 mol/s
INFO chemprop_tox: [progress] 10974/10974 (100.0%) chunk 11/11 elapsed=00:00:39 eta=00:00:00 rate=314.6 mol/s
INFO chemprop_tox: Finished at 2026-10-06T02:42:35+00:00 — elapsed 00:00:56; 10966 ok, 8 error(s); output: /data/output/predictions.csv
```

청크마다 `[progress]` 줄이 하나씩 나온다. 마지막 `[progress]`와 `Finished` 사이는
결과 파일(631개 태스크 × 2열)을 쓰는 시간이다. 위 실행의 오류 8건은 trainset의
`[AlH3]` 알루미늄 착물로, 4.5절 S9와 같은 원자가 오류다. 시작·종료 시각과 소요 시간은
`run_summary.json`에도 기록된다.

### 2.4 중단과 재시작

처리 결과는 `CHUNK_SIZE` 단위로 `CHECKPOINT_DIR`에 저장된다. 중단되면 **같은 명령을 다시
실행**한다. 완료된 청크는 건너뛰고 `Resuming: k/n chunk(s) already finished`가 출력된다.
입력 파일, 청크 크기, 표준화 설정, 가중치 중 하나라도 바뀌면 체크포인트를 버리고 처음부터
실행한다. 정상 종료 후에는 체크포인트 파일을 지운다.

`MAX_CHUNKS_PER_RUN`을 주면 그 수만큼 처리하고 종료 코드 5로 멈춘다
(`run_summary.json`의 `status`가 `partial`). 같은 명령으로 이어서 실행한다.
같은 `OUTPUT_DIR`(또는 `CHECKPOINT_DIR`)로 두 작업을 동시에 실행하지 않는다.

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

태스크 열 순서는 `models/chemprop_trainset_seed0_config.json`의 `tasks` 순서(Tox21 12개 →
ClinTox 2개 → ToxCast 617개)와 같다. 631개 태스크가 모두 출력된다.

## 4. 결과 해석

### 4.1 확률과 라벨

* 확률은 해당 분석(assay)에서 양성일 가능성에 대한 모델 점수다. Tox21·ToxCast는 in
  vitro 분석이고, ClinTox의 `CT_TOX`는 임상시험 독성 실패, `FDA_APPROVED`는 FDA 승인
  여부(독성 아님)다.
* **확률은 순위 매기기에 쓴다.** 0.5 기준 민감도가 낮다(전체 0.22, Tox21 0.09).
  ClinTox 시험에서는 `FDA_APPROVED`를 모든 분자에서 양성, `CT_TOX`를 모든 분자에서 음성으로
  판정했지만, 두 태스크의 AUROC는 0.91·0.86으로 순위 정보는 유용하다.
* 태스크마다 학습 데이터 양과 성능이 다르다(`docs/model_card.md`).

### 4.2 경고 코드

경고가 있어도 예측은 수행된다.

| 코드 | 조건 | 해석 |
|---|---|---|
| `W-STD-001` | 분자가 둘 이상의 조각으로 되어 있음(염, 용매, 혼합물) | trainset도 염을 포함한 채 학습했으므로 기본 설정은 그대로 예측한다. 모체만 보려면 `STANDARDIZE=1`(시험 사례 S6에서 최대 0.078 변화) |
| `W-STD-002` | 전하를 띤 원자가 있음(이온화 형태) | 위와 같음 |
| `W-STD-003` | `STANDARDIZE=1`로 구조가 바뀜 | `canonical_smiles`에 바뀐 구조가 표시됨 |
| `W-FEAT-001` | 원자 속성 일부가 특징화기의 개별 값 목록 밖이라 공통 '기타' 비트로 인코딩됨 | 아래 참고 |
| `W-FEAT-002` | 단일·이중·삼중·방향족이 아닌 결합(예: 배위결합 `->`)이 있어 결합 유형 비트 없이 인코딩됨 | 해당 결합의 종류 정보가 사라짐 |

`W-FEAT-001` 조건(chemprop v2 원자 특징화기 기준): 원자번호가 1–36과 53(I) 밖(예: Pt,
Pb, Sn, Hg, Gd), 결합 수(수소 포함) 0–5 밖, 형식 전하 −2·−1·0·+1·+2 밖, 수소 수 0–4 밖,
혼성이 S·SP·SP2·SP2D·SP3·SP3D·SP3D2 밖. Na, K, Ca, Fe, Zn, Br, I 등은 목록 안이라 경고가
붙지 않는다.

### 4.3 이 모델의 특징 표현에서 오는 성질

* **원자 특징 72차원:** 원자번호·결합 수·형식 전하·키랄 태그·수소 수·혼성 원-핫(각각
  '기타' 비트 포함), 방향족 여부, 원자 질량(×0.01). **결합 특징 14차원:** 결합 유형,
  공액, 고리, 결합 입체.
* **'기타' 원소도 서로 다르게 예측된다:** Pb와 Sn은 같은 '기타' 원소 비트를 쓰지만 질량
  특징이 달라 예측이 다르다(시험 사례 S12: 최대 0.076).
* **입체 정보를 쓴다:** 키랄 태그와 결합 입체가 특징에 있어, 입체 표기를 지우면 예측이
  달라진다(시험 사례 B2: 최대 0.022). 입체 표기가 없는 입력은 '입체 미지정'으로 처리된다.
* **금속 착물 표기:** 같은 착물을 배위결합(`->`)으로 쓰는지 단일결합으로 쓰는지에 따라
  수소 수·전하·결합 유형이 달라져 예측이 달라진다(시험 사례 S10: 최대 0.169).
* **결합이 없는 분자:** `[I-].[K+]` 같은 무기염도 예측된다(시험 사례 S11).

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
| `E-INPUT-011` | 422 | 요청 | serve 요청 본문이 API 스키마와 맞지 않음 |
| `E-MODEL-001` | 503 | 작업 | 체크포인트·설정 파일 누락, 로드 실패, 태스크 수·특징 차원 불일치 |
| `E-MODEL-002` | 503 | 작업 | `SHA256SUMS`가 없거나 해시가 다름 |
| `E-MODEL-003` | 500 | 분자 | 원자가 없는 분자(방어용 검사) |
| `E-SYS-001` | 500 | 작업 | 출력 디렉터리에 쓸 수 없음 |
| `E-SYS-002` | 500 | 작업 | `DEVICE=cuda`인데 GPU가 보이지 않음 |
| `E-SYS-003` | 500 | 작업 | 예기치 않은 내부 오류(로그에 상세 출력) |
| `E-SYS-004` | 400 | 작업 | 환경 변수 값이 잘못됨(`DEVICE`, `OUTPUT_FORMAT`, `CHUNK_SIZE` 등) |

'분자' 범위 오류는 해당 행만 `status=error`가 되고 나머지는 계속 예측한다. '작업' 범위
오류는 실행을 멈추고 종료 코드 2–4를 낸다.

### 4.5 raw SMILES 처리 예 (본 이미지에서 확인한 결과)

| 입력 | 결과 | 시험 사례 |
|---|---|---|
| 나트륨 염 `CCCOc1nn(C(=O)[N-]S(...)...)c(=O)n1C.[Na+]` | 그대로 예측, `W-STD-001;W-STD-002` | N3 |
| 니트로기를 전하 분리 없이 쓴 `...N(=O)=O` | RDKit이 `[N+](=O)[O-]`로 정규화, 올바른 표기와 같은 예측 | S8 |
| 4급 암모늄의 `+` 누락 `CN(C)(CCOc1ccccc1)Cc1cccs1.I` | `E-INPUT-002`: `Explicit valence for atom # 1 N, 4, is greater than permitted` | E2 |
| 고리 번호 미종결 `O=C1C2CC=CCC2C(=O)NSC(Cl)(Cl)Cl` | `E-INPUT-002`: `SMILES Parse Error: unclosed ring ...` | E1 |
| 알루미늄 착물 `CC(=O)O[AlH3](O)O` | `E-INPUT-002` (RDKit 2026.3.6 원자가 규칙) | S9 |
| 배위결합 시스플라틴 `N->[Pt](<-N)(Cl)Cl` | 예측, `W-FEAT-001;W-FEAT-002` | S10 |
| 유기납 `CC(=O)O[Pb](c1ccccc1)(c1ccccc1)c1ccccc1` | 예측, `W-FEAT-001` | S12 |
| 무기염 `[I-].[K+]` | 예측, `W-STD-001;W-STD-002` | S11 |
| 빈 SMILES | `E-INPUT-007` | S7 |

## 5. serve 모드 (선택)

```bash
docker run -d --name chemprop --gpus all -p 127.0.0.1:8000:8000 \
  pzkeung/bio-synergy-platform:chemprop-1.0.0 serve

curl -s localhost:8000/health
curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' \
  -d '{"smiles": ["CC(=O)Nc1ccc(O)cc1"], "ids": ["acetaminophen"]}'
```

* 명세: `api/openapi.yaml` (OpenAPI 3.0.3). `GET /health`, `GET /info`(태스크 목록·설정),
  `POST /predict`.
* 요청 1건에 1–100개. 101개 이상이면 `413 E-INPUT-003`, 빈 목록이면 `422 E-INPUT-006`.
* 일부 분자만 실패하면 `200`이고 해당 항목의 `status`가 `error`다. 모든 분자가 실패하면
  첫 번째 오류 코드로 `422`(입력 오류) 또는 `500`을 반환한다.
* **인증이 없다.** 신뢰된 내부망에서만 쓰고 위 예처럼 `127.0.0.1`에만 바인딩한다.
  컨테이너 코드는 외부로 접속하지 않는다.

## 6. 재현성

* 시드 42 고정, 결정적 연산, float64 추론. 같은 입력·이미지면 결과가 같다.
* 허용 오차: 확률 절대오차 1×10⁻⁶ 이내, 문자열·라벨·코드는 완전 일치.
* 실측 결과와 자체 시험: `docs/selftest_report.md`.
  재실행: `python3 tests/run_tests.py --image pzkeung/bio-synergy-platform:chemprop-1.0.0`.
