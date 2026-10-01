/*
 * Arduino Code for 4-Pin Single Water Sensor Module
 * Connect: VCC -> 5V, GND -> GND, Analog Pin (AO/PO/EC) -> A0
 */

const int sensorPin = A0;   // Connect the Analog output pin here
const float VREF = 5.0;     // Arduino supply voltage
const int ADC_RES = 1023;   // 10-bit resolution

void setup() {
  Serial.begin(9600);
  Serial.println("--- Single Sensor Module Online ---");
}

void loop() {
  // 1. Read the raw analog voltage smoothly
  float voltage = readAnalogAverage(sensorPin) * (VREF / ADC_RES);
  
  // 2. Calculate the metric based on what sensor you have plugged in:
  
  // OPTION 1: If this is your pH Sensor board
  float pH_Value = 7.0 + ((voltage - 2.0) * 4.0); 

  // OPTION 2: If this is your EC / TDS Sensor board
  // float TDS_Value = voltage * 500.0; 

  // 3. Print out your data
  Serial.print("Sensor Voltage: "); Serial.print(voltage, 2); Serial.print("V");
  Serial.print(" | Calculated pH: "); Serial.println(pH_Value, 2);
  
  // If using TDS option, uncomment below and comment out pH print lines:
  // Serial.print(" | Est. TDS: "); Serial.print(TDS_Value, 0); Serial.println(" ppm");

  delay(1500); 
}

// Rolling average function to filter out electrical ripples in water
float readAnalogAverage(int pin) {
  long total = 0;
  int samples = 20;
  for (int i = 0; i < samples; i++) {
    total += analogRead(pin);
    delay(10);
  }
  return (float)total / samples;
}
