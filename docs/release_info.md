# 릴리스 정보 — FP-GNN Toxicity Predictor 1.0.0

| 항목 | 값 |
|---|---|
| 소스 저장소 | https://github.com/pzkeung/DrugDevPlatform.git (브랜치 `fp-gnn`) — **원격 push 대기** |
| 제출 태그 | `fp-gnn-v1.0.0` |
| **제출 시점 커밋 해시** | `c7aa78dbc065a8e7708a97dbdcf9686ec6ff1d70` |
| 컨테이너 이미지 | `pzkeung/bio-synergy-platform:fp-gnn-1.0.0` (별칭 `:fp-gnn`) |
| 이미지 ID (로컬 빌드) | `sha256:661206e5df7680cef84d75d0f19b5793ba44576b8bbbcbbdc2f429d4e89b635d` |
| **레지스트리 digest** | `pzkeung/bio-synergy-platform@sha256:d5569f21c64badab478a60487671cb70765e82d240c871fd7a7122cf5b52720b` (2026-10-06 push, 태그 `fp-gnn-1.0.0`·`fp-gnn` 동일) |
| pull 명령 | `docker pull pzkeung/bio-synergy-platform@sha256:d5569f21c64badab478a60487671cb70765e82d240c871fd7a7122cf5b52720b` |
| 플랫폼 | linux/amd64 |
| 베이스 이미지 | `nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04@sha256:85fb7ac694079fff1061a0140fd5b5a641997880e12112d92589c3bbb1e8b7ca` |
| 가중치 | `models/fpgnn_trainset_seed0.pt` SHA-256 `5cb842f64c5885ecaa04e03b6657a9b8efac77c78bce387ff130226ee1022d3a` |
| 자체 시험 | 18/18 일치 (`docs/selftest_report.md`, 2026-10-06) |

이 파일과 `tool.yaml`의 `image.digest` 값은 제출 커밋 이후에 추가되었다. 이미지 안의
`tool.yaml`은 자기 digest를 담을 수 없어 `digest: null`이다.
