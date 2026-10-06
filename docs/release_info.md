# 릴리스 정보 — Chemprop Toxicity Predictor 1.0.0

| 항목 | 값 |
|---|---|
| 소스 저장소 | https://github.com/pzkeung/DrugDevPlatform.git (브랜치 `chemprop`) — **원격 push 대기** |
| 제출 태그 | `chemprop-v1.0.0` |
| **제출 시점 커밋 해시** | `acd0e15915d503a173d909fc7e1e32c465c15869` |
| 컨테이너 이미지 | `pzkeung/bio-synergy-platform:chemprop-1.0.0` (별칭 `:chemprop`) |
| 이미지 ID (로컬 빌드) | `sha256:211474073bfaf2115ae397ad611d6a9daf4aff18de5211af130aac073b7636f6` |
| **레지스트리 digest** | `pzkeung/bio-synergy-platform@sha256:437899eb36eee5ccfeaffe36dc56a0996b8d112ff85c6252862965a254e1da0a` (2026-10-06 push, 태그 `chemprop-1.0.0`·`chemprop` 동일) |
| pull 명령 | `docker pull pzkeung/bio-synergy-platform@sha256:437899eb36eee5ccfeaffe36dc56a0996b8d112ff85c6252862965a254e1da0a` |
| 플랫폼 | linux/amd64 |
| 베이스 이미지 | `nvidia/cuda:12.6.3-cudnn-runtime-ubuntu24.04@sha256:8aef630a54bc5c5146ae5ce68e6af5caa3df0fb690bb91544175c91f307e4356` |
| 가중치 | `models/chemprop_trainset_seed0.pt` SHA-256 `198d8179c7196618c6bcdabffb844760351ec59b880e4a2036faef46879ea462` |
| 자체 시험 | 19/19 일치 (`docs/selftest_report.md`, 2026-10-06) |

이 파일과 `tool.yaml`의 `image.digest` 값은 제출 커밋 이후에 추가되었다. 이미지 안의
`tool.yaml`은 자기 digest를 담을 수 없어 `digest: null`이다.
