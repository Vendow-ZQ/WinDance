#include <FastLED.h>  
// 引入 FastLED 库，用于控制 WS2812B 等可编程 RGB 灯珠

/* ================== 基本参数设置（最常改的地方） ================== */
#define LED_TYPE WS2812B      
// 灯珠型号：WS2812B（如果以后换灯，这里要改）
#define COLOR_ORDER GRB       
// WS2812B 通常是 GRB 顺序（颜色不对时优先改这里）
#define NUM_LEDS 79           
// ★★★ 灯珠数量：每条灯带 79 颗（改数量就改这里）

#define DATA_PIN_1 4          
// 第一条灯带数据引脚 → Arduino D4
#define DATA_PIN_2 5          
// 第二条灯带数据引脚 → Arduino D5
#define DATA_PIN_3 6          
// 第三条灯带数据引脚 → Arduino D6
#define BRIGHTNESS 50         
// ★★★ 全局亮度（0~255）
// 建议 20~60 之间，40 非常安全，保护电路 & USB 供电

/* ================== 灯珠数组定义 ================== */

CRGB leds1[NUM_LEDS];        
// 第一条灯带的灯珠数组
CRGB leds2[NUM_LEDS];        
// 第二条灯带的灯珠数组
CRGB leds3[NUM_LEDS];        
// 第三条灯带的灯珠数组

/* ================== 初始化 ================== */

void setup() {

  FastLED.addLeds<LED_TYPE, DATA_PIN_1, COLOR_ORDER>(leds1, NUM_LEDS);
  // 初始化第一条灯带，指定类型、引脚、颜色顺序、数量
  FastLED.addLeds<LED_TYPE, DATA_PIN_2, COLOR_ORDER>(leds2, NUM_LEDS);
  // 初始化第二条灯带
  FastLED.addLeds<LED_TYPE, DATA_PIN_3, COLOR_ORDER>(leds3, NUM_LEDS);
  // 初始化第三条灯带
  FastLED.setBrightness(BRIGHTNESS);
  // ★★★ 设置全局亮度（保护电路的关键）
}

/* ================== 主循环 ================== */

void loop() {

  /* -------- 颜色设置（最常改的地方） -------- */

  CRGB warmOrange = CRGB(255, 180, 20);
  // ★★★ 暖黄色偏橙色
  // 红 255（满）
  // 绿 140（偏暖）
  // 蓝 40（很低，避免冷色）
  // 如果想更橙 → 提高绿
  // 如果想更暖 → 降低蓝

  /* -------- 点亮第一条灯带 -------- */
  for (int i = 0; i < NUM_LEDS; i++) {
    leds1[i] = warmOrange;   
    // 给第 i 颗灯珠赋暖橙色
  }
  /* -------- 点亮第二条灯带 -------- */
  for (int i = 0; i < NUM_LEDS; i++) {
    leds2[i] = warmOrange;
  }
  /* -------- 点亮第三条灯带 -------- */
  for (int i = 0; i < NUM_LEDS; i++) {
    leds3[i] = warmOrange;
  }

  FastLED.show();            
  // ★★★ 真正把数据发送到灯带（没有这行灯不会亮）

  delay(1000);               
  // 延时 1 秒（静态常亮，其实有无都行）
}
