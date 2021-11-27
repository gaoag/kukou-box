from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from doc_compare import *

MAIN_LOOP_DELAY_S = 1
CAMERA_ID = 0 # TODO

app = Flask(__name__)

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

def check_QR():
	'''Check camera for a QR code. If one appears, process it and send data to Arduino
	to start making hot chocolate.'''
	print('check_QR')

def main():
	'''Listen for QR code and handle Arduino outputs until quit.'''
	initialize_documents()
	# Credit: https://stackoverflow.com/a/48073789
	scheduler = BackgroundScheduler()
	job = scheduler.add_job(check_QR, 'interval', seconds=1)
	scheduler.start()

main()
