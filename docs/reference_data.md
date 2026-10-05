# 참조 데이터 명세

## 1. 실행 시 필요한 참조 데이터 (이미지에 포함)

| 이름 | 종류 | 경로 | 용량 | 출처 | 라이선스 |
|---|---|---|--:|---|---|
| 모델 구조 설정·태스크 목록 | JSON | `models/gps_trainset_seed0_config.json` | 17,250 B | 본 과제 학습 산출물 (구조 값과 631개 태스크 출력 순서) | 미기재 |

모델 가중치(`models/gps_trainset_seed0.pt`)는 `models/README.md`에 정리했다. 원자·결합
특징은 RDKit 원자·결합 속성에서 바로 계산하므로 별도 사전·어휘·사전 계산 값이 없다.

**지식그래프 데이터는 쓰지 않는다.** 원 플랫폼의 `models/tox_pred/toxkg/data/KG/`
(ToxKG 저장소가 배포한 R-GCN용 유전자·경로·트리플 파일, 약 205 MB)는 이 모델의 학습과
추론 어디에도 쓰이지 않으며 패키지에 포함하지 않았다. 추론에는 외부 서비스나
데이터베이스(Neo4j 등)도 필요 없다.

## 2. 학습 데이터 (trainset) — 패키지에 포함하지 않음

| 데이터셋 | 원 출처 | 사용 판본 | 분자 / 태스크 | 원자료 파일 | 라이선스·이용 조건 |
|---|---|---|--:|---|---|
| Tox21 | NIH NCATS · US EPA · NTP, Tox21 Data Challenge 2014 (https://tripod.nih.gov/tox21/challenge/) | MoleculeNet (Wu et al., Chem. Sci. 2018), `https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/tox21.csv.gz` | 7,831 / 12 | `tox21.csv` 525,119 B | 미국 연방정부 생산 데이터(공공 영역으로 간주). MoleculeNet 재배포본에는 별도 데이터 라이선스 표기가 없음 |
| ToxCast | US EPA ToxCast 프로그램 (invitrodb) | MoleculeNet, `.../datasets/toxcast_data.csv.gz` | 8,577 / 617 | `toxcast_data.csv` 10,281,259 B | 미국 연방정부 생산 데이터(공공 영역으로 간주). 재배포본 라이선스 표기 없음 |
| ClinTox | Gayvert K.M. et al., Cell Chem. Biol. 23, 1294 (2016), doi:10.1016/j.chembiol.2016.07.023 | MoleculeNet, `.../datasets/clintox.csv.gz` | 1,461 / 2 | `clintox.csv` 95,512 B | **명시적 데이터 라이선스 확인되지 않음** — 학술 공개 데이터. 재배포 시 원저자 확인 필요 |

병합본(trainset): 10,974 분자 × 631 태스크. 원 플랫폼에서의 내부 명칭은 `golden`
(경로 `data/tox_pred/golden/`)이며, 본 제출물에서는 시험용 골든 데이터셋과 구분하기
위해 **trainset**으로 부른다. 학습 환경 RDKit(2026.3.2)에서 파싱되지 않는 8개 분자
(알루미늄 착물)는 학습에서 빠졌다.

## 3. 시험 데이터 (`tests/`)

* `tests/golden/`과 대부분의 `tests/cases/` 입력 SMILES는 trainset 분할 seed 0의 **test
  분할**(학습에 쓰지 않은 506분자)에서 골랐다. 일부는 오류·경계 시험을 위해 변형했다
  (고리 번호 제거, 전하 표기 제거, 입체 표기 제거).
* 예외: S9 `trainset_001132`(알루미늄 착물)와 S11 `trainset_000047`(KI)은 test 분할
  밖의 trainset 분자이고, S10의 시스플라틴 두 표기는 시험용으로 직접 작성한 입력이다
  (seed 0 test 분할에 결합이 없는 분자나 비표준 결합을 가진 분자가 없어서다).
* 분자 ID는 `trainset_<번호>`로 표기했다. 라벨은 포함하지 않는다.
