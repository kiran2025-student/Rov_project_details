#include <Servo.h>


Servo myESC;  // Create servo object to control the ESC


void setup() {
  Serial.begin(9600); // Initialize the Serial Monitor at 9600 baud
 
  // Attach ESC to Pin 9 with standard timing bounds (1000us to 2000us)
  myESC.attach(9, 1000, 2000);
 
  Serial.println("--- ESC Initialization ---");
  Serial.println("Sending low pulse to arm the ESC...");
 
  // SimonK safety arming routine
  myESC.write(0);
  delay(4000); // Give the ESC 4 seconds to boot up and finish arming beeps
 
  Serial.println("ESC Armed successfully!");
  Serial.println("Enter a speed value between 0 (Stop) and 180 (Full Speed):");
}


void loop() {
  // Check if you have typed a number into the Serial Monitor
  if (Serial.available() > 0) {
    int speedVal = Serial.parseInt(); // Read the typed integer
   
    // Constrain the value to safe servo limits
    speedVal = constrain(speedVal, 0, 180);
   
    Serial.print("Setting motor throttle to: ");
    Serial.println(speedVal);
   
    myESC.write(speedVal); // Send the pulse to the ESC
  }
}



