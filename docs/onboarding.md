# 온보딩 체크리스트

각 과제의 "완료 기준"을 만족하면 체크한다.

## A-0. 초기불량 점검 (아무것도 굽기 전에)
위키에 공장 펌웨어가 들어 있는지는 나와 있지 않다. 그래서 전원을 넣었을 때 보이는 상태를 먼저 기록해 둔다.
- [ ] **외관**: 화면 깨짐, 커넥터·터미널 블록 들뜸, 부품 탈락이 없다. 배터리 스위치는 OFF (배터리 없음)
- [ ] **첫 전원**: USB-C로 5V 1A 이상 공급 (위키 소비전력 450mA, 전원이 약하면 화면이 빨갛게 될 수 있다고 함)
  - 전원이 켜지는지, 화면에 무언가 뜨는지, 터치가 반응하는지 기록한다
  - 결과 (2026-11-23): 공장 데모 펌웨어가 들어 있고, 전원을 넣으면 데모 화면이 뜬다
  - 공장 데모는 부팅할 때 R·G·B·W 단색 화면을 차례로 띄운다 → 죽은 픽셀 없음 확인. 터치 점검은 진행 중
- [x] **포트 인식**: 장치 관리자에 COM 포트가 뜨고 장치 이름이 보인다 → CH343 경유인지 칩 내장 USB인지 여기서 확정
  - 결과 (2026-11-23): `USB JTAG/serial debug unit` → 칩 내장 USB Serial/JTAG. CH343을 거치지 않는다
- [ ] **화면이 비어 있으면**: 데모 zip의 `Firmware\bin` 테스트 펌웨어를 `flash_download_tool`로 굽는다
  (ESP32-S3 / USB, 주소 `0x0`, 1152000 baud, 안 되면 BOOT를 누른 채 전원 재투입)
- [ ] **기능별 점검** (Arduino 환경이 갖춰진 뒤, 데모 예제로)
  - `01_I2C_Test`: CH422G(0x20~0x27, 0x30~0x3F), RTC(0x51), 터치(0x5D) 주소가 잡힌다
  - `08_DrawColorBar`: 색 막대가 B-G-R 순서로 나오고, 죽은 픽셀이나 줄 무늬가 없다
  - `09_lvgl_Porting`: 화면 구석까지 터치가 반응한다
  - `04_RTC_Test`: 시간이 흐르고 알람이 울린다
  - `05_IO_Test`: DO0↔DI0, DO1↔DI1을 점퍼선으로 잇는다. 초록 화면이면 통과, 빨강이면 실패
  - `03_SD_Test`: TF 카드가 있을 때만. 종류와 용량을 인식한다
  - RS485, CAN은 상대 장치(USB-CAN 등)가 필요하므로 생긴 뒤에 한다

## A. 4.3B 보드 첫날
- [ ] **개발 환경**: Arduino IDE에 Espressif ESP32 보드 패키지 설치. 버전은 Waveshare 위키 권장 버전에 맞춘다
  - 위키 확인 결과 (2026-11-23): IDE ≥ 1.8, 설치 경로에 한글·중문 금지. `esp32 by Espressif Systems` **3.0.7**
    (위키는 3.0.0 이상을 요구하고, 오프라인 패키지도 3.0.7이다. RS485 수신 문제가 생기면 3.0.7로 내리라고 한다)
  - 보드 매니저 URL: `https://espressif.github.io/arduino-esp32/package_esp32_index.json`
  - 라이브러리: ESP32_Display_Panel ≥ 0.1.4, ESP32_IO_Expander ≥ 0.0.4, lvgl **8.4.0**과 `lv_conf.h`는 데모 zip에 든 파일로 오프라인 설치한다
  - 데모: `ESP32-S3-Touch-LCD-4.3B-BOX-Demo.zip`의 Arduino 예제 `09_lvgl_Porting`이 LVGL과 터치(GT911) 데모다
- [ ] **보드 설정**: Board = `ESP32S3 Dev Module`, PSRAM = `OPI PSRAM`, Flash Size = `16MB`
  - 이 설정이 틀리면 화면이 안 나오는 경우가 많다
- [ ] **포트 인식**: USB-C(데이터 케이블)로 연결해 장치 관리자에 COM 포트가 보인다
  - 업로드가 안 되면 BOOT 버튼을 누른 채 전원을 넣어 다운로드 모드로
- [ ] **Blink 대신 Serial**: `Serial.println`이 시리얼 모니터에 찍힌다
  - 이 보드는 칩 내장 USB를 쓰므로 Tools → `USB CDC On Boot` = `Enabled`, `USB Mode` = `Hardware CDC and JTAG`로 둔다
    (Disabled면 `Serial`이 USB에 연결되지 않은 UART0으로 나가서 아무것도 안 찍힌다)
  - 완료 기준: 1초마다 `millis()` 값이 찍힌다
- [ ] **위키 LVGL 데모 실행**: 화면이 뜨고 터치에 반응한다
  - 완료 기준: 데모 화면에서 버튼을 눌러 반응을 확인

## B. FreeRTOS 첫 만남
- [ ] **내 태스크 하나 만들기**: `xTaskCreate`로 1초마다 메시지를 찍는 태스크. `loop()`는 비워둔다
  - 소프트웨어 비유: 스레드 하나 띄우기
- [ ] **어느 코어에서 도는지 확인**: `xPortGetCoreID()`를 찍어본다. `loop()`와 내 태스크를 비교
- [ ] **스택 크기 감각**: `uxTaskGetStackHighWaterMark(NULL)`로 남은 스택을 확인. 스택을 일부러 작게 잡아 크래시도 내본다
- [ ] **실험 01 실행**: `experiments/01_timeslice` 업로드 → `tools/plot_trace.py`로 간트 차트 확인
  - 완료 기준: A와 B가 약 1ms 간격으로 번갈아 나오는 줄무늬를 본다
- [ ] **실험 01 변형**: `PRIO_B`를 3으로 올리고 다시 그린다. A가 B가 끝날 때까지 못 도는 것을 확인

## C. BALA2 Fire 도착 후
- [ ] 충전 먼저
- [ ] 기본 펌웨어로 밸런싱 데모가 서는지 확인 (모터, IMU, 엔코더 정상 확인)
- [ ] USB-시리얼 드라이버 (CP210x 또는 CH9102) 설치, 포트 인식
- [ ] M5Stack 보드 패키지 + M5Unified 라이브러리, Board = `M5Stack-Fire`
- [ ] IMU 기울기 값을 시리얼로 PC에 찍기 → 밸런싱 제어 입력의 출발점
- [ ] 실험 01을 BALA2 Fire에서도 돌려보고 S3와 결과 비교

## 다음
B까지 끝나면 `docs/roadmap.md`의 실험 2번부터 진행한다.
