# 하드웨어 정리

## Waveshare ESP32-S3-Touch-LCD-4.3B
- 모듈: ESP32-S3-WROOM-1-N16R8 (LX7 듀얼 코어, 최대 240MHz, 16MB Flash, 8MB PSRAM)
- 무선: 2.4GHz Wi-Fi, BLE 5 (클래식 블루투스는 없음)
- 화면: 4.3인치 800×480 RGB LCD, I2C 정전식 5점 터치 (인터럽트 지원)
- 인터페이스: 터미널 블록으로 RS485, CAN, I2C, 절연 디지털 입출력. TF 카드 슬롯, RTC
- I2C 버스: GPIO8(SDA), GPIO9(SCL). IO 확장 칩, 터치, 외부 I2C가 이 버스를 공유한다
- **주의**: LCD가 GPIO 대부분을 쓴다. 리셋과 백라이트 등은 CH422G IO 확장 칩으로 제어한다. 자유 핀이 적다
- 전원: 터미널 블록 7~36V DC, USB-C, 3.7V 리튬 배터리 (GH1.25 커넥터, 배터리는 별매)
- 다운로드 모드: BOOT 버튼을 누른 채 전원을 넣는다
  - 평소에는 필요 없다. 내장 USB Serial/JTAG가 자동으로 리셋해 다운로드 모드에 넣는다 (2026-11-23 LVGL 데모 업로드에서 확인).
    펌웨어가 USB를 망가뜨렸을 때처럼 자동 리셋이 안 될 때만 쓴다
- USB-C는 하나이고, 칩 내장 USB Serial/JTAG에 연결된다. Windows 장치 관리자에는 `USB JTAG/serial debug unit`으로 뜬다 (2026-11-23 실측)
  - Arduino에서 `Serial`을 쓰려면 `USB CDC On Boot` = `Enabled`
  - 별도 JTAG 장비 없이 USB 하나로 OpenOCD + GDB 디버깅이 된다 (ESP-IDF 단계에서 활용)
- 회로도 확인 결과 (2026-11-23, [Sch.pdf](https://files.waveshare.com/wiki/ESP32-S3-Touch-LCD-4.3B/ESP32-S3-Touch-LCD-4.3B-Sch.pdf))
  - USB-C D+/D- → `USBH_N/P` → 0Ω 저항 R27/R28 → `ESP_USB_N/P` → GPIO19/GPIO20. 중간에 스위치나 다른 칩이 없다
  - **이 보드에는 CH343이 없다.** 위키 자료 목록의 CH343 데이터시트는 공용 자료일 뿐이다. 자동 리셋 회로(DTR/RTS → EN/IO0)도 없다
  - UART0(GPIO43 `TXD0`, GPIO44 `RXD0`)은 RS485 트랜시버(SP3485)로 간다. 그래서 `USB CDC On Boot`가 Disabled면 `Serial` 출력이 RS485 단자로 나간다
  - 회로도 메모: 화면 혼자 약 550mA를 쓰고, PC USB는 500mA 미만일 수 있다. PC에 연결해 디버깅할 때는 배터리 스위치를 OFF로 둔다
- 공식 위키: https://www.waveshare.com/wiki/ESP32-S3-Touch-LCD-4.3B (Arduino와 ESP-IDF 데모 있음)

## M5Stack BALA2 Fire
- 컨트롤러: M5Stack Fire, 오리지널 ESP32 (LX6 듀얼 코어, 240MHz)
- 셀프 밸런싱 로봇 키트. 내장 IMU의 기울기가 밸런싱 제어의 입력이다
- USB-시리얼 칩은 생산 시기에 따라 CP210x 또는 CH9102. 포트가 안 보이면 드라이버부터 확인
- 직접 만든 펌웨어를 올리면 기본 데모가 지워진다. M5Burner로 공장 펌웨어를 다시 올릴 수 있다

## 두 칩의 차이
| 항목 | ESP32 (BALA2 Fire) | ESP32-S3 (4.3B) |
|---|---|---|
| CPU | LX6 듀얼 코어 240MHz | LX7 듀얼 코어 240MHz + 벡터 명령어 |
| USB | 외부 USB-시리얼 칩 필요 | 칩 내장 USB |
| 블루투스 | 클래식 + BLE | BLE만 |
| 공통 | FreeRTOS, ESP-IDF, Arduino 코어 | 같음 |

태스크, 큐, 뮤텍스, 코어 고정 코드는 거의 그대로 옮길 수 있다. 핀 번호와 주변장치를 직접 다루는 코드는 고쳐야 한다.
