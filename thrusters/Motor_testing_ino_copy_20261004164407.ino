//this is the motor test code

//use the D9(arduino pin) - signal pin of the ESC 

//comman ground between the arduino and esc.

//in the code we can have a custom values for the PWM in the line 16, 17, 18.
#include <Servo.h>

Servo esc;

const byte ESC_SIGNAL_PIN = 9;

// The listing says 1500 µs is stop, >1500 forward, <1500 reverse.
// Start with small changes from neutral.
const int NEUTRAL_US = 1500;
const int FORWARD_US = 2000;
const int REVERSE_US = 2000;

void setup() {
  esc.attach(ESC_SIGNAL_PIN, 1000, 2000);

  // Give the ESC a neutral signal while it initializes.
  esc.writeMicroseconds(NEUTRAL_US);
  delay(3000);
}

void loop() {
  esc.writeMicroseconds(NEUTRAL_US);
  delay(2000);

  esc.writeMicroseconds(FORWARD_US);
  delay(1000);

  esc.writeMicroseconds(NEUTRAL_US);
  delay(2000);

  esc.writeMicroseconds(REVERSE_US);
  delay(1000);

  esc.writeMicroseconds(NEUTRAL_US);
  delay(5000);
}
