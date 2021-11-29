#include "Adafruit_Thermal.h"
#include <ArduinoJson.h>
#include "SoftwareSerial.h"
#include <Servo.h>
#define TX_PIN 6 // Arduino transmit  YELLOW WIRE  labeled RX on printer
#define RX_PIN 5 // Arduino receive   GREEN WIRE   labeled TX on printer

SoftwareSerial mySerial(RX_PIN, TX_PIN); // Declare SoftwareSerial obj first
Adafruit_Thermal printer(&mySerial);

//Servo connectionServoPos, restServoPos, connectionServoNeg, restServoNeg, chewinessServo, milkServo;

void dispense(Servo servo, int qty) {
  if (qty >= 1) {
    servo.write(180);
  }
  if (qty >= 2) {
    servo.write(0);
  }
}

void setup() {
//  pinMode(7, OUTPUT); digitalWrite(7, LOW);
//  pinMode(8, OUTPUT); digitalWrite(8, LOW);
//  pinMode(9, OUTPUT); digitalWrite(9, LOW);
//  pinMode(10, OUTPUT); digitalWrite(10, LOW);
//  pinMode(11, OUTPUT); digitalWrite(11, LOW);
//  pinMode(12, OUTPUT); digitalWrite(12, LOW);

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

//  connectionServoNeg.attach(7);
//  restServoNeg.attach(8);
//  connectionServoPos.attach(9);
//  restServoPos.attach(10);
//  chewinessServo.attach(11);
//  milkServo.attach(12);

  // TODO - initialize all servos to correct angle

}

void loop() {
  DynamicJsonDocument doc(512);
  int     size_ = 0;
  String  payload;
  if ( Serial.available() ) {
    payload = Serial.readStringUntil( '\n' );
  }
  delay(500);
  DeserializationError   error = deserializeJson(doc, payload);
  if (error) {
    Serial.println(error.c_str());
    return;
  } else {
    if (doc["t"] == "I") {
       printer.printBarcode(doc["id"], CODE93);
       printer.println("Making your drink now. Our AI is reading through every word ever written to find some like-minded people to drink with. Come back in 15 minutes!");
    } else if (doc["t"] == "B") {

       int r_s = atoi(doc["r_s"]);
       int c_s = atoi(doc["c_s"]);
       int ch_s = atoi(doc["ch_s"]);

//       if (r_s > 0) {
//        dispense(restServoPos, r_s);
//       }
//
//       if (r_s < 0) {
//        dispense(restServoNeg, -1*r_s);
//       }
//
//       if (c_s > 0) {
//        dispense(connectionServoPos, c_s);
//       }
//
//       if (c_s < 0) {
//        dispense(connectionServoNeg, -1*c_s);
//       }
//
//       dispense(chewinessServo, 1);
//       if (ch_s >= 0) {
//         dispense(chewinessServo, ch_s);
//       }
//
//       dispense(milkServo, 1);



       printer.println("We have assessed every atom in your brain and calculated your totally objective mental state. Today, your drink has:");
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
       char* passage = new char [512]();
       serializeJson(doc["p"], passage, 512);
       printer.println("While drinking, give this a read. It feels... similar... to your thoughts ");
       printer.println(passage);
    }
    printer.feed(4);
    printer.sleep();
    delay(500);
    printer.wake();
  }

}
