# 릴리스 정보 — FP-GNN Toxicity Predictor 1.0.0

| 항목 | 값 |
|---|---|
| 소스 저장소 | https://github.com/cbi-bioinfo/all-in-one-platform.git (브랜치 `fp-gnn`) |
| 제출 태그 | `fp-gnn-v1.0.0` |
| **제출 시점 커밋 해시** | `9bf1a31a4ff167a44150596d9da8f97b8aa1dea7` (태그 `fp-gnn-v1.0.0`) |
| 컨테이너 이미지 | `cbibioinfolab/toxicity-prediction:fp-gnn-1.0.0` |
| 이미지 ID (로컬 빌드) | `sha256:bfbbf4561f1030a46d35f30a8f03c83cdd9b65b52601f71c8da2b1ecafe5cbc9` |
| **레지스트리 digest** | `cbibioinfolab/toxicity-prediction@sha256:175d4271b095d689b8972fd1c4a920b8b16493d39de118acf997e99eb73f4f67` (2026-10-06 push) |
| pull 명령 | `docker pull cbibioinfolab/toxicity-prediction@sha256:175d4271b095d689b8972fd1c4a920b8b16493d39de118acf997e99eb73f4f67` |
| 플랫폼 | linux/amd64 |
| 베이스 이미지 | `nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04@sha256:85fb7ac694079fff1061a0140fd5b5a641997880e12112d92589c3bbb1e8b7ca` |
| 가중치 | `models/fpgnn_pretrained.pt` SHA-256 `5cb842f64c5885ecaa04e03b6657a9b8efac77c78bce387ff130226ee1022d3a` (이전 파일명 `fpgnn_trainset_seed0.pt`, 내용 동일) |
| 자체 시험 | 24/24 일치 (`docs/selftest_report.md`, 2026-10-06, 위 이미지 ID) |

이 파일과 `tool.yaml`의 `image.digest`는 제출 커밋 이후에 갱신했다(이미지 push로
digest가 정해진 뒤 기록하기 위함). 태그 `fp-gnn-v1.0.0`은 이미지를 빌드한 제출
커밋을 가리키며, 이미지 내용은 그 커밋의 `src/`, `models/`, `tool.yaml`,
`README.md`, `requirements.lock`, `Dockerfile`로부터 빌드되었다.

이전 기록: `pzkeung/bio-synergy-platform:fp-gnn-1.0.0`
(`sha256:d5569f21c64badab478a60487671cb70765e82d240c871fd7a7122cf5b52720b`,
커밋 `c7aa78d`)은 저장소·이미지 이전, 가중치 파일명 변경, 작업 API 추가 전 빌드로, 대체되었다.
