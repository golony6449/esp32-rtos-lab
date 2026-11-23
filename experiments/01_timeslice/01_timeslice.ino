/*
 * 실험 01: 타임 슬라이싱 관찰
 *
 * 무엇을 관찰하는가
 *   같은 코어(core 1)에서 같은 우선순위로 쉬지 않고 도는 두 태스크 A, B를
 *   스케줄러가 어떻게 번갈아 실행시키는지 본다.
 *
 * 원리
 *   각 태스크는 계속 현재 시각(us)을 읽는다. 직전 시각과의 차이가 GAP_US보다 크면
 *   "그 사이에 내가 CPU를 뺏겼다"는 뜻이므로, 거기까지를 하나의 실행 구간으로 기록한다.
 *   기록은 RAM 버퍼에만 쌓고, 출력은 실험이 끝난 뒤에 한다 (관찰자 효과 최소화).
 *
 * 예상 결과
 *   PRIO_A == PRIO_B : 틱(보통 1ms)마다 A, B가 번갈아 나오는 줄무늬
 *   PRIO_B >  PRIO_A : B가 끝날 때까지 A는 거의 실행되지 못함
 *
 * 출력 형식 (시리얼, 115200)
 *   TRACE_BEGIN
 *   task,start_us,end_us
 *   ...
 *   TRACE_END
 *   PC에서: python tools/plot_trace.py --port COM5
 *
 * 상태: 실제 보드에서 아직 컴파일·실행 전. 처음 돌릴 때 함께 검증할 것.
 */
#include <Arduino.h>
#include "esp_timer.h"

// ---- 실험 조절 손잡이 ----
static const UBaseType_t PRIO_A = 2;
static const UBaseType_t PRIO_B = 2;   // 3으로 올리면 실험 2(굶주림) 맛보기
static const uint32_t RUN_US = 20000;  // 각 태스크가 도는 시간: 20ms
static const uint32_t GAP_US = 20;     // 이보다 긴 공백 = CPU를 뺏겼던 구간
static const BaseType_t CORE = 1;

struct Seg { uint8_t task; uint32_t start; uint32_t end; };
static const int MAX_SEGS = 1500;
static Seg segs[MAX_SEGS];
static volatile int segCount = 0;
static volatile bool overflow = false;
static portMUX_TYPE segMux = portMUX_INITIALIZER_UNLOCKED;

static int64_t t0 = 0;
static TaskHandle_t controller = nullptr;

static inline uint32_t nowUs() { return (uint32_t)(esp_timer_get_time() - t0); }

static void pushSeg(uint8_t id, uint32_t s, uint32_t e) {
  portENTER_CRITICAL(&segMux);
  if (segCount < MAX_SEGS) segs[segCount++] = {id, s, e};
  else overflow = true;
  portEXIT_CRITICAL(&segMux);
}

static void worker(void *arg) {
  const uint8_t id = (uint8_t)(uintptr_t)arg;
  uint32_t segStart = nowUs();
  uint32_t last = segStart;
  uint32_t runStart = segStart;

  while (last - runStart < RUN_US) {
    uint32_t now = nowUs();
    if (now - last > GAP_US) {      // 그 사이 다른 누군가가 CPU를 썼다
      pushSeg(id, segStart, last);
      segStart = now;
      // 뺏긴 시간은 내 실행 시간에 넣지 않는다
      runStart += (now - last);
    }
    last = now;
  }
  pushSeg(id, segStart, last);

  xTaskNotifyGive(controller);      // "나 끝났어"
  vTaskDelete(nullptr);
}

static void runExperiment() {
  segCount = 0;
  overflow = false;
  controller = xTaskGetCurrentTaskHandle();

  // 워커를 만드는 동안 워커가 끼어들지 못하도록 잠시 내 우선순위를 올린다.
  const UBaseType_t myPrio = uxTaskPriorityGet(nullptr);
  vTaskPrioritySet(nullptr, configMAX_PRIORITIES - 1);

  t0 = esp_timer_get_time();
  xTaskCreatePinnedToCore(worker, "A", 4096, (void *)0, PRIO_A, nullptr, CORE);
  xTaskCreatePinnedToCore(worker, "B", 4096, (void *)1, PRIO_B, nullptr, CORE);

  // 두 워커가 끝날 때까지 블록 (블록된 동안 높은 우선순위는 방해가 안 된다)
  ulTaskNotifyTake(pdFALSE, portMAX_DELAY);
  ulTaskNotifyTake(pdFALSE, portMAX_DELAY);
  vTaskPrioritySet(nullptr, myPrio);

  // 여기서부터 출력. 실험은 이미 끝났다.
  Serial.println("TRACE_BEGIN");
  Serial.println("task,start_us,end_us");
  for (int i = 0; i < segCount; i++) {
    Serial.printf("%c,%lu,%lu\n", 'A' + segs[i].task,
                  (unsigned long)segs[i].start, (unsigned long)segs[i].end);
  }
  Serial.println("TRACE_END");
  Serial.printf("# segments=%d overflow=%d tick_hz=%d prioA=%u prioB=%u\n",
                segCount, (int)overflow, (int)configTICK_RATE_HZ,
                (unsigned)PRIO_A, (unsigned)PRIO_B);
}

void setup() {
  Serial.begin(115200);
  delay(2000);  // 시리얼 모니터를 열 시간
  Serial.printf("# experiment 01 timeslice, loop() runs on core %d\n", xPortGetCoreID());
}

void loop() {
  runExperiment();
  delay(5000);  // 5초마다 반복하므로 PC 스크립트를 아무 때나 켜도 된다
}
