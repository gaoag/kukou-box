from qr import *
from apscheduler.schedulers.background import BackgroundScheduler
from imutils.video import VideoStream
import time
CAMERA_ID = 0
vs = VideoStream(src=CAMERA_ID).start()

found_barcodes = []
def check_barcode():
    '''Check camera for a QR code. If one appears, process it and send data to Arduino
    to start making hot chocolate.'''
    barcodes = read_ocr_from_camera(vs) # filter="CODE93")
    if len(barcodes) > 0 and barcodes not in found_barcodes:
        # if len(barcodes[]) != 8:
        #     pass
        print(barcodes)
        # pull up the associated stuff by reading in the associated text
        found_barcodes.append(barcodes)
        # brew(barcode_text)
    else:
        print("No barcodes found", len(barcodes))


def main():
    '''Listen for QR code and handle Arduino outputs until quit.'''
    print("Starting up Kukou Box...")
    while True:
        check_barcode()
        time.sleep(2)

        # Credit: https://stackoverflow.com/a/48073789
    	# scheduler = BackgroundScheduler()
    	# job = scheduler.add_job(check_barcode, 'interval', seconds=2)
    	# scheduler.start()

main()
