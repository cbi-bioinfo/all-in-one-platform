# 자체 시험 결과서 — SSL-GCN Toxicity Predictor 1.0.0

## 1. 시험 환경

| 항목 | 값 |
|---|---|
| 이미지 | `cbibioinfolab/toxicity-prediction:ssl-gcn-1.0.0` |
| 이미지 ID | `sha256:9c8b13a2cde27b45b7d859bdbcc2c4694e303ded308872b544545870e2ebf5b2` |
| 실행 장치 | GPU |
| 네트워크 | `--network none` (모든 사례) |
| 실행 시각 | 2026-10-06T18:49:53+09:00 |
| 시험 도구 | `tests/run_tests.py` |
| 허용 오차 | 확률값 절대오차 1e-06 이내, 문자열·판정값(라벨·상태·코드·메시지·경고·HTTP 상태·종료 코드)은 완전 일치 |

**결과: 22/22 일치**

## 2. 골든 데이터셋 시험 결과 (`/tests/golden/`)

| 사례 | 구분 | 입력 요약 | 기대 결과 | 실제 결과 | 확률 최대 오차 | 일치 |
|---|---|---|---|---|---|---|
| B1 | 경계 | 경계 대표 분자 10건 (serve, 원 100건 사례에서 추출) — 짧은(6·9자)·긴(196·235자) SMILES, 금속 착물 페로센·니켈로센(다중 조각·전하, W-STD-001·002), 전하 분자 2건(W-STD-002), '/'·'@' 입체 표기 | HTTP 200, 10 ok / 0 error | HTTP 200, 10 ok / 0 error | 0.0e+00 (6010개) | 일치 |
| B2 | 경계 | 입체 표기 [C@H] 포함 vs 제거 분자 — 키랄성은 특징에 없지만 대괄호 원자는 암묵 원자가 0으로 인코딩되어 두 예측이 다름 | exit 0, 2 ok / 0 error | exit 0, 2 ok / 0 error | 0.0e+00 (1202개) | 일치 |
| E1 | 오류 | 고리 미종결 SMILES (serve, 단일 요청) | HTTP 422, E-INPUT-002 | HTTP 422, E-INPUT-002 | — | 일치 |
| E2 | 오류 | 전하 표기가 빠진 4급 암모늄염 raw SMILES — 원자가 오류 행만 E-INPUT-002, 나머지 계속 | exit 0, 1 ok / 1 error, E-INPUT-002, warn W-STD-001,W-STD-002 | exit 0, 1 ok / 1 error, E-INPUT-002, warn W-STD-001,W-STD-002 | 0.0e+00 (601개) | 일치 |
| N1 | 정상 | 단일 화합물 (captan, trainset 홀드아웃 test 분자) | exit 0, 1 ok / 0 error | exit 0, 1 ok / 0 error | 0.0e+00 (601개) | 일치 |
| N2 | 정상 | 10건 일괄 예측 (CSV) | exit 0, 10 ok / 0 error | exit 0, 10 ok / 0 error | 0.0e+00 (6010개) | 일치 |
| N3 | 정상 | 나트륨 염·이온화 raw SMILES (.txt 입력) — 학습과 동일하게 그대로 예측, 경고 표시 | exit 0, 1 ok / 0 error, warn W-FEAT-001,W-STD-001,W-STD-002 | exit 0, 1 ok / 0 error, warn W-FEAT-001,W-STD-001,W-STD-002 | 0.0e+00 (601개) | 일치 |

## 3. 보조 시험 결과 (`/tests/cases/`)

| 사례 | 구분 | 입력 요약 | 기대 결과 | 실제 결과 | 확률 최대 오차 | 일치 |
|---|---|---|---|---|---|---|
| S1 | 오류 | 요청당 최대 건수 초과 101건 (serve) | HTTP 413, E-INPUT-003 | HTTP 413, E-INPUT-003 | — | 일치 |
| S10 | 정상 | T2 작업 인터페이스 — POST /jobs 제출 → GET /jobs/{job_id} 상태 → GET /jobs/{job_id}/result 결과 (입력: 전하 표기 누락 4급 암모늄 raw + 정상 표기 2건, batch와 동일 결과) | HTTP 202, job completed, 1 ok / 1 error | HTTP 202, job completed, 1 ok / 1 error | 0.0e+00 (601개) | 일치 |
| S11 | 오류 | T2 작업 — smiles 열이 없는 CSV 제출, 작업 상태 failed + E-INPUT-005 | HTTP 202, job failed, E-INPUT-005 | HTTP 202, job failed, E-INPUT-005 | — | 일치 |
| S12 | 오류 | 존재하지 않는 job_id 상태 조회 — 404 E-JOB-001 | HTTP 404, E-JOB-001 | HTTP 404, E-JOB-001 | — | 일치 |
| S13 | 정상 | GET /healthz — 프로세스 생존 확인 (serve) | HTTP 200 | HTTP 200 | — | 일치 |
| S14 | 정상 | GET /schema — 입력 형식, 결과 열, 태스크 목록(출력 순서), 오류·경고 코드 (serve) | HTTP 200 | HTTP 200 | — | 일치 |
| S15 | 경계 | 요청당 최대 건수 100건 (serve) | HTTP 200, 100 ok / 0 error | HTTP 200, 100 ok / 0 error | 0.0e+00 (60100개) | 일치 |
| S2 | 오류 | 빈 요청 목록 (serve) | HTTP 422, E-INPUT-006 | HTTP 422, E-INPUT-006 | — | 일치 |
| S3 | 오류 | smiles 컬럼이 없는 CSV (batch) | exit 2, E-INPUT-005 | exit 2, E-INPUT-005 | — | 일치 |
| S4 | 오류 | 지원하지 않는 입력 형식 .xlsx (batch) | exit 2, E-INPUT-004 | exit 2, E-INPUT-004 | — | 일치 |
| S5 | 경계 | 체크포인트 재시작 — CHUNK_SIZE=3, MAX_CHUNKS_PER_RUN=2로 중단 후 재실행 (N2와 동일 결과) | exit [5, 0], 10 ok / 0 error | exit [5, 0], 10 ok / 0 error | 0.0e+00 (6010개) | 일치 |
| S6 | 정상 | STANDARDIZE=1 — 염 제거·전하 중화 후 예측 (N3과 같은 입력) | exit 0, 1 ok / 0 error, warn W-STD-001,W-STD-002,W-STD-003 | exit 0, 1 ok / 0 error, warn W-STD-001,W-STD-002,W-STD-003 | 0.0e+00 (601개) | 일치 |
| S7 | 경계 | 정상·오류 혼합 요청 — 200 응답에 행별 오류 포함 (serve) | HTTP 200, 2 ok / 1 error | HTTP 200, 2 ok / 1 error | 0.0e+00 (1202개) | 일치 |
| S8 | 정상 | 전하 분리 없이 표기한 니트로기 raw SMILES — RDKit이 [N+](=O)[O-]로 자동 정규화, 올바른 표기와 동일 예측 | exit 0, 2 ok / 0 error, warn W-STD-002 | exit 0, 2 ok / 0 error, warn W-STD-002 | 0.0e+00 (1202개) | 일치 |
| S9 | 경계 | RDKit 버전 의존 구조 — [AlH3] 알루미늄 착물(구버전 RDKit에서는 유효)은 E-INPUT-002, 나머지 행은 계속 | exit 0, 1 ok / 1 error, E-INPUT-002 | exit 0, 1 ok / 1 error, E-INPUT-002 | 0.0e+00 (601개) | 일치 |

## 4. 추가 검증 (재현성·정확성)

측정일 2026-10-06, 측정 이미지 `sha256:420ee9619c96…`(아래 '측정 이미지' 참고), 입력은
seed0 test 506분자. 같은 서버에서 다른 사용자 작업이 돌고 있는 상태(load average 약 30–40)였다.

| 항목 | 방법 | 결과 |
|---|---|---|
| 반복 실행 결정성 (GPU 간) | 506분자를 RTX 2080 Ti(`--gpus device=0`)와 GTX 1080 Ti(`device=1`)에서 각각 batch 실행해 비교 | 최대 절대오차 **0** (304,106개 확률값), 라벨·문자열 열 불일치 0 |
| 장치 간 결정성 (GPU ↔ CPU) | 같은 입력을 `DEVICE=cpu`로 실행해 비교 | 최대 절대오차 **0**, 모든 열 일치 |
| 가중치 묶기 전후 일치 | 같은 입력을 묶기 전 이미지(`pzkeung/bio-synergy-platform:ssl-gcn-1.0.0`, 태스크별 `model.pth` 601개)로 실행해 비교 | 최대 절대오차 **0**, 모든 열 일치 |
| 가중치 묶음 동일성 | 태스크별 `model.pth` 601개를 `sslgcn_pretrained.pt` 하나로 묶은 뒤 다시 읽어 원본과 텐서 단위 비교 | 텐서 31,853개 dtype·값 모두 동일 |
| batch ↔ serve 일치 | S15(100건)을 batch로 실행해 serve 기대 응답(`tests/cases/S15/expected.json`)과 비교 | 최대 절대오차 **0** (60,100개), 라벨 일치 |
| batch ↔ 작업 API 일치 | S10 입력(4급 암모늄 raw + 정상 표기)을 `POST /jobs`로 제출해 받은 결과 파일과 batch 기대 결과 비교 (S10) | 파일 바이트 단위 동일 |
| 평가 성능 재현 | 이전 빌드에서 컨테이너 예측으로 seed0 test 지표를 다시 계산해 학습 환경(float32) 재채점값과 비교. 현재 이미지의 예측은 이전 빌드와 같으므로(위 '가중치 묶기 전후 일치') 지표도 같다 | F1 0.153997 / 민감도 0.264900 / 특이도 0.754410 / 평가 태스크 534개 — 일치. AUROC 0.599252 vs 0.597232 — 분자별 확률 차이 최대 3×10⁻⁵이나 포화 확률(0·1)의 동점 처리 차이로 순위가 바뀜(`docs/model_card.md` 4.3) |
| 금속 착물 처리 | RDKit 2026에서 canonical SMILES가 바뀌는 5개 분자(코발라민 4, 유기납 1)를 입력 문자열에서 바로 그래프로 변환하는지 확인 | 학습 경로(`smiles_to_bigraph`)와 같은 그래프 사용 |
| 오프라인 실행 | 모든 시험을 `--network none`으로 실행 | 정상 동작 |
| 비루트 실행 | 이미지 `User` 설정, 출력 파일 소유자 | UID 10001 (`app`) |
| 가중치 무결성 | 시작 시 `models/SHA256SUMS`로 `sslgcn_pretrained.pt` 검증 | 일치 |
| 모델 로드 시간 | 로그의 시작 시각 ~ `Model loaded` (체크섬 검증 + 601개 모델 구성) | GPU 50–55초, CPU 45–53초 |
| GPU 처리량 | 506분자, `run_summary.json`의 `throughput_mol_per_sec` | RTX 2080 Ti 47.7–49.5, GTX 1080 Ti 47.5–48.1 분자/초 |
| CPU 처리량 | 506분자, `DEVICE=cpu` | 0.63–0.74 분자/초 (12분 20초–14분 6초, 서버 부하에 따라 다름) |
| 메모리 (GPU 실행) | 1초 간격 표본: `docker stats` 컨테이너 메모리, 컨테이너 주 프로세스 RSS, `nvidia-smi` 프로세스별 GPU 메모리 | 컨테이너 메모리 최대 0.75–1.00 GiB, RSS 최대 1.27 GiB, GPU 메모리 최대 712 MiB |
| 메모리 (CPU 실행) | 위와 같음 | 컨테이너 메모리 최대 1.16–1.90 GiB |
| 메모리 비교 (묶기 전 이미지) | 같은 조건으로 묶기 전 이미지 측정 | 컨테이너 메모리 최대 0.73–0.75 GiB, RSS 최대 1.05 GiB, GPU 712 MiB |

가중치를 한 파일로 읽기 때문에 시작할 때 최대 메모리(RSS)가 묶기 전보다 약 0.2 GiB
늘었다(1.05 → 1.27 GiB). 태스크 가중치를 모델로 옮긴 즉시 해제하도록 했고, 파일을
메모리 매핑(`mmap=True`)으로 읽는 방식은 오히려 더 많이 써서(로드만 1.26 GiB, 현재
방식 1.10 GiB) 채택하지 않았다. 권장 메모리(최소 4 GiB)에는 영향이 없다.

측정 이미지: 결정성·처리량·메모리는 `sha256:420ee9619c96…`(최종 이미지와 `src/`·가중치가
같고 `tool.yaml`·`README.md`의 측정값 표기만 다름)로 측정했다. 최종 이미지로 골든·보조
시험의 기대 결과가 그대로 일치함을 다시 확인했다(`docs/selftest_report.md`).

## 5. 사례별 파일

각 사례 디렉터리에 입력 파일과 기대 결과 파일이 쌍으로 있다.

* batch 사례: `input.*` → `expected.csv` (`case.json`에 환경 변수·기대 종료 코드)
* serve 사례: `request.json` → `expected.json` (`case.json`에 기대 HTTP 상태)
* job 사례: `input.*`를 `POST /jobs`로 제출 → `GET /jobs/{job_id}` 상태가 끝날 때까지 조회 → `GET /jobs/{job_id}/result` 결과를 `expected.csv`, 최종 상태를 `expected_job.json`과 비교

재실행: `python3 tests/run_tests.py --image <이미지>` (GPU 없으면 `--cpu`).
