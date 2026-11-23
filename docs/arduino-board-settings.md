# Arduino IDE 보드 설정 (Tools 메뉴)

기준: Arduino IDE 2.x + esp32 3.0.7, Board = `ESP32S3 Dev Module` (2026-11-23).
옆 칸의 비유는 소프트웨어 쪽에서 비슷한 개념이다.

## 이 보드에서 쓰는 값

| 설정 | 값 |
|---|---|
| Board | `ESP32S3 Dev Module` |
| Port | `COM9` (이 PC 기준) |
| USB CDC On Boot | **Enabled** |
| USB Mode | `Hardware CDC and JTAG` |
| Flash Size | `16MB (128Mb)` |
| PSRAM | `OPI PSRAM` |
| Partition Scheme | 시리얼 테스트는 기본값으로 충분하다. LVGL처럼 큰 앱은 `16M Flash (3MB APP/9.9MB FATFS)` |
| 나머지 | 기본값 |

## 주의
- 보드를 꽂으면 IDE가 USB ID(PID 0x1001)를 보고 `ESP32 Family Device`를 자동으로 고른다. 이 항목은 장치를 식별하는 용도라서 컴파일이 안 된다. Board는 직접 고른다.
- **보드를 바꾸면 아래 설정이 기본값으로 돌아간다.** Board를 먼저 고르고 나머지를 맞춘다. 보드를 바꾸지 않으면 IDE가 설정을 기억한다.
- esp32 3.0.7에는 `Waveshare ESP32-S3-Touch-LCD-4.3B` 전용 보드 정의도 있다.
  - 이 정의는 Flash 16MB와 16MB용 파티션을 기본값으로 잡아 준다.
  - 단, PSRAM(`Enabled`를 고르면 OPI로 설정된다)과 USB CDC On Boot는 기본값이 Disabled라서 직접 켜야 한다.

## 지금 중요한 것

| 설정 | 의미 | 비유 |
|---|---|---|
| **Board** | 어떤 보드용으로 빌드할지 정한다. 핀 이름, 칩 종류, 설정 메뉴와 각 메뉴의 기본값이 이 선택에 따라 정해진다 | 빌드 타깃 프로필 (`--target`) |
| **Port** | 업로드하고 모니터링할 COM 포트 | 접속할 서버 주소 |
| **USB CDC On Boot** | `Serial`을 USB로 보낼지(Enabled), UART0으로 보낼지(Disabled) 정한다. 이 보드의 UART0은 RS485 단자에 연결되어 있어서, Disabled면 출력이 보이지 않는다 | stdout 리다이렉트 대상 |
| **USB Mode** | `Hardware CDC and JTAG`는 칩에 고정된 USB 하드웨어를 쓴다. 시리얼, JTAG, 자동 리셋이 된다. `USB-OTG (TinyUSB)`는 소프트웨어 USB 스택이다. 키보드나 USB 메모리 흉내를 낼 수 있지만, 펌웨어가 죽으면 USB도 같이 죽는다 | NIC 펌웨어가 처리하는 통신 vs 사용자 공간 네트워크 스택 |
| **Flash Size** | 플래시 용량을 링커와 업로더에 알려 준다. 이 보드는 16MB (esptool 실측) | 디스크 용량 |
| **PSRAM** | 칩 밖에 붙은 8MB RAM을 쓸지, 버스 방식은 무엇인지 정한다. 이 보드는 OPI(데이터선 8개)다. 화면 한 장이 800×480×2바이트 = 750KB인데 칩 내부 RAM은 512KB라서, **PSRAM이 없으면 화면을 띄울 수 없다** | RAM 증설과 BIOS의 메모리 종류 설정 |
| **Partition Scheme** | 플래시를 앱, OTA 예비 공간, 파일시스템으로 나누는 방식. ESP32S3 Dev Module의 기본값은 4MB 기준이라 16MB 중 대부분을 쓰지 않는다 | 디스크 파티션 테이블 |

## RTOS 실험과 관련 있는 것

| 설정 | 의미 | 비유 |
|---|---|---|
| **Arduino Runs On** | `loop()`를 실행하는 태스크를 몇 번 코어에 고정할지 정한다 (기본 Core 1). 시리얼 테스트에서 찍힌 `core=1`이 이 값이다 | 스레드 CPU affinity |
| **Events Run On** | Wi-Fi 같은 시스템 이벤트를 처리하는 태스크의 코어 | 이벤트 루프 스레드의 affinity |
| **CPU Frequency** | 클럭. 240MHz가 최대다. 낮추면 전력은 줄고 실험의 타이밍은 달라진다 | CPU 거버너 |
| **Core Debug Level** | ESP 내부 로그를 어디까지 찍을지 정한다. 올리면 출력이 늘어서 관찰자 효과가 생긴다 | 로그 레벨 |

## 지금은 기본값으로 두는 것

| 설정 | 의미 |
|---|---|
| Flash Mode | 플래시와 통신하는 방식과 속도 (QIO 80MHz) |
| Upload Mode | 업로드 경로. `UART0 / Hardware CDC` 그대로 둔다 |
| Upload Speed | UART 업로드 속도. 내장 USB에서는 사실상 영향이 없다 |
| Erase All Flash Before Upload | 업로드 전에 플래시 전체를 지운다. 저장해 둔 설정까지 지워진다 (포맷 후 설치) |
| USB Firmware MSC / DFU On Boot | USB-OTG 모드 전용 기능. 지금 모드에서는 상관없다 |
| JTAG Adapter | 나중에 디버거를 붙일 때 쓴다 |
