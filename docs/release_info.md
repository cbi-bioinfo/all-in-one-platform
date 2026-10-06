# 릴리스 정보 — SSL-GCN Toxicity Predictor 1.0.0

| 항목 | 값 |
|---|---|
| 소스 저장소 | https://github.com/cbi-bioinfo/all-in-one-platform.git (브랜치 `ssl-gcn`) |
| 제출 태그 | `ssl-gcn-v1.0.0` |
| **제출 시점 커밋 해시** | `6efad3ee5c2088ad5d8d836a96badb51f92d0da8` (태그 `ssl-gcn-v1.0.0`) |
| 컨테이너 이미지 | `cbibioinfolab/toxicity-prediction:ssl-gcn-1.0.0` |
| 이미지 ID (로컬 빌드) | `sha256:9c8b13a2cde27b45b7d859bdbcc2c4694e303ded308872b544545870e2ebf5b2` |
| **레지스트리 digest** | `cbibioinfolab/toxicity-prediction@sha256:b2bcb1087798bff7e196dca892f27d167f9116eb47104afedfe5917a592f7870` (2026-10-06 push) |
| pull 명령 | `docker pull cbibioinfolab/toxicity-prediction@sha256:b2bcb1087798bff7e196dca892f27d167f9116eb47104afedfe5917a592f7870` |
| 플랫폼 | linux/amd64 |
| 베이스 이미지 | `nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04@sha256:85fb7ac694079fff1061a0140fd5b5a641997880e12112d92589c3bbb1e8b7ca` |
| 가중치 | `models/sslgcn_pretrained.pt` (SHA-256 `c8cdf79e0f39a408f82893d6016c5e41ca1645f4775ddd1b468fb3d7958eeae7`) — 태스크 모델 601개 묶음 |
| 자체 시험 | 21/21 일치 (`docs/selftest_report.md`, 2026-10-06, 위 이미지 ID) |

이 파일과 `tool.yaml`의 `image.digest`는 제출 커밋 이후에 갱신했다(이미지 push로
digest가 정해진 뒤 기록하기 위함). 태그 `ssl-gcn-v1.0.0`은 이미지를 빌드한 제출
커밋을 가리키며, 이미지 내용은 그 커밋의 `src/`, `models/`, `tool.yaml`,
`README.md`, `requirements.lock`, `Dockerfile`로부터 빌드되었다.

이전 기록: `pzkeung/bio-synergy-platform:ssl-gcn-1.0.0`
(`sha256:1ad8f0e52ff2becaa5991f1e1871e8b28c82222c5315e297de70cb349347ecb2`,
커밋 `4b889fa`)은 저장소·이미지 이전, 가중치 묶음, 작업 API 추가 전 빌드로, 대체되었다.
같은 날 먼저 push한 `cbibioinfolab/toxicity-prediction:ssl-gcn-1.0.0`
(`sha256:b84b47a24e426f912bb84474a099e3b8b68916bd403a79895ee242c13660c2f4`, 커밋 `7e069d6`)은
자원 재측정과 메모리 해제 수정 전 빌드로, 같은 태그로 대체되었다.
