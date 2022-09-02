unsigned int dTime=0;
unsigned long timeNow=0;
unsigned long lastTime=0;

// the setup routine runs once when you press reset:
void setup() {
  Serial.begin(115200); // initialize serial communication at 115200 bits per second:
  Serial.write("Dear Python, Good day to you! Yours sincerely, Arduino"); // A distinctive startup message 
  lastTime=micros(); // start time
}

// the loop routine runs over and over again forever:
void loop() {
  // read the input on analog pin 0:
  int sensorValue = analogRead(A0);
  // generate timestamp
  timeNow=micros();
  dTime = (unsigned int)(timeNow-lastTime); // small difference between (potentially) large values
  lastTime=timeNow;

  //float voltage = sensorValue * (5.0 / 1023.0);
  //Serial.print(voltage);
  //Serial.print(',');
  //Serial.println(dTime);

  // send the two bytes corresponding to (unsigned) integer A0 reading
  Serial.write(lowByte(sensorValue));
  Serial.write(highByte(sensorValue));
  // send the two bytes corresponding to (unsigned) integer time difference
  Serial.write(lowByte(dTime));
  Serial.write(highByte(dTime));
  // NO termination character, message of 4 byte fixed length!
}
