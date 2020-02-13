// 58 us +Vs followed by 58 us -Vs defines a binary 1
// 100 us +Vs followed by 100 us -Vs defines a binary 0

int PWM = 0;
int DIR = 1;
int TF = 21;
int BREAK = 20;
int CUR = 23;
int WARNING_LED = 13;
float current;
const long numChars = 1000;
char receivedChars[numChars];
long messageLen = 0;
char currentPacket[numChars];
long lenCurrentPacket = 0;
const long baselinePacketLen = 43;
const char idlePacket[baselinePacketLen] = "111111111111110111111110000000000111111111"; // all decoders ignore this command

void setup() {
  // the setup routine runs once when you press reset:
  pinMode(PWM, OUTPUT);
  digitalWrite(PWM, HIGH);
  pinMode(DIR, OUTPUT);
  pinMode(TF, INPUT);
  pinMode(BREAK, OUTPUT);
  digitalWrite(BREAK, LOW);
  pinMode(WARNING_LED, OUTPUT);
  Serial.begin(9600);              // Baud rate
}

// the loop routine runs over and over again forever:
void loop() { 
  current = analogRead(CUR) * 3.3/1024. / (0.350*3./1000.);
  if (current > 1000) {
    digitalWrite(BREAK, HIGH);
    delayMicroseconds(1); // Should be 1 us delay between pin changes on LMD18200
    digitalWrite(PWM, LOW);
    digitalWrite(WARNING_LED, HIGH);
  }
  recvWithStartEndMarkers();
  writeDCC();
}

void recvWithStartEndMarkers() {
    static boolean recvInProgress = false;
    static long ndx = 0;
    char startMarker = '<';
    char endMarker = '>';
    char rc;
 
    while (Serial.available() > 0) {
        rc = Serial.read();

        if (recvInProgress == true) {
            if (rc != endMarker) {
                receivedChars[ndx] = rc;
                ndx++;
                if (ndx >= numChars) {
                    ndx = numChars - 1;
                }
            }
            else {
                recvInProgress = false;
                messageLen = ndx;
                strncpy(currentPacket, receivedChars, messageLen);
                lenCurrentPacket = messageLen;
            }
        }
        else if (rc == startMarker) {
            ndx = 0;
            recvInProgress = true;
        }
    }
}

void writeBinary1(){
  digitalWrite(DIR, LOW);
  delayMicroseconds(58);
  digitalWrite(DIR, HIGH);
  delayMicroseconds(58);
}

void writeBinary0(){
  digitalWrite(DIR, LOW);
  delayMicroseconds(100);
  digitalWrite(DIR, HIGH);
  delayMicroseconds(100);
}

void writeDCC(){
  long i = 0;
  if (lenCurrentPacket > 0){
    for (i=0; i<lenCurrentPacket; i++){
      if (currentPacket[i] == '0'){
        writeBinary0();
      }
      else if (currentPacket[i] == '1'){
        writeBinary1();
      }
    }
  }
  writeIdlePacket(); // write an idle packet between repeats
}

void writeIdlePacket(){
  long i = 0;
  for (i=0; i<baselinePacketLen; i++){
    if (idlePacket[i] == '0'){
      writeBinary0();
    }
    else if (idlePacket[i] == '1'){
      writeBinary1();
    }
  }
}

