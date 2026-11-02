//indevidual motor control with arduino + Adafruit PCA9685 PWM driver
//Hardware connetions:
//PCA9685 VCC to Arduino 5V 
//PCA9685 GND to Arduino GND
//PCA9685 SDA to Arduino A4
//PCA9685 SCL to Arduino A5
//ESC signal wire to PCA9685 channel 0 ground wire to PCA9685 GND
//ESC power wire to battery
//this code is excecuted in the platformio environment with the Adafruit PWM Servo Driver Library installed

#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_PWMServoDriver.h>

Adafruit_PWMServoDriver pca(0x40);

constexpr uint8_t ESC_CHANNEL = 0;
constexpr uint16_t PWM_HZ = 50;
constexpr uint16_t NEUTRAL_US = 1500;
constexpr uint16_t FORWARD_TEST_US = 1600;

uint16_t microsecondsToTicks(uint16_t pulseUs) {
  return static_cast<uint32_t>(pulseUs) * PWM_HZ * 4096UL / 1000000UL;
}

void setEscPulse(uint16_t pulseUs) {
  pca.setPWM(ESC_CHANNEL, 0, microsecondsToTicks(pulseUs));
}

void setup() {
  Wire.begin();
  pca.begin();
  pca.setPWMFreq(PWM_HZ);
  delay(10);

  setEscPulse(NEUTRAL_US);
  delay(3000);
}

void loop() {
  setEscPulse(NEUTRAL_US);
  delay(3000);

  setEscPulse(FORWARD_TEST_US);
  delay(2000);

  setEscPulse(NEUTRAL_US);
  delay(5000);
}