from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from doc_compare import *
from command_arduino import *
from qr import *
from datetime import datetime
from csv import writer
import shortuuid
import json


MAIN_LOOP_DELAY_S = 1
CAMERA_ID = 0 # TODO

app = Flask(__name__)

# what port number do we use?
arduino_controller = BasicArduinoOutputModule(0)
arduino_controller_TCP = BasicArduinoOutputModuleTCPSerial()



def save_results(results, journal_result_id, timestamp):
	outlist = [results['connection'], results['rest'], results['connection_score'], results['rest_score'], results['chewiness_score'], journal_result_id, timestamp]

	with open("./data/tickets.csv", 'a') as f:
		writer_object = writer(f)
		writer_object.writerow(outlist)

@app.route("/submit")
def submit():
	'''Submit a ticket, get back a ticket ID, or possibly the QR code image itself.'''
	return "submit"

@app.route("/get/<int:ticket_id>")
def get_ticket(ticket_id):
	'''Get information associated with a ticket ID.'''
	return f"getting {ticket_id}"

@app.route("/delete/<int:ticket_id>")
def delete_ticket(ticket_id):
	'''Once ticket is used, remove it from the system.'''
	return f"deleting {ticket_id}"

@app.route("/submit_journal_text", methods=['POST'])
def submittext():
	'''
	   1. process journal text to construct scores + document mapping.
	   2. save information in a csv; associate with a qr code.
	   3. tell arduino to print QR code.
	'''
	journal_text = request.get_data().decode('utf-8')
	results = calc_journal_scores(journal_text)
	# results is an array that follows this convention: {'connection':passage, 'rest':passage, 'connection_score':float, 'rest_score':float, 'speed_score':float}
	journal_result_id = str(shortuuid.uuid()[:10])
	currenttime = datetime.now()
	save_results(results, journal_result_id, currenttime)

	return f"submitting journal text"



def check_barcode():
	'''Check camera for a barcode. If a barcode exists, then '''
	barcode_exists = False
	# do something to modify barcode_exists!
	if barcode_exists:
		# pull up the associated stuff by reading in the associated text
		barcode_text = read_barcode_text()
		tickets = pd.read_csv("./data/tickets.csv")
		entry = tickets[tickets['journal_id'] == barcode_text]
		timestamp = entry['timestamp'].iloc[0]
		timestampobj = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S.%f')
		if ((datetime.now() - timestampobj).seconds < 900) {
			return "Do nothing! It's not time yet."
		} else {
			# construct dictionary to send to the arduino
			data = {}
			data['connection'] = str(entry['connection'].iloc[0])
			data['rest'] = str(entry['rest'].iloc[0])
			data['connection_score'] = entry['connection_score'].iloc[0]
			data['rest_score'] = entry['rest_score'].iloc[0]
			data_json = json.dumps(data)
			arduino_controller.send_message(data_json, format='ascii')
		}
	print('checked QR')



def main():
	'''Listen for QR code and handle Arduino outputs until quit.'''
	
	# Credit: https://stackoverflow.com/a/48073789
	scheduler = BackgroundScheduler()
	job = scheduler.add_job(check_QR, 'interval', seconds=10)
	scheduler.start()

main()
