# 릴리스 정보 — MTDNN Toxicity Predictor 1.0.0

| 항목 | 값 |
|---|---|
| 소스 저장소 | https://github.com/cbi-bioinfo/all-in-one-platform.git (브랜치 `mtdnn`) |
| 제출 태그 | `mtdnn-v1.0.0` |
| **제출 시점 커밋 해시** | `a38025ae5096ad9b200336c45bb78c272c6bfdc0` (태그 `mtdnn-v1.0.0`) |
| 컨테이너 이미지 | `cbibioinfolab/toxicity-prediction:mtdnn-1.0.0` |
| 이미지 ID (로컬 빌드) | `sha256:7d0ce779100f85ceed27e490a11b86fcb9a812727dd1b7e3a7597ac3c5b5696a` |
| **레지스트리 digest** | `cbibioinfolab/toxicity-prediction@sha256:a0df0d88552a16459ae6666e3a13932e99aab5e6273bbbf1205ab2b2b670d77c` (2026-10-06 push) |
| pull 명령 | `docker pull cbibioinfolab/toxicity-prediction@sha256:a0df0d88552a16459ae6666e3a13932e99aab5e6273bbbf1205ab2b2b670d77c` |
| 플랫폼 | linux/amd64 |
| 베이스 이미지 | `python:3.10-slim@sha256:c1aaf3d03e14944a039a1647e0b3f6f34c6bee517bac6ff380215ee099c4e808` |
| 가중치 체크섬 | `models/SHA256SUMS` |
| 자체 시험 | 21/21 일치 (`docs/selftest_report.md`, 2026-10-06, 위 이미지 ID) |

이 파일과 `tool.yaml`의 `image.digest`는 제출 커밋 이후에 갱신했다(이미지 push로
digest가 정해진 뒤 기록하기 위함). 태그 `mtdnn-v1.0.0`은 이미지를 빌드한 제출
커밋을 가리키며, 이미지 내용은 그 커밋의 `src/`, `models/`, `tool.yaml`,
`README.md`, `LICENSE`, `NOTICE`, `requirements.lock`, `Dockerfile`로부터 빌드되었다.

이전 기록: `pzkeung/bio-synergy-platform:mtdnn-1.0.0`
(`sha256:ad487678f942525a22f7597040338a229c39b7e3b7935afb982d2e0e77567c43`,
커밋 `2841c6c`)은 저장소·이미지 이전 및 작업 API 추가 전 빌드로, 대체되었다.
