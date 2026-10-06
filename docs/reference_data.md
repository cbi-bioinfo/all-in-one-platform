# 참조 데이터 명세

## 1. 실행 시 필요한 참조 데이터 (이미지에 포함)

| 이름 | 종류 | 경로 | 용량 | 출처 | 라이선스 |
|---|---|---|--:|---|---|
| MTDNN 가중치 | PyTorch 체크포인트 (dict: `state_dict`, `tasks`, `emb_dim`, `epoch`, `val_loss`, `run_id`) | `models/mtdnn_pretrained.pt` | 1,677,343,497 B | 본 과제 학습 산출물 (trainset 홀드아웃 seed 0, `docs/model_card.md`) | Apache-2.0 |
| SE 인코더 가중치 | PyTorch state_dict | `models/se_encoder/model.pt` | 50,302,643 B | IBM/multitask-toxicity `SE_featurization/models/` (원 논문 공개본, 바이트 단위 동일) | Apache-2.0 |
| SE 인코더 설정 | pickle (`argparse.Namespace`) | `models/se_encoder/config.nb` | 3,114 B | 위와 같음 | Apache-2.0 |
| SE 토크나이저 어휘 | pickle (`CharVocab`, 39 토큰) | `models/se_encoder/vocab.nb` | 7,151 B | 위와 같음 | Apache-2.0 |
| SE 인코더 코드 | Python 소스 | `src/moses/` | 약 100 KB | IBM/multitask-toxicity `SE_featurization/moses/` (MOSES 유래 부분 포함), 수정 없이 포함 | Apache-2.0 / MIT (`NOTICE`) |

가중치 파일은 용량 때문에 소스 저장소에 넣지 않고 이미지에만 포함한다(빌드 시
배치 방법은 `docs/deployment.md` 1.1절). 체크섬은 `models/SHA256SUMS`에 있다.
추론에는 그 밖의 데이터베이스, 사전 계산 임베딩, 외부 서비스가 필요 없다.

## 2. 학습 데이터 (trainset) — 패키지에 포함하지 않음

모델 학습에만 사용했고 이미지·저장소에는 들어 있지 않다.

| 데이터셋 | 원 출처 | 사용 판본 | 분자 / 태스크 | 원자료 파일 | 라이선스·이용 조건 |
|---|---|---|--:|---|---|
| Tox21 | NIH NCATS · US EPA · NTP, Tox21 Data Challenge 2014 (https://tripod.nih.gov/tox21/challenge/) | MoleculeNet (Wu et al., Chem. Sci. 2018), `https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/tox21.csv.gz` | 7,831 / 12 | `tox21.csv` 525,119 B | 미국 연방정부 생산 데이터(공공 영역으로 간주). MoleculeNet 재배포본에는 별도 데이터 라이선스 표기가 없음 |
| ToxCast | US EPA ToxCast 프로그램 (invitrodb) | MoleculeNet, `.../datasets/toxcast_data.csv.gz` | 8,577 / 617 | `toxcast_data.csv` 10,281,259 B | 미국 연방정부 생산 데이터(공공 영역으로 간주). 재배포본 라이선스 표기 없음 |
| ClinTox | Gayvert K.M. et al., Cell Chem. Biol. 23, 1294 (2016), doi:10.1016/j.chembiol.2016.07.023 (FDA 승인 약물 + 임상시험 독성 실패 약물) | MoleculeNet, `.../datasets/clintox.csv.gz` | 1,461 / 2 | `clintox.csv` 95,512 B | **명시적 데이터 라이선스 확인되지 않음** — 학술 공개 데이터. 재배포 시 원저자 확인 필요 |

병합본(trainset): 10,974 분자 × 631 태스크. 병합·분할 방법은 `docs/model_card.md` 2절.
원 플랫폼에서의 내부 명칭은 `golden`(경로 `data/tox_pred/golden/`)이며, 본
제출물에서는 시험용 골든 데이터셋과 구분하기 위해 **trainset**으로 부른다.

## 3. 시험 데이터 (`tests/`)

`tests/golden/`과 `tests/cases/`의 입력 SMILES는 trainset 분할 seed 0의 **test
분할**(학습에 쓰지 않은 506분자)에서 골랐다. 일부 사례는 오류·경계 시험을 위해
해당 SMILES를 변형했다(고리 번호 제거, 전하 표기 제거, 입체 표기 제거). 분자
ID는 `trainset_<번호>`로 표기했다. 라벨은 포함하지 않는다.
