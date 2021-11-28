from flask import Flask, request
from apscheduler.schedulers.background import BackgroundScheduler
from imutils.video import VideoStream
import time
import math

from doc_compare import *
from qr import *
from manage_tickets import *

CAMERA_ID = 1 # TODO: Set to external webcam id.

app = Flask(__name__)
vs = VideoStream(src=CAMERA_ID).start()

@app.route("/get/<int:ticket_id>")
def get_ticket(ticket_id):
	'''Get information associated with a ticket ID.'''
	return f"getting {ticket_id}"

@app.route("/delete/<int:ticket_id>")
def delete_ticket(ticket_id):
	'''Once ticket is used, remove it from the system.'''
	return f"deleting {ticket_id}"

@app.route("/submit_journal_text", methods=['POST'])
def submit_text():
	'''
	   1. process journal text to construct scores + document mapping.
	   2. save information in a csv; associate with a qr code.
	   3. tell arduino to print QR code.
	'''
	journal_text = request.get_data().decode('utf-8')
	results = calc_journal_scores(journal_text)
	timestamp = int(math.floor(time.time())) # In seconds; used as an id
	associated_code = generate_qr(timestamp, timestamp)
	save_ticket(timestamp, results, associated_code)
	return { "id": timestamp, "success": True }

def check_QR():
	'''Check camera for a QR code. If one appears, process it and send data to Arduino
	to start making hot chocolate.'''
	qr_codes = read_qr_from_camera(vs)
	if len(qr_codes) > 0:
		# TODO: Start making hot chocolate!
		print(f"Found QR code: {qr_codes[0]}")

def main():
	'''Listen for QR code and handle Arduino outputs until quit.'''
	print("Starting up Kukou Box...")

	# Get newest available ticket number from CSV database

	# Credit: https://stackoverflow.com/a/48073789
	scheduler = BackgroundScheduler()
	job = scheduler.add_job(check_QR, 'interval', seconds=1)
	scheduler.start()

main()
