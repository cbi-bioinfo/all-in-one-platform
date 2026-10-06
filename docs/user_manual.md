# 사용자 매뉴얼 — GROVER Toxicity Predictor 1.0.0

화합물 구조를 입력하면 GROVER 그래프 트랜스포머(사전학습 후 trainset으로 미세조정)가
**631개 독성 태스크**(Tox21 12, ClinTox 2, ToxCast 617)의 양성 확률을 계산한다. 입력 파일을
한 번 처리하고 끝나는 배치 분석형(T2) 도구이며, 필요하면 HTTP API로도 띄울 수 있다.
실행 중 인터넷에 접속하지 않으며 로그인 기능이 없다.

## 1. 실행 환경

| 항목 | 요구 사항 | 근거 |
|---|---|---|
| OS / 아키텍처 | Linux x86_64 (linux/amd64) | 이미지 빌드 플랫폼 |
| Docker | 20.10 이상 | |
| GPU (권장) | NVIDIA GPU, 드라이버 520 이상, NVIDIA Container Toolkit | 이미지에 CUDA 11.8 런타임 포함 |
| GPU 메모리 | 6 GB 이상 권장 | 10,974분자 실행 시 최대 4.0 GB 실측 |
| 메모리 | 2 GiB 이상 | 최대 0.94 GiB 실측 |
| 디스크 | 이미지 9.9 GB | |

GPU 처리 속도는 약 35 분자/초(RTX 2080 Ti), CPU는 약 1.7 분자/초다. 모델 로드는 약 7초.

### 1.1 이미지 반입 (오프라인 환경)

```bash
# 인터넷이 되는 PC
docker pull pzkeung/bio-synergy-platform:grover-1.0.0
docker save pzkeung/bio-synergy-platform:grover-1.0.0 | gzip > grover-1.0.0.tar.gz
# 분석 서버
docker load < grover-1.0.0.tar.gz
docker run --rm --network none pzkeung/bio-synergy-platform:grover-1.0.0 version
# → tox-grover 1.0.0
```

## 2. 배치 실행

```bash
mkdir -p input output && chmod 777 output     # 컨테이너 사용자 UID 10001
cp molecules.csv input/
docker run --rm --gpus all --network none \
  -v "$PWD/input:/data/input:ro" -v "$PWD/output:/data/output" \
  -e INPUT_PATH=/data/input/molecules.csv \
  pzkeung/bio-synergy-platform:grover-1.0.0
```

출력 디렉터리 권한을 바꾸기 어려우면 `--user "$(id -u):$(id -g)"`를 추가한다.

### 2.1 입력 파일

| 확장자 | 형식 | 분자 ID |
|---|---|---|
| `.csv` | 헤더 필수, `smiles` 또는 `canonical_smiles` 열 필수(대소문자 무관) | `id`/`mol_id`/`name`/`compound_id` 중 처음 발견된 열, 없으면 `mol_<순번>` |
| `.smi`, `.txt` | 한 줄에 `SMILES [ID]` | 둘째 칸, 없으면 `mol_<순번>` |
| `.sdf` | 다중 분자 | 분자 이름 |
| `.mol` | 단일 분자 | 파일 이름 |

UTF-8, 분자 수 제한 없음, SMILES 최대 1,000자. 모델은 **입력한 SMILES 문자열을 그대로**
특징화한다(`STANDARDIZE=1`이면 표준화된 SMILES). 입체 표기(`@`, `/`, `\`)는 예측에
반영된다(4.3절).

### 2.2 환경 변수

| 변수 | 기본값 | 설명 |
|---|---|---|
| `INPUT_PATH` | (필수) | 입력 파일 경로(컨테이너 내부) |
| `OUTPUT_DIR` | `/data/output` | 결과 저장 경로 |
| `OUTPUT_FORMAT` | `csv` | `csv` 또는 `json` |
| `DEVICE` | `auto` | `auto`, `cuda`(GPU 필수), `cpu` |
| `CHUNK_SIZE` | `1000` | 체크포인트 단위(분자 수). 결과에는 영향 없음 |
| `RESUME` | `1` | 이전 체크포인트에서 이어서 실행 |
| `MAX_CHUNKS_PER_RUN` | `0` | 1회 실행 최대 청크 수(0 = 제한 없음) |
| `CHECKPOINT_DIR` | `$OUTPUT_DIR/.checkpoint` | 체크포인트 경로 |
| `STANDARDIZE` | `0` | `1`이면 최대 유기 조각만 남기고 전하 중화 후 예측(학습 조건과 다름) |
| `MAX_SMILES_LENGTH` | `1000` | SMILES 최대 길이 |
| `SEED` | `42` | 난수 시드 |
| `MODEL_DIR` | `/opt/app/models` | 가중치 디렉터리(`SHA256SUMS` 포함) |
| `MODEL_PATH` | `$MODEL_DIR/grover_trainset_seed2.pt` | 미세조정 체크포인트 |
| `MODEL_CONFIG` | `$MODEL_DIR/grover_trainset_seed2_config.json` | 태스크 목록 |
| `VERIFY_CHECKSUM` | `1` | 시작 시 SHA-256 검증 |
| `LOG_LEVEL` | `INFO` | 로그 수준 |
| `HOST`, `PORT` | `0.0.0.0`, `8000` | serve 모드 주소·포트 |
| `MAX_REQUEST_ITEMS` | `100` | serve 요청당 최대 분자 수 |

### 2.3 진행률·수행 시간

실제 로그(trainset 10,974분자, RTX 2080 Ti, 일부):

```
INFO grover_tox: Model loaded: 631 tasks, device=cuda
INFO grover_tox: [progress] 10000/10974 (91.1%) chunk 10/11 elapsed=00:04:47 eta=00:00:27 rate=35.8 mol/s
INFO grover_tox: [progress] 10974/10974 (100.0%) chunk 11/11 elapsed=00:05:18 eta=00:00:00 rate=35.3 mol/s
INFO grover_tox: Finished at 2026-10-06T00:12:32+00:00 — elapsed 00:05:33; 10966 ok, 8 error(s); output: /data/output/predictions.csv
```

`run_summary.json`에 시작·종료 시각, `elapsed_sec`, 처리량, 건수가 기록된다.

### 2.4 중단과 재시작

결과는 `CHUNK_SIZE` 단위로 저장된다. 같은 명령을 다시 실행하면 완료된 청크를 건너뛴다
(`Resuming: k/n chunk(s) already finished`). 입력·청크 크기·표준화 설정·가중치가 바뀌면
처음부터 실행한다. `MAX_CHUNKS_PER_RUN`에 도달하면 종료 코드 5로 멈추고
`run_summary.json`의 `status`가 `partial`이 된다. 같은 출력 디렉터리로 두 작업을 동시에
실행하지 않는다. 이 모델은 배치 독립적이므로 청크 크기나 재시작 여부가 확률에 영향을
주지 않는다(시험 사례 S5).

### 2.5 종료 코드

| 코드 | 의미 |
|---|---|
| 0 | 완료(분자 단위 오류는 결과 파일에 기록) |
| 2 | 입력 오류(`E-INPUT-*`, 작업 단위) |
| 3 | 모델 오류(`E-MODEL-*`) |
| 4 | 시스템·설정 오류(`E-SYS-*`) |
| 5 | `MAX_CHUNKS_PER_RUN` 도달로 일시 중단 |

## 3. 출력

| 열 | 설명 |
|---|---|
| `index`, `id` | 입력 순서, 분자 ID |
| `input_smiles` | 입력 SMILES(SDF/MOL은 RDKit 변환값) |
| `canonical_smiles` | RDKit canonical SMILES(표시용) |
| `status` | `ok`/`error` |
| `error_code`, `error_message` | 오류 코드와 설명(RDKit 원문 포함) |
| `warnings` | 경고 코드(`;` 구분) |
| `<태스크>_prob` | 원자 관점·결합 관점 두 헤드 확률의 평균(0–1, 소수점 8자리) |
| `<태스크>_label` | `_prob` ≥ 0.5이면 1 |

태스크 열 순서는 `models/grover_trainset_seed2_config.json`의 `tasks`(Tox21 12 → ClinTox 2 →
ToxCast 617)와 같다. `run_summary.json`의 `model_sha256`은 체크포인트 파일의 SHA-256이다.

## 4. 결과 해석

### 4.1 확률과 라벨

* **확률은 순위 매기기에 쓴다.** 0.5 기준 민감도가 0.10(Tox21 0.004)으로, 라벨 열은 거의
  항상 0이다. 같은 Tox21 태스크의 AUROC는 0.75로 순위 정보는 있다.
* ClinTox 두 태스크(`FDA_APPROVED`, `CT_TOX`)는 test AUROC 0.47–0.56으로 무작위 수준이다.
  `FDA_APPROVED`는 승인 여부이며 독성이 아니다.

### 4.2 경고 코드

| 코드 | 조건 | 해석 |
|---|---|---|
| `W-STD-001` | 여러 조각(염·용매·혼합물) | 학습도 염 포함 SMILES로 했으므로 그대로 예측 |
| `W-STD-002` | 전하를 띤 원자 | 위와 같음 |
| `W-STD-003` | `STANDARDIZE=1`로 구조가 바뀜 | 바뀐 구조는 `canonical_smiles`에 표시 |
| `W-FEAT-001` | 단일·이중·삼중·방향족 외의 결합(예: 배위결합 `->`) | 그 결합의 유형 특징이 모두 0 |
| `W-FEAT-002` | 형식 전하가 −2..+2 밖, 또는 원자번호 > 100 | GROVER 특징에서 다른 값과 같은 칸에 인코딩되어 구별되지 않음 |

### 4.3 이 모델에서 확인된 성질

* **입체 표기가 예측을 바꾼다.** 원자 키랄 태그와 결합 입체가 특징에 있다. 같은 분자의
  R/S는 최대 0.039, 입체 표기 유무는 최대 0.025 차이가 났다(시험 사례 B2).
* **배치와 무관하다.** 다른 분자와 함께 넣거나 순서를 바꿔도 결과가 같다(시험 사례 S13).
* **결합이 없는 무기염**(`[I-].[K+]`)도 예측된다(S11).
* **금속 착물 표기**: 배위결합(`->`)과 단일결합 표기는 예측이 다르며(S10, 최대 0.025)
  배위결합에는 `W-FEAT-001`이 붙는다.

### 4.4 오류 코드

| 코드 | HTTP | 범위 | 의미 |
|---|---|---|---|
| `E-INPUT-001` | 422 | 작업 | 입력 파일 없음·읽기 불가·UTF-8 아님, `INPUT_PATH` 미지정 |
| `E-INPUT-002` | 422 | 분자 | RDKit이 SMILES를 해석하지 못함(문법 오류, 원자가 초과 등) |
| `E-INPUT-003` | 413 | 요청 | serve 요청 분자 수 > `MAX_REQUEST_ITEMS` |
| `E-INPUT-004` | 422 | 작업 | 지원하지 않는 확장자 |
| `E-INPUT-005` | 422 | 작업 | CSV에 smiles 열 없음 |
| `E-INPUT-006` | 422 | 작업·요청 | 분자가 하나도 없음 |
| `E-INPUT-007` | 422 | 분자 | 빈 SMILES |
| `E-INPUT-008` | 422 | 분자 | SDF/MOL 레코드 읽기 실패 |
| `E-INPUT-009` | 422 | 분자 | 표준화 후 남은 분자 없음 |
| `E-INPUT-010` | 422 | 분자 | SMILES 길이 초과 |
| `E-INPUT-011` | 422 | 요청 | serve 요청 본문 스키마 불일치 |
| `E-INPUT-012` | 422 | 분자 | 수소 외 원자가 없음(예: `[H][H]`) |
| `E-INPUT-013` | 422 | 분자 | 형식 전하 +6 이상 또는 −7 이하(GROVER가 인코딩 불가) |
| `E-MODEL-001` | 503 | 작업 | 가중치·설정 누락 또는 로드 실패 |
| `E-MODEL-002` | 503 | 작업 | 체크섬 불일치 |
| `E-MODEL-003` | 500 | 분자 | 그래프 생성 실패(방어용) |
| `E-SYS-001` | 500 | 작업 | 출력 디렉터리 쓰기 불가 |
| `E-SYS-002` | 500 | 작업 | `DEVICE=cuda`인데 GPU 없음 |
| `E-SYS-003` | 500 | 작업 | 예기치 않은 내부 오류 |
| `E-SYS-004` | 400 | 작업 | 환경 변수 값 오류 |

### 4.5 raw SMILES 처리 예 (본 이미지에서 확인)

| 입력 | 결과 | 사례 |
|---|---|---|
| 나트륨 염 `COC(=O)c1ccc(I)cc1S(=O)(=O)[N-]C(=O)Nc1nc(C)nc(OC)n1.[Na+]` | 예측, `W-STD-001;W-STD-002` | N3 |
| 니트로기 전하 분리 없이 `...c1N(=O)=O` | RDKit이 `[N+](=O)[O-]`로 정규화, 같은 예측 | S8 |
| 4급 암모늄 `+` 누락 `CC(C)N(C)(CCOC(=O)...)C(C)C.Br` | `E-INPUT-002` (원자가 초과) | E2 |
| 고리 미종결 `CCNc1nc(Cl)nc(NC(C)C)n` | `E-INPUT-002` (`unclosed ring`) | E1 |
| 알루미늄 착물 `...O[AlH3](O)O...` | `E-INPUT-002` (Al 원자가 초과) | S9 |
| `[Cr+6]` / `[Fe+5]` / `[Og]` / `[H][H]` | `E-INPUT-013` / `W-FEAT-002` / `W-FEAT-002` / `E-INPUT-012` | S12 |
| 빈 SMILES | `E-INPUT-007` | S7 |

## 5. serve 모드

```bash
docker run -d --name grover --gpus all -p 127.0.0.1:8000:8000 \
  pzkeung/bio-synergy-platform:grover-1.0.0 serve
curl -s localhost:8000/health
curl -s -X POST localhost:8000/predict -H 'Content-Type: application/json' \
  -d '{"smiles": ["CCNc1nc(Cl)nc(NC(C)C)n1"], "ids": ["atrazine"]}'
```

명세는 `api/openapi.yaml`(OpenAPI 3.0.3). 요청당 1–100개, 101개 이상은 `413 E-INPUT-003`,
빈 목록은 `422 E-INPUT-006`. 일부만 실패하면 `200`과 항목별 `status: error`, 전부 실패하면
첫 오류 코드로 `422` 또는 `500`. 응답 확률은 batch 모드와 같다(시험 사례 B1 대조, 차이 0).
**인증이 없으므로** 신뢰된 내부망에서 `127.0.0.1`에만 바인딩해 쓴다.

## 6. 재현성

시드 42, 결정적 연산, float64, 배치 독립 패딩. 허용 오차: 확률 절대오차 1×10⁻⁶, 문자열·라벨
완전 일치. 자체 시험: `python3 tests/run_tests.py --image pzkeung/bio-synergy-platform:grover-1.0.0`.
