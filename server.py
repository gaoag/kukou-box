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
TICKET_DELAY_S = 20
ARDUINO_PORT = "/dev/cu.usbmodem14101" # TODO
BAUDRATE = 9600

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

found_barcodes = []

# what port number do we use?
# arduino_controller = BasicArduinoOutputModule(0)
# arduino_controller_TCP = BasicArduinoOutputModuleTCPSerial()
ser = Serial(ARDUINO_PORT, BAUDRATE, timeout=2.5)

journal_dict = {}

vs = VideoStream(src=CAMERA_ID).start()

def send_message(data):
	data_json = json.dumps(data)
	print(data_json)
	ser.write(data_json.encode('ascii'))


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
	ticket_nums = len(pd.read_csv("./data/tickets.csv"))
	print(ticket_nums)
	journal_result_id = str(ticket_nums).zfill(8) # FIXME: I think we need either 8 or 12 digits depending on which
	print(journal_result_id)
	currenttime = datetime.now()
	save_results(results, journal_result_id, currenttime)

	# Send barcode to Arduino for initial receipt
	data = { 't': "I", 'id': journal_result_id}

	send_message(data)

	# brew(journal_result_id)


	return f"submitting journal text"

def check_barcode():
	'''Check camera for a QR code. If one appears, process it and send data to Arduino
	to start making hot chocolate.'''
	# barcodes = read_from_camera(vs, filter="EAN8") # filter="CODE93")
	barcode = read_ocr_from_camera(vs)
	if len(barcode) > 0 and barcode not in found_barcodes:
		print(f"Found QR code: {barcode}")
		# pull up the associated stuff by reading in the associated text
		# barcode_text = barcodes[0]
		found_barcodes.append(barcode[:8])
		brew(barcode[:8])
	else:
		print("No barcodes found", len(found_barcodes))

def brew(id):
	tickets = pd.read_csv("./data/tickets.csv")
	if (int(id) not in tickets['journal_id']):
		return None

	entry = tickets[tickets['journal_id'] == int(id)]
	timestamp = entry['timestamp'].iloc[0]
	timestampobj = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f' )
	if ((datetime.now() - timestampobj).seconds < TICKET_DELAY_S):
		print('not time yet!')
		return None
	# "Do nothing! It's not time yet."
	# construct dictionary to send to the arduino
	print(len(entry))
	data = {}
	data['t'] = "B"
	if abs(entry['connection_score'].iloc[0]) > abs(entry['rest_score'].iloc[0]):
		passage = "on connection - " + str(entry['connection'].iloc[0])
	else:
		passage = "on rest - " + str(entry['rest'].iloc[0])

	passage = passage.replace("'", "")
	passage = passage.replace('"', "")
	passage = passage.encode("ascii", "ignore")
	passage = passage.decode()
	passage += ">"
	# data['p'] = "he"
	data['c_s'] = str(entry['connection_score'].iloc[0])
	data['r_s'] = str(entry['rest_score'].iloc[0])
	data['ch_s'] = str(entry['chewiness_score'].iloc[0])
	print(data)
	send_message(data)
	time.sleep(5)


	# data['p'] = "hello this is a long passage hello "
	# we have a couple of things we can try:
	# we can continuously send requests with bits and pieces of the message?

	divisor = 31
	for i in range(len(passage)//divisor+1):
		data = {}
		data['t'] = "R"
		passage_part_to_send = passage[i*divisor:(i+1)*divisor]
		data['p'] = passage_part_to_send
		send_message(data)
		time.sleep(2)

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

@app.route("/test0")
def send_test_init_data():
	data = { 't': "I", 'id': "12345678" }
	print(data)
	send_message(data)
	return "hi"

def main():

	'''Listen for QR code and handle Arduino outputs until quit.'''
	print("Starting up Kukou Box...")
	# Credit: https://stackoverflow.com/a/48073789
	scheduler = BackgroundScheduler()
	job = scheduler.add_job(check_barcode, 'interval', seconds=3)
	scheduler.start()
@app.route("/test1")
def send_test_passage_data():
	passage = "I find myself again at thirty-four and while it feels somewhat hopeful, it also feels like an overwhelming task. Each break-up I go through takes me back to the original break-up of my twenties, the place where all that pain lives pressed like dead flowers on display. I struggle with feeling like a failure. I find myself single again at thirty-four and while it feels somewhat hopeful, it also feels like an overwhelming task. Each break-up I go through takes me back to the original break-up of my twenties, the place where all that pain lives pressed like dead."

	divisor = 31
	for i in range(len(passage)//divisor+1):
		data = {}
		data['t'] = "R"
		passage_part_to_send = passage[i*divisor:(i+1)*divisor]
		data['p'] = passage_part_to_send
		print(data)
		send_message(data)
		time.sleep(2)

	return "hi"

main()
