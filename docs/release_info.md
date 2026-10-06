# 릴리스 정보 — Chemprop Toxicity Predictor 1.0.0

| 항목 | 값 |
|---|---|
| 소스 저장소 | https://github.com/cbi-bioinfo/all-in-one-platform.git (브랜치 `chemprop`) |
| 제출 태그 | `chemprop-v1.0.0` |
| **제출 시점 커밋 해시** | `35b8b5b3d34f7b7b529eb915e0c22b1304686c11` (태그 `chemprop-v1.0.0`) |
| 컨테이너 이미지 | `cbibioinfolab/toxicity-prediction:chemprop-1.0.0` |
| 이미지 ID (로컬 빌드) | `sha256:80fd9edc2921515e1423dbd6681202a3e3f98488665c5a0da64adbba7b9f2fdd` |
| **레지스트리 digest** | `cbibioinfolab/toxicity-prediction@sha256:7faa009eba9da06421784c345089d9c2f85eb0a621ff2f85ddd64e075ca97e61` (2026-10-06 push) |
| pull 명령 | `docker pull cbibioinfolab/toxicity-prediction@sha256:7faa009eba9da06421784c345089d9c2f85eb0a621ff2f85ddd64e075ca97e61` |
| 플랫폼 | linux/amd64 |
| 베이스 이미지 | `nvidia/cuda:12.6.3-cudnn-runtime-ubuntu24.04@sha256:8aef630a54bc5c5146ae5ce68e6af5caa3df0fb690bb91544175c91f307e4356` |
| 가중치 | `models/chemprop_pretrained.pt` SHA-256 `198d8179c7196618c6bcdabffb844760351ec59b880e4a2036faef46879ea462` (이전 파일명 `chemprop_trainset_seed0.pt`, 내용 동일) |
| 자체 시험 | 25/25 일치 (`docs/selftest_report.md`, 2026-10-06, 위 이미지 ID) |

이 파일과 `tool.yaml`의 `image.digest`는 제출 커밋 이후에 갱신했다(이미지 push로
digest가 정해진 뒤 기록하기 위함). 태그 `chemprop-v1.0.0`은 이미지를 빌드한 제출
커밋을 가리키며, 이미지 내용은 그 커밋의 `src/`, `models/`, `tool.yaml`,
`README.md`, `LICENSE`, `requirements.lock`, `Dockerfile`로부터 빌드되었다.

이전 기록: `pzkeung/bio-synergy-platform:chemprop-1.0.0`
(`sha256:437899eb36eee5ccfeaffe36dc56a0996b8d112ff85c6252862965a254e1da0a`,
커밋 `acd0e15`)은 저장소·이미지 이전, 가중치 파일명 변경, 작업 API 추가 전 빌드로, 대체되었다.
