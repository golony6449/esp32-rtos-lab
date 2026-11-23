/*
 * 실험 00: 내 첫 태스크 (온보딩 B-1~B-3)
 *
 * 무엇을 관찰하는가
 *   (B-1) xTaskCreate로 만든 태스크(my_task)가 loop()와 따로 도는지 본다.
 *   (B-2) 코어를 고정하지 않은 태스크가 어느 코어에서 도는지,
 *         setup()/loop()를 실행하는 Arduino loopTask(기본 core 1)와 비교한다.
 *   (B-3) uxTaskGetStackHighWaterMark(NULL)로 작업 스택의 최고 수위(남은 여유)를
 *         보고, CRASH_DEMO를 1로 두면 스택을 일부러 넘쳐 크래시가 나는 것을 본다.
 *
 * 원리
 *   FreeRTOS에서 태스크는 자기 스택을 따로 가진 실행 흐름이다. ESP32의
 *   xTaskCreate는 스택 크기를 워드가 아니라 바이트 단위로 받는다.
 *   high water mark는 태스크가 지금까지 스택을 가장 깊이 썼던 순간의
 *   남은 바이트 수다. 처음 몇 번은 함수 호출 깊이가 늘면서 줄고, 이후 일정해진다.
 *   코어를 고정하지 않으면 스케줄러가 한가한 코어에 태스크를 배치한다.
 *
 * 예상 결과
 *   1초마다 `tick=N core=C hwm=B first=F` 한 줄. first는 my_task가 처음 실행된 코어.
 *   - core는 0 또는 1이 나오고 실행 중에 바뀔 수도 있다(코어 고정 안 함).
 *   - setup()/loop()는 core 1에서 돈다(Arduino 기본값).
 *   - hwm은 처음 몇 줄에서 줄어들다가 일정한 값으로 안정된다.
 *   - CRASH_DEMO 1이면 `A stack overflow in task my_task has been detected` 같은
 *     메시지와 함께 보드가 재부팅된다.
 *
 * 비유
 *   태스크 = 스레드, xTaskCreate = 스레드 생성, 코어 고정 안 함 = affinity 없음,
 *   high water mark = 스택을 가장 깊이 썼을 때 남은 여유 공간.
 *
 * 출력 형식 (시리얼, 115200)
 *   # setup() core=1 prio=1 stack=4096 bytes crash_demo=0
 *   tick=12 core=0 hwm=2436 first=1
 *   tick=13 core=0 hwm=2436 first=1
 *   ...
 *   # loop() core=1 prio=1
 *
 * 실행 방법 (업로드는 사람이 보드에서 확인할 때만)
 *   python tools/build.py experiments/00_first_task --upload
 *   시리얼 모니터 115200
 *
 * 상태: 2026-11-23 보드에서 실행 확인 (위 출력은 실측값). 처음엔 core 1, 깨어난 뒤엔 core 0.
 *       CRASH_DEMO 1도 확인: 첫 printf에서 Stack canary watchpoint triggered (my_task), core 1.
 */
#include <Arduino.h>

// ---- 실험 조절 손잡이 ----
#define CRASH_DEMO 0     // 1로 바꾸면 스택 오버플로 크래시를 본다 (B-3)
#define TASK_PRIO 1      // Arduino loopTask와 같은 우선순위
#define PERIOD_MS 1000   // 관찰 출력 주기
#if CRASH_DEMO
#define STACK_BYTES 1024  // 일부러 작게: 아래 2048바이트 지역 배열이 넘친다
#else
#define STACK_BYTES 4096  // 스택 크기 단위는 바이트다 (워드 아님)
#endif

static uint32_t tick = 0;

#if CRASH_DEMO
static volatile uint8_t overflow_sink;

// 큰 지역 배열로 스택을 넘치게 한다. 결과를 volatile에 남겨 컴파일러가 지우지 못하게 한다.
static void __attribute__((noinline)) overflow_stack(void) {
  volatile uint8_t big[2048];
  for (size_t i = 0; i < sizeof(big); i++) {
    big[i] = (uint8_t)(i * 7u);
  }
  uint8_t sum = 0;
  for (size_t i = 0; i < sizeof(big); i++) {
    sum = (uint8_t)(sum + big[i]);
  }
  overflow_sink = sum;
}
#endif

// B-1: loop()와 별개로 도는 내 태스크. loopTask와 같은 우선순위(1)다.
static void my_task(void *arg) {
  (void)arg;
  // B-2: 처음 실행된 코어를 출력보다 먼저 적어 둔다. 리셋 직후 USB가 다시 붙는 동안
  // 첫 줄을 놓쳐도, 매 줄의 first=로 언제든 확인할 수 있다.
  const int first_core = (int)xPortGetCoreID();
  for (;;) {
    tick++;
    Serial.printf("tick=%lu core=%d hwm=%u first=%d\n",
                  (unsigned long)tick,
                  (int)xPortGetCoreID(),                  // B-2: 지금 도는 코어
                  (unsigned)uxTaskGetStackHighWaterMark(NULL),  // B-3: 남은 스택(바이트)
                  first_core);                            // B-2: 처음 실행된 코어
#if CRASH_DEMO
    overflow_stack();  // 스택을 넘겨 크래시를 일으킨다
#endif
    vTaskDelay(pdMS_TO_TICKS(PERIOD_MS));
  }
}

void setup() {
  Serial.begin(115200);
  // USB CDC가 연결될 때까지 최대 3초 기다린다. 보드를 꽂고 모니터를 여는 데 시간이 걸린다.
  while (!Serial && millis() < 3000) delay(10);

  Serial.printf("# setup() core=%d prio=%u stack=%u bytes crash_demo=%d\n",
                (int)xPortGetCoreID(),
                (unsigned)uxTaskPriorityGet(NULL),
                (unsigned)STACK_BYTES,
                (int)CRASH_DEMO);

  // 코어를 고정하지 않는 xTaskCreate를 쓴다. xTaskCreatePinnedToCore는 쓰지 않는다.
  // 비유: affinity 없이 스레드를 만드는 것.
  BaseType_t ok = xTaskCreate(my_task, "my_task", STACK_BYTES, nullptr, TASK_PRIO, nullptr);
  if (ok != pdPASS) {
    Serial.println("# xTaskCreate 실패: 태스크를 만들지 못했다");
  }
}

void loop() {
  // Arduino loopTask는 core 1에서 돈다. 처음 한 번만 찍는다.
  static bool printed = false;
  if (!printed) {
    printed = true;
    Serial.printf("# loop() core=%d prio=%u\n",
                  (int)xPortGetCoreID(),
                  (unsigned)uxTaskPriorityGet(NULL));
  }
  // 빈 loop()가 쉬지 않고 돌면 core 1의 CPU를 계속 써서 관찰자 효과가 생긴다
  // (관찰 대상인 my_task의 실행 시간도 흔들린다). 그래서 영원히 잠든다.
  vTaskDelay(portMAX_DELAY);
}
