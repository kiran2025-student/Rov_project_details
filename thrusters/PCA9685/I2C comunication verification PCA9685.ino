//standard code to verify the I2C comunication of PCA9685 Module

//Hardware connection 
// SDA -> A4 
// SCL -> A5 
//power connetion.
#include <Wire.h>

void setup() {
  Wire.begin();
  
  // Enforce a 25-millisecond timeout limit so the code cannot freeze infinitely
  Wire.setWireTimeout(25000, true); 
  
  Serial.begin(9600);
  while (!Serial); 
  Serial.println("\nI2C Scanner with Timeout Protection");
}

void loop() {
  byte error, address;
  int nDevices = 0;

  Serial.println("Scanning...");

  for (address = 1; address < 127; address++) {
    Wire.beginTransmission(address);
    error = Wire.endTransmission();

    if (error == 0) {
      Serial.print("I2C device found at address 0x");
      if (address < 16) Serial.print("0");
      Serial.print(address, HEX);
      Serial.println(" !");
      nDevices++;
    }
    else if (error == 5) {
      // Error 5 means a hardware timeout was intercepted and cleared!
      Serial.print("Timeout/Lockup detected at address 0x");
      if (address < 16) Serial.print("0");
      Serial.println(address, HEX);
      
      // Attempt an emergency reset of the software I2C flags
      Wire.clearWireTimeoutFlag();
    }
  }
  
  if (nDevices == 0)
    Serial.println("No functional I2C devices found.\n");
  else
    Serial.println("Done.\n");

  delay(5000); 
}
