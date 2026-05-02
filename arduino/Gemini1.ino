/*
 * 项目：风力发电光效响应系统 (Wind & Human Interaction)
 * 平台：Arduino Uno
 * 优化：内存复用技术 (Mirroring) - 极大节省内存
 */

#include <Wire.h>
#include <INA226_WE.h>
#include <FastLED.h>

// ==========================================
//           用户配置区域 (手动修改这里)
// ==========================================

// --- 硬件引脚定义 ---
#define PIN_PIR       2     // 红外传感器引脚
#define PIN_LED_1     3     // 灯带1 数据脚
#define PIN_LED_2     4     // 灯带2 数据脚
#define PIN_LED_3     5     // 灯带3 数据脚

// --- 灯带参数设置 ---
#define NUM_LEDS      79    // 每条灯带的总灯珠数量
#define LED_START_IDX 9     // 第0-8号不亮，从第9号开始亮 (索引从0开始)
#define LED_TYPE      WS2812B
#define COLOR_ORDER   GRB   // 如果颜色不对(比如红绿反了)，改成 RGB

// --- 颜色定义 (R, G, B) ---
// 冷光 (无人的状态) - 纯白
#define COLOR_COLD    CRGB(255, 255, 255) 
// 暖光 (有人的状态) - 暖黄，可微调
#define COLOR_WARM    CRGB(255, 147, 40)  

// --- 亮度与电压映射设置 ---
// 这里的电压单位是伏特 (V)
#define VOLT_MIN      12.0  // 起始电压 (低于此值保持最低亮度)
#define VOLT_MAX      27.0  // 满载电压 (高于此值保持最高亮度)
#define BRIGHT_MIN    10.0  // 最低待机亮度 (0-255)
#define BRIGHT_MAX    255.0 // 最高满载亮度 (0-255)

// --- 平滑系数 (数值越小越平滑，延迟越高) ---
// 范围 0.01 - 1.0。0.05 类似于“果冻般”的弹性延迟
#define SMOOTH_K      0.05  

// ==========================================
//           系统变量 (无需修改)
// ==========================================

INA226_WE ina226 = INA226_WE(0x40); // 假设INA226地址为0x40
CRGB leds[NUM_LEDS]; // 只需要定义一个数组，节省3倍内存

// 用于平滑过渡的中间变量
float currentVolts = 0.0;
float filteredVolts = 0.0; // 滤波后的电压
float currentRed = 255.0, currentGreen = 255.0, currentBlue = 255.0; // 当前颜色浮点值
float currentBright = 10.0; // 当前亮度浮点值

void setup() {
  Serial.begin(9600);
  
  // 1. 初始化传感器
  pinMode(PIN_PIR, INPUT);
  Wire.begin();
  
  if(!ina226.init()){
    Serial.println("INA226 Init Failed!");
    // 如果失败不要卡死，继续运行灯光，只是没电压反应
  }
  // 设置平均值采样，减少电压读数抖动
  ina226.setAverage(INA226_AVERAGE_16);      // 16次平均
  ina226.setConversionTime(INA226_CONV_1100); // 1.1ms转换时间

  // 2. 初始化灯带 (核心技巧：多引脚镜像)
  // 将同一个 leds 数组的数据，同时发送给 3 个引脚
  FastLED.addLeds<LED_TYPE, PIN_LED_1, COLOR_ORDER>(leds, NUM_LEDS);
  FastLED.addLeds<LED_TYPE, PIN_LED_2, COLOR_ORDER>(leds, NUM_LEDS);
  FastLED.addLeds<LED_TYPE, PIN_LED_3, COLOR_ORDER>(leds, NUM_LEDS);

  // 3. 初始状态清理
  FastLED.clear();
  FastLED.show();
  Serial.println("System Ready.");
}

void loop() {
  // ------------------------------------
  // 第一步：读取并处理数据
  // ------------------------------------
  
  // 读取电压 (单位 V)
  float rawVolts = ina226.getBusVoltage_V();
  // 读取红外 (HIGH = 有人)
  bool humanDetected = digitalRead(PIN_PIR);

  // 电压滤波：消除风力不稳造成的闪烁
  // 使用低通滤波算法: 新值 = 旧值 * 0.95 + 新读数 * 0.05
  filteredVolts = (filteredVolts * 0.95) + (rawVolts * 0.05);

  // ------------------------------------
  // 第二步：计算目标状态 (Target)
  // ------------------------------------

  // 1. 计算目标颜色
  CRGB targetColor = humanDetected ? COLOR_WARM : COLOR_COLD;

  // 2. 计算目标亮度 (映射逻辑)
  // map() 函数不支持浮点，我们手动写线性映射
  float targetBright;
  
  if (filteredVolts <= VOLT_MIN) {
    targetBright = BRIGHT_MIN;
  } else if (filteredVolts >= VOLT_MAX) {
    targetBright = BRIGHT_MAX;
  } else {
    // 线性插值公式
    targetBright = BRIGHT_MIN + (filteredVolts - VOLT_MIN) * (BRIGHT_MAX - BRIGHT_MIN) / (VOLT_MAX - VOLT_MIN);
  }

  // ------------------------------------
  // 第三步：执行平滑过渡 (Smoothing)
  // ------------------------------------
  
  // 颜色的 RGB 三通道分别逼近目标值
  currentRed   += (targetColor.r - currentRed)   * SMOOTH_K;
  currentGreen += (targetColor.g - currentGreen) * SMOOTH_K;
  currentBlue  += (targetColor.b - currentBlue)  * SMOOTH_K;

  // 亮度逼近目标值
  currentBright += (targetBright - currentBright) * SMOOTH_K;

  // ------------------------------------
  // 第四步：写入灯带
  // ------------------------------------

  // 1. 组合出当前的平滑颜色
  CRGB displayColor = CRGB((uint8_t)currentRed, (uint8_t)currentGreen, (uint8_t)currentBlue);

  // 2. 填充数组
  for (int i = 0; i < NUM_LEDS; i++) {
    if (i < LED_START_IDX) {
      // 0-8号灯珠强制黑 (不亮)
      leds[i] = CRGB::Black;
    } else {
      // 9-78号灯珠显示颜色
      leds[i] = displayColor;
    }
  }

  // 3. 设置全局亮度并显示
  FastLED.setBrightness((uint8_t)currentBright);
  FastLED.show();

  // ------------------------------------
  // 调试信息 (可选，不用时可注释掉)
  // ------------------------------------
  // Serial.print("Volt:"); Serial.print(filteredVolts);
  // Serial.print(" TgtBrt:"); Serial.print(targetBright);
  // Serial.print(" CurBrt:"); Serial.println(currentBright);

  // FastLED 内部已经很忙，不需要额外的 delay，或者极短的 delay 保持帧率
  delay(10); 
}