from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
from imutils.video import VideoStream
from datetime import datetime
from csv import writer
import shortuuid
import json

from doc_compare import *
from command_arduino import *
from qr import *

CAMERA_ID = 1 # TODO: Set to external webcam id.
TICKET_DELAY_S = 900

app = Flask(__name__)

# what port number do we use?
arduino_controller = BasicArduinoOutputModule(0)
arduino_controller_TCP = BasicArduinoOutputModuleTCPSerial()

vs = VideoStream(src=CAMERA_ID).start()

def save_results(results, journal_result_id, timestamp):
	outlist = [results['connection'], results['rest'], results['connection_score'], results['rest_score'], results['chewiness_score'], journal_result_id, timestamp]

	with open("./data/tickets.csv", 'a') as f:
		writer_object = writer(f)
		writer_object.writerow(outlist)

@app.route("/submit_journal_text", methods=['POST'])
def submit_text():
	'''
	   1. process journal text to construct scores + document mapping.
	   2. save information in a csv; associate with a qr code.
	   3. tell arduino to print QR code.
	'''
	journal_text = request.get_data().decode('utf-8')
	# TODO - this needs to be a JSON that goes {"q1":"journal text", "q2":"some more journal text"}

	results = calc_journal_scores_whole(jstringjson)
	# results is an array that follows this convention: {'connection':passage, 'rest':passage, 'connection_score':float, 'rest_score':float, 'speed_score':float}
	journal_result_id = str(shortuuid.uuid()[:10]) # FIXME: I think we need either 8 or 12 digits depending on which 
	currenttime = datetime.now()
	save_results(results, journal_result_id, currenttime)
	
	# Send barcode to Arduino for initial receipt
	data = { 'type': "INIT", 'id': journal_result_id }
	data_json = json.dumps(data)
	arduino_controller.send_message(data_json, format='ascii')

	return f"submitting journal text"

def check_barcode():
	'''Check camera for a QR code. If one appears, process it and send data to Arduino
	to start making hot chocolate.'''
	barcodes = read_from_camera(vs, filter="CODE93")
	if len(barcodes) > 0:
		print(f"Found QR code: {barcodes[0]}")
		# pull up the associated stuff by reading in the associated text
		barcode_text = barcodes[0][:-1] # Chop off the suffix -8
		tickets = pd.read_csv("./data/tickets.csv")
		entry = tickets[tickets['journal_id'] == barcode_text]
		timestamp = entry['timestamp'].iloc[0]
		timestampobj = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
		if ((datetime.now() - timestampobj).seconds < TICKET_DELAY_S):
			return # "Do nothing! It's not time yet."
		else:
			# construct dictionary to send to the arduino
			data = {}
			data['type'] = "BREW"
			data['connection'] = str(entry['connection'].iloc[0])
			data['rest'] = str(entry['rest'].iloc[0])
			data['connection_score'] = entry['connection_score'].iloc[0]
			data['rest_score'] = entry['rest_score'].iloc[0]
			data_json = json.dumps(data)
			arduino_controller.send_message(data_json, format='ascii')


def main():
	'''Listen for QR code and handle Arduino outputs until quit.'''
	print("Starting up Kukou Box...")
	# Credit: https://stackoverflow.com/a/48073789
	scheduler = BackgroundScheduler()
	job = scheduler.add_job(check_barcode, 'interval', seconds=10)
	scheduler.start()

main()
