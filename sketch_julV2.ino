#include <Wire.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BNO055.h>
#include <utility/imumaths.h>

Adafruit_BNO055 bno = Adafruit_BNO055(55);

// Variables to store sensor data
float heading, roll, pitch;

// Direction strings
String headingDirection;
String rollDirection;
String pitchDirection;

// Function Prototypes
void readSensor();
void calculateHeadingDirection();
void calculateRollDirection();
void calculatePitchDirection();
void printTelemetry();

void setup()
{
  Serial.begin(9600);
  Serial.println("=================================");
  Serial.println("      BNO055 ORIENTATION");
  Serial.println("=================================");

  // Initialize BNO055
  if (!bno.begin())
  {
    Serial.println("ERROR: BNO055 not detected!");
    Serial.println("Check wiring or I2C address.");
    while (1);
  }

  delay(1000);

  // Use external crystal for better accuracy
  bno.setExtCrystalUse(true);

  Serial.println("BNO055 Initialized Successfully!");
  Serial.println();
}

void loop()
{
  readSensor();

  calculateHeadingDirection();
  calculateRollDirection();
  calculatePitchDirection();

  printTelemetry();

  delay(5000);
}

//------------------------------------------------------
// Read Orientation Data
//------------------------------------------------------

int count = 0;
void readSensor()
{

  Serial.print("Reading #: ");
  Serial.println(count++);

  sensors_event_t event;
  bno.getEvent(&event);

  heading = event.orientation.x;
  roll = event.orientation.y;
  pitch = event.orientation.z;
}

//------------------------------------------------------
// Convert Heading Angle to Compass Direction
//------------------------------------------------------
void calculateHeadingDirection()
{
  if (heading >= 337.5 || heading < 22.5)
    headingDirection = "North";
  else if (heading < 67.5)
    headingDirection = "North-East";
  else if (heading < 112.5)
    headingDirection = "East";
  else if (heading < 157.5)
    headingDirection = "South-East";
  else if (heading < 202.5)
    headingDirection = "South";
  else if (heading < 247.5)
    headingDirection = "South-West";
  else if (heading < 292.5)
    headingDirection = "West";
  else
    headingDirection = "North-West";
}

//------------------------------------------------------
// Determine Roll Status
//------------------------------------------------------
void calculateRollDirection()
{
  if (roll > 5)
    rollDirection = "Right Roll";
  else if (roll < -5)
    rollDirection = "Left Roll";
  else
    rollDirection = "Level";
}

//------------------------------------------------------
// Determine Pitch Status
//------------------------------------------------------
void calculatePitchDirection()
{
  if (pitch > 5)
    pitchDirection = "Nose Up";
  else if (pitch < -5)
    pitchDirection = "Nose Down";
  else
    pitchDirection = "Level";
}

//------------------------------------------------------
// Display Telemetry
//------------------------------------------------------
void printTelemetry()
{
  Serial.println("=================================");
  Serial.println("         ROV TELEMETRY");
  Serial.println("=================================");

  Serial.print("Heading : ");
  Serial.print(heading, 1);
  Serial.print("° (");
  Serial.print(headingDirection);
  Serial.println(")");

  Serial.print("Roll    : ");
  Serial.print(roll, 1);
  Serial.print("° (");
  Serial.print(rollDirection);
  Serial.println(")");

  Serial.print("Pitch   : ");
  Serial.print(pitch, 1);
  Serial.print("° (");
  Serial.print(pitchDirection);
  Serial.println(")");

  Serial.println("---------------------------------");
  Serial.println("Sensor Status : OK");
  Serial.println("=================================");
  Serial.println();
// --- particailly added for converting data into CSV 
  Serial.print(heading);
Serial.print(",");
Serial.print(roll);
Serial.print(",");
Serial.println(pitch);
}