# ESP32 RTOS Lab

ESP32-S3 터치 디스플레이 보드로 FreeRTOS 내부 동작을 관찰하고, 그 감각을 BALA2 밸런싱 로봇으로 옮기기 위한 실험실.

## 구성
| 경로 | 내용 |
|---|---|
| `CLAUDE.md` | Claude Code용 프로젝트 맥락 (목표, 하드웨어, 작업 규칙) |
| `docs/onboarding.md` | 보드 도착 후 할 일과 온보딩 과제 체크리스트 |
| `docs/roadmap.md` | 1~4단계 로드맵, RTOS 관찰 실험 7가지 |
| `docs/hardware.md` | 두 보드의 사양과 차이 |
| `docs/arduino-vs-esp-idf.md` | Arduino와 ESP-IDF 비교, 언제 넘어갈지 |
| `docs/arduino-board-settings.md` | Arduino IDE Tools 메뉴 설정값과 각 설정의 의미 |
| `experiments/01_timeslice/` | 첫 실험: 같은 우선순위 두 태스크의 타임 슬라이싱 관찰 |
| `tools/plot_trace.py` | 보드가 보낸 트레이스를 PC에서 간트 차트로 그리는 스크립트 |

## Claude Code에서 이어가기
이 폴더에서 Claude Code를 열고 이렇게 시작하면 된다.

> CLAUDE.md와 docs/onboarding.md 읽고, 지금 체크리스트 어디까지 왔는지 같이 확인하자.
