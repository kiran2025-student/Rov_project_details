/*
 * PH-4502C pH sensor reader for Arduino Uno.
 *
 * Connect the module analog output to A0, VCC to 5 V, and GND to GND.
 * The slope and offset below are starting calibration values; calibrate
 * them against buffer solutions for your specific probe and module.
 */

const int PH_PIN = A0;
const float VREF_VOLTS = 5.0f;       // Nominal Uno ADC reference voltage.
const float ADC_MAX_COUNT = 1023.0f; // 10-bit ADC: 0..1023.
const float PH_SLOPE = -5.56f;
const float PH_OFFSET = 20.89f;
const int SAMPLE_COUNT = 15;
const unsigned long SAMPLE_DELAY_MS = 10;
const unsigned long REPORT_INTERVAL_MS = 1500;

float readAverageAdc(int pin);

void setup() {
  Serial.begin(9600);
  Serial.println("PH-4502C pH sensor ready");
  Serial.println("sample,raw_adc_avg,voltage_v,estimated_ph");
}

void loop() {
  static unsigned long sampleNumber = 0;

  const float averageAdc = readAverageAdc(PH_PIN);
  const float voltage = averageAdc * (VREF_VOLTS / ADC_MAX_COUNT);
  const float estimatedPh = (PH_SLOPE * voltage) + PH_OFFSET;

  ++sampleNumber;
  Serial.print(sampleNumber);
  Serial.print(',');
  Serial.print(averageAdc, 1);
  Serial.print(',');
  Serial.print(voltage, 3);
  Serial.print(',');
  Serial.println(estimatedPh, 2);

  delay(REPORT_INTERVAL_MS);
}

float readAverageAdc(int pin) {
  unsigned long total = 0;

  for (int i = 0; i < SAMPLE_COUNT; ++i) {
    total += analogRead(pin);
    if (i + 1 < SAMPLE_COUNT) {
      delay(SAMPLE_DELAY_MS);
    }
  }

  return static_cast<float>(total) / SAMPLE_COUNT;
}
