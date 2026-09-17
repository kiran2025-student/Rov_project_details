//PH sensor code
//Micro-controller: Arduino UNO
//WARNING 
//i have fixed the voltage rating for ADC but in real time working it might change so during the testing check the PH value for both.
//pin declaration
const int PH_Pin = A0;

const float V_Ref = 5; //the voltage declaration help the MC to find the operating voltage and help for the ADC working.

const float ADC_res = 1023; //1023 id the ADC resolution of the Arduino

// the below value are the base value used to convert the  standard PH scale.
// the below values considered from a https://cimpleo.com/blog/arduino-ph-meter-using-ph-4502c/
float sensor_slope = -5.56;
float sensor_offset = 20.89; 


void setup(){
//initializing the communication with Arduino UART
Serial.begin(9600);
Serial.println("===================================");
Serial.println("---------PH405C Firm ware----------");
Serial.println("===================================");
}

void loop() {
// collection of the analog value and finding the average value 
// declaration of the keyword for the for loop 
int total_samples = 15;
float raw_adc_sum = 0;

//for loop to find the average of the PH value
for (int i =0; i < total_samples; i++) 
{
  raw_adc_sum += analogRead(PH_Pin); //find the average ADC value
  delay(10); //10ms gap between every ADC value calculation
}

float average_adc = raw_adc_sum / total_samples; //formula for the average value of ADC which give the average value for the better digital value.

//conversion of average ADC value into the DC value.
float voltage = average_adc * (V_Ref / ADC_res);

//PH value calculation formula
float caluculated_ph = (sensor_slope * voltage) + sensor_offset;

//serial monitor display
Serial.print("raw ADC Avg: ");
Serial.print(average_adc, 1);
Serial.print("sensor voltage: ");
Serial.print(voltage, 3);
Serial.print("Final PH value");
Serial.print(caluculated_ph, 2);
delay(1500); 

}



