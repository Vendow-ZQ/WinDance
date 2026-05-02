#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <INA226_WE.h>

// --- 硬件参数设置 ---
#define SCREEN_WIDTH 128 // OLED 屏幕宽度
#define SCREEN_HEIGHT 64 // OLED 屏幕高度
#define OLED_RESET    -1 // 重置引脚 (如果你的屏没有RST脚，就设为-1)
#define SCREEN_ADDRESS 0x3C // OLED I2C 地址，通常是 0x3C
#define INA226_ADDRESS 0x40 // INA226 I2C 地址，默认通常是 0x40

// --- 引脚定义 ---
#define PIR_PIN 2       // 红外传感器接在 D2

// --- 对象实例化 ---
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);
INA226_WE ina226 = INA226_WE(INA226_ADDRESS);

void setup() {
  // 1. 初始化串口 (用于电脑端调试)
  Serial.begin(9600);

  // 2. 初始化红外传感器引脚
  pinMode(PIR_PIN, INPUT);

  // 3. 初始化 OLED 屏幕
  if(!display.begin(SSD1306_SWITCHCAPVCC, SCREEN_ADDRESS)) {
    Serial.println(F("OLED allocation failed"));
    for(;;); // 如果屏幕启动失败，卡死在这里
  }
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 10);
  display.println("System Init...");
  display.display();
  delay(1000);

  // 4. 初始化 INA226
  if(!ina226.init()){
    Serial.println("Failed to init INA226. Check wiring.");
    display.clearDisplay();
    display.setCursor(0,0);
    display.println("INA226 Error!");
    display.display();
    while(1);
  }
  
  // 设置 INA226 的工作模式 (根据需要调整)
  // 等待转换时间设为平均值，增加读数稳定性
  ina226.setAverage(INA226_AVERAGE_16);
  
  Serial.println("System Ready!");
}

void loop() {
  // --- 读取传感器数据 (已修正函数名) ---
  float voltage_V = ina226.getBusVoltage_V(); 
  float current_mA = ina226.getCurrent_mA();  
  float power_mW = ina226.getBusPower();   // 这里已修改
  int pirState = digitalRead(PIR_PIN);        

  // --- 串口打印 ---
  Serial.print("V: "); Serial.print(voltage_V); Serial.print(" V, ");
  Serial.print("I: "); Serial.print(current_mA); Serial.print(" mA, ");
  Serial.print("P: "); Serial.print(power_mW); Serial.println(" mW");

  // --- OLED 显示更新 ---
  display.clearDisplay();
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.print("Power Monitor");

  display.setCursor(0, 16);
  display.print("Vol: "); display.print(voltage_V); display.print(" V");

  display.setCursor(0, 28);
  display.print("Cur: "); display.print(current_mA); display.print(" mA");

  display.setCursor(0, 40);
  display.print("Pwr: "); display.print(power_mW); display.print(" mW");

  display.setCursor(0, 54);
  display.print("Human: ");
  if (pirState == HIGH) {
    display.setTextColor(SSD1306_BLACK, SSD1306_WHITE); 
    display.print(" YES ");
    display.setTextColor(SSD1306_WHITE); 
  } else {
    display.print(" No  ");
  }

  display.display(); 
  delay(500); 
}