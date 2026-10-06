# 릴리스 정보 — ToxKG-GPS Toxicity Predictor 1.0.0

| 항목 | 값 |
|---|---|
| 소스 저장소 | https://github.com/cbi-bioinfo/all-in-one-platform.git (브랜치 `toxkg-gps`) |
| 제출 태그 | `toxkg-gps-v1.0.0` |
| **제출 시점 커밋 해시** | `e60f13ff271e9e688a8b835ebd1d19195e440491` (태그 `toxkg-gps-v1.0.0`) |
| 컨테이너 이미지 | `cbibioinfolab/toxicity-prediction:toxkg-gps-1.0.0` |
| 이미지 ID (로컬 빌드) | `sha256:7a85f0dc60dbfb65b1ca001bd51841d187e5a7a6d96ee5e13b85307510fae226` |
| **레지스트리 digest** | `cbibioinfolab/toxicity-prediction@sha256:3f7f1f607c419da46a132f8cddf36d5844dd3361ed2285f31bd86125540477db` (2026-10-06 push) |
| pull 명령 | `docker pull cbibioinfolab/toxicity-prediction@sha256:3f7f1f607c419da46a132f8cddf36d5844dd3361ed2285f31bd86125540477db` |
| 플랫폼 | linux/amd64 |
| 베이스 이미지 | `nvidia/cuda:11.8.0-cudnn8-runtime-ubuntu22.04@sha256:85fb7ac694079fff1061a0140fd5b5a641997880e12112d92589c3bbb1e8b7ca` |
| 가중치 | `models/toxkggps_pretrained.pt` SHA-256 `95ac41f79b5ca5476cc040c670ca900569a51ead5daf79e0457162c827a294d4` (이전 파일명 `gps_trainset_seed0.pt`, 내용 동일) |
| 자체 시험 | 24/24 일치 (`docs/selftest_report.md`, 2026-10-06, 위 이미지 ID) |

이 파일과 `tool.yaml`의 `image.digest`는 제출 커밋 이후에 갱신했다(이미지 push로
digest가 정해진 뒤 기록하기 위함). 태그 `toxkg-gps-v1.0.0`은 이미지를 빌드한 제출
커밋을 가리키며, 이미지 내용은 그 커밋의 `src/`, `models/`, `tool.yaml`,
`README.md`, `requirements.lock`, `Dockerfile`로부터 빌드되었다.

이전 기록: `pzkeung/bio-synergy-platform:toxkg-gps-1.0.0`
(`sha256:910c4b58ee1202469bb91f8a8fafbc0a18ada19786f4824888a2820de562cbfc`,
커밋 `4f6e8cd`)은 저장소·이미지 이전, 가중치 파일명 변경, 작업 API 추가 전 빌드로, 대체되었다.
