# 참조 데이터 명세

## 1. 실행 시 필요한 참조 데이터 (이미지에 포함)

| 이름 | 종류 | 경로 | 용량 | 출처 | 라이선스 |
|---|---|---|--:|---|---|
| 모델 설정·태스크 목록 | JSON | `models/chemprop_trainset_seed0_config.json` | 17,410 B | 본 과제 학습 산출물 (631개 태스크 이름, 출력 순서) | MIT (`LICENSE`) |
| 원자·결합 특징 정의 | Python 소스 | `src/chemprop/featurizers/` (chemprop 2.3.1) | — | Chemprop 개발팀 | MIT |

모델 가중치는 `models/README.md`에 정리했다. 추론에는 그 밖의 데이터베이스, 사전 계산
값, 외부 서비스가 필요 없다(chemprop의 선택 기능인 RDKit 2D 기술자 등 추가 분자
특징은 이 모델에서 쓰지 않는다).

## 2. 학습 데이터 (trainset) — 패키지에 포함하지 않음

| 데이터셋 | 원 출처 | 사용 판본 | 분자 / 태스크 | 원자료 파일 | 라이선스·이용 조건 |
|---|---|---|--:|---|---|
| Tox21 | NIH NCATS · US EPA · NTP, Tox21 Data Challenge 2014 (https://tripod.nih.gov/tox21/challenge/) | MoleculeNet (Wu et al., Chem. Sci. 2018), `https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/tox21.csv.gz` | 7,831 / 12 | `tox21.csv` 525,119 B | 미국 연방정부 생산 데이터(공공 영역으로 간주). MoleculeNet 재배포본에는 별도 데이터 라이선스 표기가 없음 |
| ToxCast | US EPA ToxCast 프로그램 (invitrodb) | MoleculeNet, `.../datasets/toxcast_data.csv.gz` | 8,577 / 617 | `toxcast_data.csv` 10,281,259 B | 미국 연방정부 생산 데이터(공공 영역으로 간주). 재배포본 라이선스 표기 없음 |
| ClinTox | Gayvert K.M. et al., Cell Chem. Biol. 23, 1294 (2016), doi:10.1016/j.chembiol.2016.07.023 | MoleculeNet, `.../datasets/clintox.csv.gz` | 1,461 / 2 | `clintox.csv` 95,512 B | **명시적 데이터 라이선스 확인되지 않음** — 학술 공개 데이터 |

병합본(trainset): 10,974 분자 × 631 태스크. 원 플랫폼 내부 명칭은 `golden`
(`data/tox_pred/golden/`)이며, 본 제출물에서는 시험용 골든 데이터셋과 구분하기 위해
**trainset**으로 부른다. 학습 환경 RDKit(2026.3.6)이 파싱하지 못하는 8개 분자
(`[AlH3]` 알루미늄 착물)는 학습에서 제외되었다.

## 3. 시험 데이터 (`tests/`)

입력 SMILES는 trainset 분할 seed 0의 **test 분할**(학습에 쓰지 않은 506분자)에서
골랐다. 예외: S9의 알루미늄 착물(`trainset_001132`), S11의 요오드화칼륨
(`trainset_000047`)은 trainset 분자이고, S10의 시스플라틴 두 표기와 S12의 원소 시험
분자는 경계 시험을 위해 직접 작성한 구조다. 일부 사례는 오류·경계 시험을 위해 SMILES를
변형했다. 라벨은 포함하지 않는다.

분자 ID 표기:

* `testset_<번호>` — test 분할 분자. 번호는 trainset(병합본)의 분자 번호다.
* `testset_<번호>_<변형>` — 오류·경계 시험을 위해 그 분자의 SMILES를 일부러 바꾼 입력
  (고리 번호 제거, 전하 표기 제거, 입체 표기 제거).
* `trainset_<번호>` — test 분할 밖(train 분할)의 분자. 위 예외 사례에만 쓴다.

골든 데이터셋의 범주별 분자 수는 정상 12(N1–N3), 경계 12(B1–B2), 오류 3(E1–E2)이다.
B1은 원래 serve 요청당 최대 건수(100건) 시험이었으며, 그 100건 사례는 보충 사례로 옮기고
B1에는 그중 경계 대표 10건만 남겼다(기대 결과도 원 사례에서 그대로 추출).
