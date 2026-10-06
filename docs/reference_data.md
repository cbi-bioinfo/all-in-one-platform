# 참조 데이터 명세

## 1. 실행 시 필요한 참조 데이터 (이미지에 포함)

| 이름 | 종류 | 경로 | 용량 | 출처 | 라이선스 |
|---|---|---|--:|---|---|
| 모델 가중치 묶음 | PyTorch 파일 (dict: `tasks`, `tasks_without_model`, `note`, `config`, `state_dicts`) | `models/sslgcn_pretrained.pt` | 240,980,132 B | 본 과제 학습 산출물 (trainset holdout seed 0, 601개 태스크 모델과 공통 설정, 태스크 순서·모델 없는 30개 태스크 목록 포함) | 미기재 |
| 원자 특징화기 정의 | 라이브러리 코드 | dgllife 0.3.2 `CanonicalAtomFeaturizer` (pip 패키지) | — | DGL-LifeSci | Apache-2.0 |

가중치 파일은 용량 때문에 소스 저장소에 넣지 않고 이미지에만 포함한다(빌드 시
배치 방법은 `docs/deployment.md` 1.1절). 체크섬은 `models/SHA256SUMS`에 있다.
추론에는 그 밖의 데이터베이스, 사전 계산 값, 외부 서비스가 필요 없다.

## 2. 학습 데이터 (trainset) — 패키지에 포함하지 않음

| 데이터셋 | 원 출처 | 사용 판본 | 분자 / 태스크 | 원자료 파일 | 라이선스·이용 조건 |
|---|---|---|--:|---|---|
| Tox21 | NIH NCATS · US EPA · NTP, Tox21 Data Challenge 2014 (https://tripod.nih.gov/tox21/challenge/) | MoleculeNet (Wu et al., Chem. Sci. 2018), `https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/tox21.csv.gz` | 7,831 / 12 | `tox21.csv` 525,119 B | 미국 연방정부 생산 데이터(공공 영역으로 간주). MoleculeNet 재배포본에는 별도 데이터 라이선스 표기가 없음 |
| ToxCast | US EPA ToxCast 프로그램 (invitrodb) | MoleculeNet, `.../datasets/toxcast_data.csv.gz` | 8,577 / 617 | `toxcast_data.csv` 10,281,259 B | 미국 연방정부 생산 데이터(공공 영역으로 간주). 재배포본 라이선스 표기 없음 |
| ClinTox | Gayvert K.M. et al., Cell Chem. Biol. 23, 1294 (2016), doi:10.1016/j.chembiol.2016.07.023 | MoleculeNet, `.../datasets/clintox.csv.gz` | 1,461 / 2 | `clintox.csv` 95,512 B | **명시적 데이터 라이선스 확인되지 않음** — 학술 공개 데이터. 재배포 시 원저자 확인 필요 |

병합본(trainset): 10,974 분자 × 631 태스크. 원 플랫폼에서의 내부 명칭은 `golden`
(경로 `data/tox_pred/golden/`)이며, 본 제출물에서는 시험용 골든 데이터셋과 구분하기
위해 **trainset**으로 부른다. 학습 환경 RDKit(2026.3.1)에서 파싱되지 않는 8개
분자(알루미늄 착물)는 SSL-GCN 학습 그래프에서 제외되었다.

## 3. 시험 데이터 (`tests/`)

입력 SMILES는 trainset 분할 seed 0의 **test 분할**(학습에 쓰지 않은 506분자)에서
골랐다(S9의 알루미늄 착물은 trainset 분자 `trainset_001132`). 일부 사례는 오류·경계
시험을 위해 SMILES를 변형했다(고리 번호 제거, 전하 표기 제거, 입체 표기 제거).
분자 ID는 `trainset_<번호>`로 표기했다. 라벨은 포함하지 않는다.
