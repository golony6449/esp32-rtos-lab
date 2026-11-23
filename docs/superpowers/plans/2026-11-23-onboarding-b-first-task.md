# 온보딩 B-1~B-3: 첫 태스크와 빌드 스크립트

목표: `docs/onboarding.md`의 B-1(내 태스크 하나 만들기), B-2(어느 코어에서 도는지), B-3(스택 크기 감각)을
스케치 하나로 관찰한다. 주니어가 워크트리 안에서 컴파일까지 확인할 수 있게 빌드 진입점도 만든다.

## Global Constraints
- 대화·주석·출력 메시지는 한국어로 쓴다. 새 개념에는 소프트웨어 비유를 한 줄 붙인다.
- 스크립트는 파이썬 표준 라이브러리만 쓴다. `subprocess`는 인자 리스트로 부르고 `shell=True`를 쓰지 않는다. Windows 전용 셸 문법을 쓰지 않는다.
- 실험은 `experiments/NN_이름/`에 두고, 머리 주석에 "무엇을 관찰하는가"와 "예상 결과"를 쓴다 (`experiments/01_timeslice/01_timeslice.ino` 형식).
- **ESP32의 FreeRTOS는 스택 크기를 워드가 아니라 바이트로 받는다.** `xTaskCreate`의 스택 인자와 `uxTaskGetStackHighWaterMark`의 반환값은 모두 바이트다. 이름과 주석도 바이트로 쓴다.
- 관찰자 효과를 의식한다. 관찰 대상이 아닌 곳에서 CPU를 쓰지 않는다 (예: 빈 `loop()`가 쉬지 않고 도는 일).
- 보드 설정(FQBN)은 `docs/arduino-board-settings.md`의 값을 따른다: `esp32:esp32:esp32s3:CDCOnBoot=cdc,USBMode=hwcdc,FlashSize=16M,PSRAM=opi`.
- 다른 파일은 건드리지 않는다. 특히 `experiments/01_timeslice/`와 `tools/plot_trace.py`는 바꾸지 않는다.

## 작업

### 작업 1: 빌드·업로드 진입점 `tools/build.py`

**Files:**
- Create: `tools/build.py`
- Create: `tests/test_build.py`
- Modify: `.gitignore`

사용법:
```
python tools/build.py <스케치 폴더> [--upload] [--port COM9] [--partition app3M_fat9M_16MB] [--dry-run]
```

함수 (모두 `tools/build.py` 안):
- `BASE_FQBN = "esp32:esp32:esp32s3:CDCOnBoot=cdc,USBMode=hwcdc,FlashSize=16M,PSRAM=opi"`
- `make_fqbn(partition: str | None) -> str`: partition이 있으면 `BASE_FQBN + ",PartitionScheme=" + partition`, 없으면 `BASE_FQBN`.
- `find_cli(env: Mapping[str, str] = os.environ) -> Path | None`: 순서대로 찾는다.
  1. 환경변수 `ARDUINO_CLI`가 가리키는 파일이 있으면 그것
  2. `shutil.which("arduino-cli")`
  3. Windows(`sys.platform == "win32"`)이면 `C:\Program Files\Arduino IDE\resources\app\lib\backend\resources\arduino-cli.exe` (Arduino IDE 2.x에 들어 있는 것)
  4. 없으면 `None`
- `find_config() -> Path | None`: `Path.home() / ".arduinoIDE" / "arduino-cli.yaml"`이 있으면 그 경로 (IDE와 같은 라이브러리·보드 패키지 위치를 쓰기 위함), 없으면 `None`.
- `build_commands(cli: Path, sketch: Path, build_dir: Path, fqbn: str, config: Path | None, upload: bool, port: str) -> list[list[str]]`:
  - 첫 명령: `[cli, (--config-file, config), "compile", "--fqbn", fqbn, "--build-path", build_dir, sketch]` (config가 None이면 `--config-file` 쌍을 뺀다). 모든 원소는 `str`.
  - upload가 True면 둘째 명령: `[cli, (--config-file, config), "upload", "-p", port, "--fqbn", fqbn, "--input-dir", build_dir, sketch]`.
- `port_busy_hint(output: str) -> str | None`: 출력에 `PermissionError`, `port doesn't exist`, `port is busy` 중 하나가 있으면
  "포트를 다른 프로그램(Arduino IDE의 Serial Monitor 등)이 잡고 있을 수 있다. 닫고 다시 올린다." 같은 한국어 안내를, 없으면 `None`.
- `main(argv: list[str] | None = None) -> int`:
  - 빌드 폴더는 `<레포 루트>/.build/<스케치 폴더 이름>` (레포 루트 = `tools/`의 부모).
  - CLI를 못 찾으면 한국어 안내를 stderr에 쓰고 2를 돌려준다.
  - `--dry-run`이면 명령을 한 줄씩 출력만 하고 0.
  - 명령을 차례로 실행하고, 출력은 그대로 보여 주면서(그리고 안내 판단용으로 모아서) 실패하면 `port_busy_hint`가 있으면 stderr에 쓰고 그 명령의 종료 코드를 돌려준다. 모두 성공하면 0.
  - `--port` 기본값 `COM9`.
- `if __name__ == "__main__": sys.exit(main())`

`.gitignore`에 `.build/`를 추가한다.

테스트 `tests/test_build.py` (pytest, 보드·arduino-cli 없이 돈다):
- 모듈 이름이 PyPI `build`와 겹치지 않도록 `importlib.util.spec_from_file_location("lab_build", <레포>/tools/build.py)`로 불러온다.
- `make_fqbn(None) == BASE_FQBN`, `make_fqbn("app3M_fat9M_16MB")`가 `,PartitionScheme=app3M_fat9M_16MB`로 끝난다.
- `build_commands`: upload=False면 명령 1개이고 `compile`·`--fqbn`·`--build-path`가 들어 있다. upload=True면 2개이고 둘째에 `upload`, `-p`, 포트, `--input-dir`가 있다. config=None이면 `--config-file`이 없다. 모든 원소가 `str`이다.
- `port_busy_hint`: `"PermissionError(13, ...)"`, `"Could not open COM9, the port doesn't exist"`, `"the port is busy"`에는 안내 문자열, `"Sketch uses 1234 bytes"`에는 `None`.
- `find_cli`: `tmp_path`에 가짜 파일을 만들고 `{"ARDUINO_CLI": str(파일)}`을 넘기면 그 경로를 돌려준다.
- `main(["<임시 스케치 폴더>", "--dry-run"])`: `ARDUINO_CLI`를 monkeypatch로 가짜 파일로 두면 0을 돌려주고 stdout에 `compile`이 찍힌다.

### 작업 2: 첫 태스크 실험 `experiments/00_first_task/`

**Files:**
- Create: `experiments/00_first_task/00_first_task.ino`
- Modify: `docs/onboarding.md`
- Modify: `README.md`

머리 주석 (실험 01 형식):
- 무엇을 관찰하는가: (B-1) `xTaskCreate`로 만든 태스크가 `loop()`와 따로 돈다. (B-2) 코어를 고정하지 않은 태스크가 어느 코어에서 도는지, `setup()`/`loop()`(Arduino의 loopTask, core 1)와 비교한다. (B-3) 스택 최고 수위(high water mark)로 남은 스택을 보고, `CRASH_DEMO`를 1로 두면 스택을 넘쳐 크래시가 나는 것을 본다.
- 예상 결과: 1초마다 `tick=N core=C hwm=B` 한 줄. `core`는 0 또는 1이 나오고 바뀔 수도 있다(코어 고정 안 함). `hwm`은 처음 몇 번 줄다가 일정해진다. `CRASH_DEMO 1`이면 `A stack overflow in task my_task has been detected` 같은 메시지와 함께 재부팅된다.
- 비유: 태스크 = 스레드, `xTaskCreate` = 스레드 생성, 코어 고정 안 함 = affinity 없음, high water mark = 스레드 스택을 가장 깊이 썼을 때의 남은 여유.
- 출력 형식과 실행 방법: `python tools/build.py experiments/00_first_task --upload` 후 시리얼 모니터 115200.

코드 요구사항:
- 조절 손잡이: `#define CRASH_DEMO 0`, `STACK_BYTES` (평소 4096, `CRASH_DEMO`면 1024 수준), `TASK_PRIO = 1`, `PERIOD_MS = 1000`.
- `setup()`: `Serial.begin(115200)`, USB CDC 연결을 최대 3초 기다린다(`while (!Serial && millis() < 3000) delay(10);`). `setup` 자신이 도는 코어와 우선순위(`uxTaskPriorityGet(NULL)`)를 한 줄 찍는다. 그다음 `xTaskCreate`(코어 고정 없음, `xTaskCreatePinnedToCore`를 쓰지 않는다)로 `my_task`를 만들고, 실패하면 그 사실을 찍는다.
- `my_task`: `PERIOD_MS`마다 `tick`, `xPortGetCoreID()`, `uxTaskGetStackHighWaterMark(NULL)`(바이트)를 한 줄로 찍는다. 대기는 `vTaskDelay(pdMS_TO_TICKS(PERIOD_MS))`. 정수 형식 지정자는 타입에 맞게 캐스트한다(`(unsigned)` 등).
- `CRASH_DEMO`가 1이면 `my_task`가 큰 지역 배열(예: 2048바이트 `volatile uint8_t`)을 쓰는 함수를 불러 스택을 넘친다. 컴파일러가 지우지 못하게 배열을 실제로 읽고 쓴다.
- `loop()`: 자기 코어를 처음 한 번만 찍고 `vTaskDelay(portMAX_DELAY)`로 잠든다. 빈 `loop()`는 쉬지 않고 돌아 core 1의 CPU를 쓰기 때문이라는 주석을 단다(관찰자 효과).

문서:
- `docs/onboarding.md`의 B-1~B-3 항목 아래에 "실험: `experiments/00_first_task` (`CRASH_DEMO`로 B-3 크래시)" 한 줄씩. 체크박스는 바꾸지 않는다(보드에서 확인한 뒤 사람이 체크한다).
- `README.md` 구성 표에 `experiments/00_first_task/`와 `tools/build.py` 행을 추가한다.

## 테스트 명령
```
uv run --with pytest python -m pytest tests -q
python tools/build.py experiments/00_first_task
```
둘째 명령은 이 PC의 Arduino IDE와 esp32 3.0.7로 실제 컴파일한다.

## Review Focus
1. ESP32 FreeRTOS의 스택 단위는 바이트다. 이름·주석·출력에서 워드라고 하지 않는다.
2. `loop()`가 쉬지 않고 돌지 않는다. 관찰하는 출력 말고는 CPU를 쓰지 않는다.
3. `my_task`는 코어를 고정하지 않는다 (`xTaskCreate`). `CRASH_DEMO` 기본값은 0이다.
4. `tools/build.py`는 `shell=True`를 쓰지 않고, 실패한 명령의 종료 코드를 그대로 돌려준다.
5. 실험 머리 주석에 "무엇을 관찰하는가", "예상 결과", 비유가 있다.
