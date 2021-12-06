#include "Adafruit_Thermal.h"
#include <ArduinoJson.h>
#include "SoftwareSerial.h"
#include <Servo.h>
#define TX_PIN 6 // Arduino transmit  YELLOW WIRE  labeled RX on printer
#define RX_PIN 5 // Arduino receive   GREEN WIRE   labeled TX on printer

Servo connectionServo, restServo, chocolateChipServo, cacaoServo;


SoftwareSerial mySerial(RX_PIN, TX_PIN); // Declare SoftwareSerial obj first
Adafruit_Thermal printer(&mySerial);

String permString;
bool gotThing = false;

void dispense(Servo servo, int score) {
  int num_servings = abs(score);
  int dispenseAngle = 180;
  if (num_servings >= 1) {
    servo.write(dispenseAngle);
    if (dispenseAngle == 180) {
      dispenseAngle = 0;
    } else {
      dispenseAngle = 180;
    }
  } if (num_servings >= 2) {
    servo.write(dispenseAngle);
    if (dispenseAngle == 180) {
      dispenseAngle = 0;
    } else {
      dispenseAngle = 180;
    }
  }
}

void dispenseWhole(int connection_score, int rest_score, int chewy_score) {
  // dispense one chocolate and one cacao powder by default
  dispense(chocolateChipServo, 1);
  dispense(cacaoServo, 1);
  dispense(connectionServo, connection_score);
  dispense(restServo, rest_score);
  dispense(chocolateChipServo, chewy_score);


}


void setup() {


  // NOTE: SOME PRINTERS NEED 9600 BAUD instead of 19200, check test page.
  mySerial.begin(9600);  // Initialize SoftwareSerial
  //Serial1.begin(19200); // Use this instead if using hardware serial
  printer.begin();        // Init printer (same regardless of serial type)

  printer.setFont('A');
  printer.justify('C');
  printer.setSize('S');

  printer.setBarcodeHeight(100);

  Serial.begin(9600);
  while(!Serial) {
  }

  chocolateChipServo.attach(9);
  cacaoServo.attach(10);
  restServo.attach(11);
  connectionServo.attach(12);

  connectionServo.write(0);
  restServo.write(0);
  chocolateChipServo.write(0);
  cacaoServo.write(0);





}

void loop() {
//
  DynamicJsonDocument doc(768);
  int     size_ = 0;
  String  payload;
  if ( Serial.available() ) {
    payload = Serial.readStringUntil( '\n' );
    Serial.println(payload);
    if (payload.length() > 0) {
      permString = payload;
      gotThing = true;
      Serial.println(payload);
    }

 } else {
  return;
 }

  if (gotThing) {
    Serial.println(payload);
  }


  DeserializationError   error = deserializeJson(doc, payload);
  if (error) {
    if (error.c_str() != "EmptyInput") {
      printer.println(error.c_str());
      printer.feed(2);
    }

    Serial.println(error.c_str());
    return;
  }
  else {
    if (doc["t"] == "I") {
      const char* barcodeId = doc["id"];
      printer.setSize('L');
      printer.println(barcodeId);
      printer.setSize('S');
      printer.feed(3);
     printer.println("Analyzing your feelings and making your drink now - itll take 5 minutes.");
     printer.println("Kukou is reading through every word ever to find some stories to sip to.");

//          printer.println("Making your drink now.");
       printer.feed(3);
       printer.flush();
    } else if (doc["t"] == "B") {
      Serial.println("2");
       int r_s = atoi(doc["r_s"]);
       int c_s = atoi(doc["c_s"]);
       int ch_s = atoi(doc["ch_s"]);

       dispenseWhole(r_s, c_s, ch_s);

       printer.println("We have assessed every atom in your brain to make this. Today, your drink has: ");
       delay(250);



       printer.print(c_s);
       printer.println(" connection");
       delay(250);
       printer.print(r_s);
       printer.println(" rest");
       delay(250);
       printer.print(ch_s);
       printer.println(" things to chew on");
       delay(250);
    } else if (doc["t"] == "R") {
      const char* printout = doc["p"];
      byte len = strlen(printout);
      if (len) {
        if (printout[len-1] == '>') {
          printer.println(printout);
          printer.feed(3);
        } else {
        printer.println(printout); }
      }

      printer.flush();
    }

    printer.sleep();
    delay(500);
    printer.wake();
  }


}
