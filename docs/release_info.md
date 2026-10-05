# 릴리스 정보 — SE-MTDNN Toxicity Predictor 1.0.0

| 항목 | 값 |
|---|---|
| 소스 저장소 | https://github.com/pzkeung/DrugDevPlatform.git (브랜치 `mtdnn`) — **원격 push 대기** |
| 제출 태그 | `mtdnn-v1.0.0` |
| **제출 시점 커밋 해시** | `2841c6c7428c0b11c32df18cc5e25bb0c85abed0` |
| 컨테이너 이미지 | `pzkeung/bio-synergy-platform:mtdnn-1.0.0` (별칭 `:mtdnn`) |
| 이미지 ID (로컬 빌드) | `sha256:a678943f6619046550792a21667ef7b956bf8cd15328a073b635d6c2b0d6f688` |
| 레지스트리 digest | push 후 기입 — `docker inspect --format '{{index .RepoDigests 0}}' pzkeung/bio-synergy-platform:mtdnn-1.0.0` |
| 플랫폼 | linux/amd64 |
| 베이스 이미지 | `python:3.10-slim@sha256:c1aaf3d03e14944a039a1647e0b3f6f34c6bee517bac6ff380215ee099c4e808` |
| 가중치 체크섬 | `models/SHA256SUMS` |
| 자체 시험 | 15/15 일치 (`docs/selftest_report.md`, 2026-10-06) |

이 파일은 제출 커밋 이후에 추가되었다(커밋 해시를 기록하기 위함). 이미지 내용은
제출 커밋의 `src/`, `models/`, `tool.yaml`, `README.md`, `requirements.lock`,
`Dockerfile`로부터 빌드되었다.
