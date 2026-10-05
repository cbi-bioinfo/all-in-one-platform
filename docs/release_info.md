# 릴리스 정보 — SSL-GCN Toxicity Predictor 1.0.0

| 항목 | 값 |
|---|---|
| 소스 저장소 | https://github.com/pzkeung/DrugDevPlatform.git (브랜치 `ssl-gcn`) — **원격 push 대기** |
| 제출 태그 | `ssl-gcn-v1.0.0` |
| **제출 시점 커밋 해시** | `4b889fa480e087eb3b082b116032bfd33421e3c2` |
| 컨테이너 이미지 | `pzkeung/bio-synergy-platform:ssl-gcn-1.0.0` (별칭 `:ssl-gcn`) |
| 이미지 ID (로컬 빌드) | `sha256:fe237001b443663a74c40ab5d60558bcc1b438bb3eefe7bb752dec6eff658659` |
| **레지스트리 digest** | `pzkeung/bio-synergy-platform@sha256:1ad8f0e52ff2becaa5991f1e1871e8b28c82222c5315e297de70cb349347ecb2` (2026-10-06 push, 태그 `ssl-gcn-1.0.0`·`ssl-gcn` 동일) |
| pull 명령 | `docker pull pzkeung/bio-synergy-platform@sha256:1ad8f0e52ff2becaa5991f1e1871e8b28c82222c5315e297de70cb349347ecb2` |
| 플랫폼 | linux/amd64 |
| 베이스 이미지 | `nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04@sha256:85fb7ac694079fff1061a0140fd5b5a641997880e12112d92589c3bbb1e8b7ca` |
| 가중치 세트 | `models/SHA256SUMS` (SHA-256 `95e9a2cdd3801bf553c027d13c3a909127286be8c0dcc7d27b241101d85f352b`) — 태스크 모델 601개 |
| 자체 시험 | 16/16 일치 (`docs/selftest_report.md`, 2026-10-06) |

이 파일과 `tool.yaml`의 `image.digest` 값은 제출 커밋 이후에 추가되었다. 이미지
안의 `tool.yaml`은 자기 digest를 담을 수 없어 `digest: null`이다.
