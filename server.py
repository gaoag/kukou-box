from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
from imutils.video import VideoStream
import time
import math
from command_arduino import *
from qr import *
from serial import Serial
from datetime import datetime
from csv import writer
import shortuuid
import json
from flask_cors import CORS, cross_origin
import pandas as pd
from doc_compare import *

CAMERA_ID = 0 # TODO: Set to external webcam id.
TICKET_DELAY_S = 900
ARDUINO_PORT = "/dev/cu.usbmodem14101" # TODO
BAUDRATE = 9600

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

# what port number do we use?
# arduino_controller = BasicArduinoOutputModule(0)
# arduino_controller_TCP = BasicArduinoOutputModuleTCPSerial()
ser = Serial(ARDUINO_PORT, BAUDRATE, timeout=2.5)

journal_dict = {}

vs = VideoStream(src=CAMERA_ID).start()

def send_message(data):
	data_json = json.dumps(data)
	ser.write(data_json.encode('ascii'))

def send_message_2(data):
	ser.write(data.encode('ascii'))

def save_results(results, journal_result_id, timestamp):
	outlist = [results['connection'], results['rest'], results['connection_score'], results['rest_score'], results['chewiness_score'], journal_result_id, timestamp]

	with open("./data/tickets.csv", 'a') as f:
		writer_object = writer(f)
		writer_object.writerow(outlist)
		f.close()

@app.route("/submit_journal_text_partial", methods=['POST'])
def submit_journal_text_partial():
	jsdata = request.data
	dict1 = json.loads(jsdata)
	journal_dict.update(dict1)
	return "added q1"

@app.route("/submit_journal_text", methods=['POST'])
def submit_journal_text():
	'''
	   1. process journal text to construct scores + document mapping.
	   2. save information in a csv; associate with a qr code.
	   3. tell arduino to print QR code.
	'''
	jsdata = request.data
	dictpartial = json.loads(jsdata)
	journal_dict.update(dictpartial)
	results = calc_journal_scores_whole(journal_dict)
	journal_dict.clear()

	# results is an array that follows this convention: {'connection':passage, 'rest':passage, 'connection_score':float, 'rest_score':float, 'speed_score':float}
	journal_result_id = str(shortuuid.uuid()[:10]).upper() # FIXME: I think we need either 8 or 12 digits depending on which
	currenttime = datetime.now()
	save_results(results, journal_result_id, currenttime)

	# Send barcode to Arduino for initial receipt
	data = { 't': "I", 'id': journal_result_id }
	print(data)
	print(results)
	send_message(data)


	return f"submitting journal text"

def check_barcode():
	'''Check camera for a QR code. If one appears, process it and send data to Arduino
	to start making hot chocolate.'''
	barcodes = read_from_camera(vs, filter="ANY") # filter="CODE93")
	if len(barcodes) > 0:
		print(f"Found QR code: {barcodes[0]}")
		# pull up the associated stuff by reading in the associated text
		barcode_text = barcodes[0]
		brew(barcode_text)
	else:
		print("No barcodes found")

def brew(id):
	tickets = pd.read_csv("./data/tickets.csv")
	entry = tickets[tickets['journal_id'].str.slice(start=0, stop=-1) == id]
	try:
		timestamp = entry['timestamp'].iloc[0]

	except:
		return False # No entries found
	timestampobj = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
	if ((datetime.now() - timestampobj).seconds < 10):
		return False # "Do nothing! It's not time yet."
	# construct dictionary to send to the arduino


	data = {}
	data['t'] = "B"
	if abs(entry['connection_score'].iloc[0]) > abs(entry['rest_score'].iloc[0]):
		passage = "on connection - " + str(entry['connection'].iloc[0])
	else:
		passage = "on rest - " + str(entry['rest'].iloc[0])

	passage = passage.replace("'", "")
	passage = passage.replace('"', "")
	# data['p'] = "he"
	data['c_s'] = str(entry['connection_score'].iloc[0])
	data['r_s'] = str(entry['rest_score'].iloc[0])
	data['ch_s'] = str(entry['chewiness_score'].iloc[0])
	print(data)
	send_message(data)
	time.sleep(3)

	data = {}
	data['t'] = "R"
	# data['p'] = "hello this is a long passage hello "
	send_message(data)
	time.sleep(1)
	print(passage)
	send_message_2("<" + "asdfasdfas I cat makdfjsdfkj kjsdf" + ">")

	return True

@app.route("/brew/<string:id>")
def brew_api(id):
	res = brew(id)
	return f"Brewing {id}: {res}"

# Handy debugging/testing functions for Arduino

def send_test_brew_data(co, re, ch):
	data = {}
	data['t'] = "B"
	if abs(entry['connection_score'].iloc[0]) > abs(entry['rest_score'].iloc[0]):
		passage = "on connection: " + str(entry['connection'].iloc[0])
	else:
		passage = "on rest: " + str(entry['rest'].iloc[0])

	data['p'] = passage
	data['c_s'] = str(entry['connection_score'].iloc[0])
	data['r_s'] = str(entry['rest_score'].iloc[0])
	data['ch_s'] = str(entry['chewiness_score'].iloc[0])
	send_message(data)

def send_test_init_data(id):
	data = { 't': "I", 'id': id }
	send_message(data)

def main():
	'''Listen for QR code and handle Arduino outputs until quit.'''
	print("Starting up Kukou Box...")
	# Credit: https://stackoverflow.com/a/48073789
	scheduler = BackgroundScheduler()
	job = scheduler.add_job(check_barcode, 'interval', seconds=1)
	scheduler.start()

main()
