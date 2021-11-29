#include <Servo.h>
#include <ArduinoJson.h>

Servo connectionServo, restServo, chewinessServo;

void dispense(Servo servo, int qty) {
  if (qty >= 1) {
    servo.write(180);
  }
  if (qty >= 2) {
    servo.write(0);
  }
}

void setup() {
  // TODO: Add servo setup
  Serial.begin(9600);
}

void loop() {
  // Listen for updates from server
  // Source: https://stackoverflow.com/questions/55698070/sending-json-over-serial-in-python-to-arduino/55744475
  String payload;
  while (!Serial.available()) {}
  if (Serial.available()) payload = Serial.readStringUntil('\n');
  StaticJsonDocument<512> doc;
  DeserializationError error = deserializeJson(doc, payload);
  if (error) {
    Serial.println(error.c_str()); 
    return;
  }

  if (doc["type"] == "BREW") {
    dispense(connectionServo, doc["connection_score"]);
    dispense(restServo, doc["rest_score"]);
    dispense(chewinessServo, doc["chewiness_score"]);
    // TODO: Print final receipt if that's still a thing we're doing
  } else if (doc["type"] == "INIT") {
    int id = doc["id"]; // What to encode in the barcode
    // TODO: Print initial receipt
  }

  delay(20);
}
