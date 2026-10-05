# 릴리스 정보 — ToxKG-GPS Toxicity Predictor 1.0.0

| 항목 | 값 |
|---|---|
| 소스 저장소 | https://github.com/pzkeung/DrugDevPlatform.git (브랜치 `toxkg-gps`) — **원격 push 대기** |
| 제출 태그 | `toxkg-gps-v1.0.0` |
| **제출 시점 커밋 해시** | `4f6e8cd0cf24891193bfe40259111a594d7c1b47` |
| 컨테이너 이미지 | `pzkeung/bio-synergy-platform:toxkg-gps-1.0.0` (별칭 `:toxkg-gps`) |
| 이미지 ID (로컬 빌드) | `sha256:70850f7242171a89f7c791a92c896977042ee7c07339e184fbe33bd44fba9945` |
| **레지스트리 digest** | `pzkeung/bio-synergy-platform@sha256:910c4b58ee1202469bb91f8a8fafbc0a18ada19786f4824888a2820de562cbfc` (2026-10-06 push, 태그 `toxkg-gps-1.0.0`·`toxkg-gps` 동일) |
| pull 명령 | `docker pull pzkeung/bio-synergy-platform@sha256:910c4b58ee1202469bb91f8a8fafbc0a18ada19786f4824888a2820de562cbfc` |
| 플랫폼 | linux/amd64 |
| 베이스 이미지 | `nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04@sha256:85fb7ac694079fff1061a0140fd5b5a641997880e12112d92589c3bbb1e8b7ca` |
| 가중치 | `models/gps_trainset_seed0.pt` SHA-256 `95ac41f79b5ca5476cc040c670ca900569a51ead5daf79e0457162c827a294d4` |
| 자체 시험 | 18/18 일치 (`docs/selftest_report.md`, 2026-10-06) |

이 파일과 `tool.yaml`의 `image.digest` 값은 제출 커밋 이후에 추가되었다. 이미지
안의 `tool.yaml`은 자기 digest를 담을 수 없어 `digest: null`이다.
