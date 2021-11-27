import qrcode
from pyzbar import pyzbar
import imutils
import cv2
import os

BASE_DIR = os.path.dirname(os.path.realpath(__file__))
print(BASE_DIR)

def generate_qr(name, data):
	png_path = f"qr_imgs/{name}.png"
	qr = qrcode.QRCode(version=1, box_size=10, border=0)
	qr.add_data(data)
	qr.make(fit=True)
	img = qr.make_image(fill="black", back_color="white")

	if not os.path.isdir(f"{BASE_DIR}/qr_imgs"):
		os.mkdir(f"{BASE_DIR}/qr_imgs")
	img.save(png_path)
	return png_path

# Source: https://www.pyimagesearch.com/2018/05/21/an-opencv-barcode-and-qr-code-scanner-with-zbar/
def read_qr(frame, render=False):
	barcodes = pyzbar.decode(frame)
	vals = []

	for barcode in barcodes:
		if render:
			(x, y, w, h) = barcode.rect
			cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

		barcode_data = barcode.data.decode("utf-8")
		barcode_type = barcode.type
		print(f"{barcode_data} | {barcode_type}")
		if barcode_type == "QRCODE": # FIXME: Can I use a constant from lib for this?
			vals.append(barcode_data)

		if render:
			text = "{} ({})".format(barcode_data, barcode_type)
			cv2.putText(frame, text, (x, y - 10),
				cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

	if render:
		cv2.imshow("Barcode Scanner", frame)
		key = cv2.waitKey(1) & 0xFF
	
	return vals

def read_qr_from_camera(vs, render=False):
	frame = vs.read()
	frame = imutils.resize(frame, width=400)
	return read_qr(frame, render)
