# 참조 데이터 명세

## 1. 실행 시 필요한 데이터 (이미지에 포함)

| 이름 | 종류 | 경로 | 용량 | 출처 | 라이선스 |
|---|---|---|--:|---|---|
| 미세조정 체크포인트 | PyTorch 체크포인트(args·state_dict) | `models/grover_pretrained.pt` | 195,924,310 B | 본 과제 학습 산출물(업스트림 GROVER-base에서 미세조정) | MIT(업스트림 GROVER, 4절) |
| 태스크 목록·구조 요약 | JSON | `models/grover_pretrained_config.json` | 17,538 B | 본 과제 | MIT |
| 원자 특징 SMARTS 패턴 | 소스 코드 상수 | `src/grover/data/molgraph.py` | — | GROVER(chemprop 유래) | MIT |

사전학습 체크포인트 `grover_base.pt`(업스트림 공개본)의 가중치는 미세조정 체크포인트 안에
이미 들어 있어 별도로 필요하지 않으며 포함하지 않는다. 추가 특징 생성기(RDKit 2D 기술자 등)는
쓰지 않는다(`features_generator=None`).

## 2. 학습 데이터 (trainset) — 포함하지 않음

| 데이터셋 | 원 출처 | 사용 판본 | 분자 / 태스크 | 라이선스·이용 조건 |
|---|---|---|--:|---|
| Tox21 | NIH NCATS · US EPA · NTP, Tox21 Data Challenge 2014 | MoleculeNet(Wu et al., 2018), `deepchemdata.s3-us-west-1.amazonaws.com/datasets/tox21.csv.gz` (525,119 B) | 7,831 / 12 | 미국 연방정부 생산 데이터(공공 영역으로 간주). 재배포본에 별도 라이선스 표기 없음 |
| ToxCast | US EPA ToxCast | MoleculeNet, `toxcast_data.csv.gz` (10,281,259 B) | 8,577 / 617 | 위와 같음 |
| ClinTox | Gayvert K.M. et al., Cell Chem. Biol. 23, 1294 (2016) | MoleculeNet, `clintox.csv.gz` (95,512 B) | 1,461 / 2 | **명시적 데이터 라이선스 확인되지 않음** — 재배포 시 원저자 확인 필요 |
| GROVER 사전학습 데이터 | ZINC15·ChEMBL 비표지 분자(업스트림 논문) | 업스트림 `grover_base.pt`에 반영 | 약 1,100만 분자(논문 기재) | 업스트림 공개 가중치를 MIT로 사용 |

병합본 trainset: 10,974 분자 × 631 태스크(원 플랫폼 내부 명칭 `golden`, 경로
`data/tox_pred/golden/`). 본 제출물에서는 시험용 골든 데이터셋과 구분하기 위해 trainset으로 부른다.

## 3. 시험 데이터 (`tests/`)

입력 SMILES는 trainset 분할 seed 2의 test 분할(1,104분자, 학습 미사용)에서 골랐다. 예외:
S10(시스플라틴 표기 예), S11(`[I-].[K+]`, trainset 분자), S12(전하·원소 경계 인공 예),
S3·S4(형식 오류 예). 오류·경계 시험을 위해 일부 SMILES를 변형했다. 라벨은 포함하지 않는다.

분자 ID 표기:

* `testset_<번호>` — test 분할 분자. 번호는 trainset(병합본)의 분자 번호다.
* `testset_<번호>_<변형>` — 오류·경계 시험을 위해 그 분자의 SMILES를 일부러 바꾼 입력
  (고리 번호 제거, 전하 표기 제거, 입체 표기 변경).
* `trainset_<번호>` — test 분할 밖(train 분할)의 분자. 위 예외 사례에만 쓴다.

골든 데이터셋의 범주별 분자 수는 정상 12(N1–N3), 경계 13(B1–B2), 오류 3(E1–E2)이다.
B1은 원래 serve 요청당 최대 건수(100건) 시험이었으며, 그 100건 사례는 보충 사례로 옮기고
B1에는 그중 경계 대표 10건만 남겼다(기대 결과도 원 사례에서 그대로 추출).
