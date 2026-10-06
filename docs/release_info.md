# 릴리스 정보 — GROVER Toxicity Predictor 1.0.0

| 항목 | 값 |
|---|---|
| 소스 저장소 | https://github.com/pzkeung/DrugDevPlatform.git (브랜치 `grover`) — **원격 push 대기** |
| 제출 태그 | `grover-v1.0.0` |
| **제출 시점 커밋 해시** | `d4e809df28ed6e76bc7963d78ae3274ebeeb2952` |
| 컨테이너 이미지 | `pzkeung/bio-synergy-platform:grover-1.0.0` (별칭 `:grover`) |
| 이미지 ID (로컬 빌드) | `sha256:2ea4340cc150bdda550a580eff5c20d5a4798699dcdce1f31b1525b98151b769` |
| **레지스트리 digest** | `pzkeung/bio-synergy-platform@sha256:31b6b974b82bac858e5054fd0f545aef52bc1d64237a3a16eeea46140d6c8675` (2026-10-06 push, 두 태그 동일) |
| pull 명령 | `docker pull pzkeung/bio-synergy-platform@sha256:31b6b974b82bac858e5054fd0f545aef52bc1d64237a3a16eeea46140d6c8675` |
| 플랫폼 | linux/amd64 |
| 베이스 이미지 | `nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04@sha256:85fb7ac694079fff1061a0140fd5b5a641997880e12112d92589c3bbb1e8b7ca` |
| 가중치 | `models/grover_trainset_seed2.pt` SHA-256 `2d6a3350a2d665dfa552427ba1b6f60cf2f07635641c2a7718f254d16076fc9e` |
| 자체 시험 | 20/20 일치 (`docs/selftest_report.md`, 2026-10-06) |

이 파일과 `tool.yaml`의 `image.digest` 값은 제출 커밋 이후에 추가되었다. 이미지 안의
`tool.yaml`은 자기 digest를 담을 수 없어 `digest: null`이다.
