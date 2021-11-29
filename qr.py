import qrcode
from barcode import EAN13
from barcode.writer import ImageWriter
from pyzbar import pyzbar
import imutils
import cv2
import os

BASE_DIR = os.path.dirname(os.path.realpath(__file__))

def make_dir_if_not_exists(d):
	if not os.path.isdir(f"{BASE_DIR}/{d}"):
		os.mkdir(f"{BASE_DIR}/{d}")

def generate_qr(name, data):
	png_path = f"qr_imgs/{name}.png"
	qr = qrcode.QRCode(version=1, box_size=10, border=0)
	qr.add_data(data)
	qr.make(fit=True)
	img = qr.make_image(fill="black", back_color="white")
	make_dir_if_not_exists("qr_imgs")
	img.save(png_path)
	return png_path

def generate_barcode(name, number):
	my_code = EAN13(str(number), writer=ImageWriter())
	make_dir_if_not_exists("barcode_imgs")
	my_code.save(f"barcode_imgs/{name}")

def make_reader(code_type):
	# Source: https://www.pyimagesearch.com/2018/05/21/an-opencv-barcode-and-qr-code-scanner-with-zbar/
	def read_code(frame, render=False):
		barcodes = pyzbar.decode(frame)
		vals = []
		for barcode in barcodes:
			if render:
				(x, y, w, h) = barcode.rect
				cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
			barcode_data = barcode.data.decode("utf-8")
			barcode_type = barcode.type
			if barcode_type == code_type:
				vals.append(barcode_data)
			if render:
				text = "{} ({})".format(barcode_data, barcode_type)
				cv2.putText(frame, text, (x, y - 10),
					cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
		if render:
			cv2.imshow("Barcode Scanner", frame)
			key = cv2.waitKey(1) & 0xFF
		return vals
	return read_code

read_qr = make_reader("QRCODE")
read_barcode = make_reader("EAN13")

def read_qr_from_camera(vs, render=False):
	frame = vs.read()
	frame = imutils.resize(frame, width=400)
	return read_qr(frame, render)

def read_barcode_from_camera(vs, render=False):
	frame = vs.read()
	frame = imutils.resize(frame, width=400)
	return read_barcode(frame, render)
