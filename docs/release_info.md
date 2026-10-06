# 릴리스 정보 — GROVER Toxicity Predictor 1.0.0

| 항목 | 값 |
|---|---|
| 소스 저장소 | https://github.com/cbi-bioinfo/all-in-one-platform.git (브랜치 `grover`) |
| 제출 태그 | `grover-v1.0.0` |
| **제출 시점 커밋 해시** | (push 후 기록) |
| 컨테이너 이미지 | `cbibioinfolab/toxicity-prediction:grover-1.0.0` |
| 이미지 ID (로컬 빌드) | (빌드 후 기록 — `docs/selftest_report.md` 1절) |
| **레지스트리 digest** | (push 후 기록) |
| pull 명령 | `docker pull cbibioinfolab/toxicity-prediction@sha256:<digest>` |
| 플랫폼 | linux/amd64 |
| 베이스 이미지 | `nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04@sha256:85fb7ac694079fff1061a0140fd5b5a641997880e12112d92589c3bbb1e8b7ca` |
| 가중치 | `models/grover_pretrained.pt` SHA-256 `2d6a3350a2d665dfa552427ba1b6f60cf2f07635641c2a7718f254d16076fc9e` (이전 파일명 `grover_trainset_seed2.pt`, 내용 동일) |
| 자체 시험 | `docs/selftest_report.md` |

이 파일과 `tool.yaml`의 `image.digest`는 제출 커밋 이후에 갱신한다(이미지 push로
digest가 정해진 뒤 기록하기 위함). 태그 `grover-v1.0.0`은 이미지를 빌드한 제출
커밋을 가리키며, 이미지 내용은 그 커밋의 `src/`, `models/`, `tool.yaml`,
`README.md`, `LICENSE`, `requirements.lock`, `Dockerfile`로부터 빌드된다.

이전 기록: `pzkeung/bio-synergy-platform:grover-1.0.0`
(`sha256:31b6b974b82bac858e5054fd0f545aef52bc1d64237a3a16eeea46140d6c8675`,
커밋 `d4e809d`)은 저장소·이미지 이전, 가중치 파일명 변경, 작업 API 추가 전 빌드로, 대체되었다.
