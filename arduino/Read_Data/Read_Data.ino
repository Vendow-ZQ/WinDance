#include <Wire.h>
#include <INA226_WE.h>

#define INA226_ADDRESS 0x40

INA226_WE ina226(INA226_ADDRESS);

void setup() {
  Serial.begin(9600);
  Wire.begin();

  if (!ina226.init()) {
    Serial.println("INA226 not found");
    while (1);
  }

  // ===== CSV Header =====
  Serial.println("Time_ms,Voltage_V,Current_mA,Power_mW");
}

void loop() {
  unsigned long t = millis();

  float voltage = ina226.getBusVoltage_V();  // V
  float current = ina226.getCurrent_mA();    // mA
  float power   = ina226.getBusPower();      // mW

  Serial.print(t);
  Serial.print(",");
  Serial.print(voltage, 4);
  Serial.print(",");
  Serial.print(current, 4);
  Serial.print(",");
  Serial.println(power, 4);

  delay(1000);
}
