#include <Wire.h>
#include <INA226.h>
#include <FastLED.h>

/* =====================================================
   ★★★ 灯带核心参数（最常改） ★★★
   ===================================================== */
#define NUM_LEDS     79        // ★ 灯珠总数（每条）
#define LED_START     9        // ★ 从第 9 颗开始亮（0~8 不亮）
#define BRIGHT_MIN   3         // ★ 初始 / 无风亮度（非常暗，安全）
#define BRIGHT_MAX  150         // ★ 最大亮度（保护电路，别太大）

#define DATA_PIN_1   3
#define DATA_PIN_2   4
#define DATA_PIN_3   5

/* ===================================================== */

#define PIR_PIN      2
#define INA_ADDR  0x40

CRGB leds1[NUM_LEDS];
CRGB leds2[NUM_LEDS];
CRGB leds3[NUM_LEDS];

INA226 ina226(INA_ADDR);

/* -------- 颜色定义（可随意改） -------- */
const CRGB COLOR_WHITE = CRGB(240, 240, 255);
const CRGB COLOR_WARM  = CRGB(255, 120, 15);   // 暖黄色

/* -------- 状态变量 -------- */
uint8_t currentBrightness = BRIGHT_MIN;
uint8_t targetBrightness  = BRIGHT_MIN;

CRGB currentColor = COLOR_WHITE;
CRGB targetColor  = COLOR_WHITE;

bool humanLatched = false;   // ★ 红外锁存，解决你白↔黄跳的问题

/* ===================================================== */

void setup() {
  Serial.begin(9600);
  pinMode(PIR_PIN, INPUT);

  Wire.begin();
  ina226.begin();

  FastLED.addLeds<WS2812B, DATA_PIN_1, GRB>(leds1, NUM_LEDS);
  FastLED.addLeds<WS2812B, DATA_PIN_2, GRB>(leds2, NUM_LEDS);
  FastLED.addLeds<WS2812B, DATA_PIN_3, GRB>(leds3, NUM_LEDS);

  FastLED.setBrightness(BRIGHT_MIN);
  fillAll(COLOR_WHITE);
}

/* ===================================================== */

void loop() {
  /* -------- 读取 INA226 电压 -------- */
  float voltage = ina226.getBusVoltage();  // V

  /* -------- 电压 → 亮度（非线性 + 档位明显） -------- */
  if (voltage < 9.0)       targetBrightness = BRIGHT_MIN;
  else if (voltage < 12.0) targetBrightness = 25;   
  else if (voltage < 14.0) targetBrightness = 50;   // 一档
  else if (voltage < 18.0) targetBrightness = 75;   
  else if (voltage < 20.0) targetBrightness = 100;   // 二档
  else if (voltage < 22.0) targetBrightness = 125;  
  else                     targetBrightness = BRIGHT_MAX; // 三档

  /* -------- 红外锁存逻辑（关键） -------- */
  if (digitalRead(PIR_PIN) == HIGH) {
    humanLatched = true;
  } else if (digitalRead(PIR_PIN) == LOW) {
    humanLatched = false;
  }

  targetColor = humanLatched ? COLOR_WARM : COLOR_WHITE;

  /* -------- 平滑过渡（亮度 + 颜色） -------- */
  smoothBrightness();
  smoothColor();

  /* -------- 输出到灯带 -------- */
  FastLED.setBrightness(currentBrightness);
  fillAll(currentColor);
  FastLED.show();

  delay(20);   // ★ 小延迟 = 丝滑关键
}

/* =====================================================
   工具函数（极省内存）
   ===================================================== */

void fillAll(CRGB c) {
  for (int i = LED_START; i < NUM_LEDS; i++) {
    leds1[i] = c;
    leds2[i] = c;
    leds3[i] = c;
  }
}

void smoothBrightness() {
  if (currentBrightness < targetBrightness) currentBrightness++;
  else if (currentBrightness > targetBrightness) currentBrightness--;
}

void smoothColor() {
  currentColor.r += (targetColor.r - currentColor.r) / 6;
  currentColor.g += (targetColor.g - currentColor.g) / 6;
  currentColor.b += (targetColor.b - currentColor.b) / 6;
}
