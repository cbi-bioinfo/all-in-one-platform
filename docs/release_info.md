# 릴리스 정보 — MTDNN Toxicity Predictor 1.0.0

| 항목 | 값 |
|---|---|
| 소스 저장소 | https://github.com/cbi-bioinfo/all-in-one-platform.git (브랜치 `mtdnn`) — **push 대기** |
| 제출 태그 | `mtdnn-v1.0.0` — **재지정 대기** |
| **제출 시점 커밋 해시** | (push 후 기록) |
| 컨테이너 이미지 | `cbibioinfolab/toxicity-prediction:mtdnn-1.0.0` |
| 이미지 ID (로컬 빌드) | (빌드 후 기록 — `docs/selftest_report.md` 1절) |
| **레지스트리 digest** | (push 후 기록) |
| pull 명령 | `docker pull cbibioinfolab/toxicity-prediction@sha256:<digest>` |
| 플랫폼 | linux/amd64 |
| 베이스 이미지 | `python:3.10-slim@sha256:c1aaf3d03e14944a039a1647e0b3f6f34c6bee517bac6ff380215ee099c4e808` |
| 가중치 체크섬 | `models/SHA256SUMS` |
| 자체 시험 | `docs/selftest_report.md` |

이 파일은 제출 커밋 이후에 갱신한다(커밋 해시와 digest를 기록하기 위함). 이미지
내용은 제출 커밋의 `src/`, `models/`, `tool.yaml`, `README.md`, `LICENSE`,
`NOTICE`, `requirements.lock`, `Dockerfile`로부터 빌드된다.

이전 기록: `pzkeung/bio-synergy-platform:mtdnn-1.0.0`
(`sha256:ad487678f942525a22f7597040338a229c39b7e3b7935afb982d2e0e77567c43`,
커밋 `2841c6c`)은 저장소·이미지 이전 및 작업 API 추가 전 빌드로, 대체되었다.
