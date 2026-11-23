# Arduino vs ESP-IDF

ESP-IDF(Espressif IoT Development Framework)는 ESP32 제조사 Espressif의 공식 개발 프레임워크다.
Arduino ESP32 코어도 내부적으로 ESP-IDF 위에서 돈다. 소프트웨어로 치면 Arduino는 고수준 프레임워크, ESP-IDF는 그 아래 SDK다.

| 항목 | Arduino | ESP-IDF |
|---|---|---|
| 시작점 | `setup()` / `loop()` | `app_main()` |
| FreeRTOS 설정 | 미리 컴파일되어 고정 | `menuconfig`로 틱 주기, 런타임 통계, 워치독 등 변경 |
| 디버깅 | 시리얼 출력 위주 | JTAG, 코어 덤프, 시스템 트레이스 |
| 빌드 | IDE 버튼 | CMake 기반, VS Code 확장 있음 |
| 진입 장벽 | 낮음 | 높음 |

## 넘어갈 시점
- `xTaskCreate`, 큐, 세마포어 같은 FreeRTOS API는 양쪽이 같다. Arduino에서 익힌 것은 그대로 쓴다.
- "커널 설정을 바꾸고 싶은데 못 바꾼다"는 순간이 오면 넘어간다. 예: `vTaskGetRunTimeStats`가 막혀 있을 때, 틱 주기를 바꿔 실험하고 싶을 때.
- micro-ROS는 ESP-IDF 기반 지원이 가장 탄탄하다. 4단계 전에는 넘어가 있는 편이 좋다.
